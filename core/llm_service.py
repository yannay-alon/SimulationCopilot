import json
from typing import TypeVar, overload, Type, Literal, Any, Callable

import streamlit as st
from google import genai
from google.genai import errors as google_exceptions
from google.genai import types
from pydantic import BaseModel

from core.prompts.general_simulation_knowledge import ERUPTIVE_SIMULATION, PERSONAL_SIMULATION
from core.prompts.system_prompts import (
    BASE_SYSTEM_INSTRUCTION,
    ANALYZE_REQUEST_ADDITION,
    GENERATE_DRAFT_ADDITION,
    GENERATE_CHAT_ADDITION
)
from models.domain_models import AgentDecision, Cadet, MultipleSimulations
from models.state_models import AppContext

ModelOutput = TypeVar("ModelOutput", bound=BaseModel)


class LLMService:
    def __init__(
            self,
            api_key: str,
            model_name: str,
            available_models: list[str],
            analysis_temperature: float = 0.2,
            generation_temperature: float = 0.7,
    ):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.available_models = available_models

        self.analysis_temperature = analysis_temperature
        self.generation_temperature = generation_temperature

    def _build_system_instruction(
            self,
            context: AppContext,
            selected_cadets: list[Cadet],
            specific_instructions: str,
    ) -> str:
        additional_explanations = [
            ERUPTIVE_SIMULATION,
            PERSONAL_SIMULATION
        ]
        formatted_explanations = "\n\n".join(additional_explanations)

        formatted_past_simulations = ""
        if len(context.past_simulations) > 0:
            past_simulations = "\n\n".join([
                f"Simulation:\n{sim.content}\nScore: {sim.score}"
                for sim in context.past_simulations
            ])
            formatted_past_simulations = f"Past Simulations (for style and quality reference):\n{past_simulations}\n"

        cadets_information = "\n".join([
            f"Name: {cadet.name}\nAnswers: {json.dumps(cadet.interview_answers, ensure_ascii=False)}"
            for cadet in selected_cadets
        ])

        instruction = BASE_SYSTEM_INSTRUCTION.format(
            role_description=context.role_description,
            formatted_explanations=formatted_explanations,
            weekly_theme=context.weekly_theme,
            formatted_past_simulations=formatted_past_simulations,
            cadets_information=cadets_information,
            specific_instructions=specific_instructions,
        )
        return instruction

    @overload
    async def _generate_content_with_fallback(
            self,
            model_name: str,
            contents: Any,
            config: types.GenerateContentConfig,
            is_structured: Literal[True],
            structured_output: Type[ModelOutput]
    ) -> tuple[ModelOutput, types.GenerateContentResponse]:
        ...

    @overload
    async def _generate_content_with_fallback(
            self,
            model_name: str,
            contents: Any,
            config: types.GenerateContentConfig,
            is_structured: Literal[False],
            structured_output: None
    ) -> tuple[str, types.GenerateContentResponse]:
        ...

    async def _generate_content_with_fallback(
            self,
            model_name: str,
            contents: Any,
            config: types.GenerateContentConfig,
            is_structured: bool = False,
            structured_output: Type[ModelOutput] | None = None
    ) -> tuple[ModelOutput | str, types.GenerateContentResponse]:
        models_to_try = [model_name] + [
            fallback_model
            for fallback_model in self.available_models
            if fallback_model != model_name
        ]

        toast_message = None
        for attempt_index, model in enumerate(models_to_try):
            if attempt_index > 0:
                if toast_message:
                    toast_message.toast(f"🔄 Model busy. Fallback to `{model}`", icon="⚠️")
                else:
                    toast_message = st.toast(f"🔄 Model busy. Fallback to `{model}`", icon="⚠️")
            try:
                response = await self.client.aio.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
            except google_exceptions.APIError as e:
                if attempt_index == len(models_to_try) - 1:
                    raise e
                continue

            if is_structured and structured_output is not None:
                if not response.parsed:
                    continue
                output = structured_output.model_validate(response.parsed)
                return output, response
            return str(response.text), response
        raise RuntimeError("No models available to attempt generation.")

    async def _stream_content_with_fallback(
            self,
            model_name: str,
            contents: Any,
            config: types.GenerateContentConfig,
            on_chunk: Callable[[str], None] | None = None,
    ) -> tuple[str, types.Content | None]:
        models_to_try = [model_name] + [
            fallback_model
            for fallback_model in self.available_models
            if fallback_model != model_name
        ]

        toast_message = None
        for attempt_index, model in enumerate(models_to_try):
            if attempt_index > 0:
                if toast_message:
                    toast_message.toast(f"🔄 Model busy. Fallback to `{model}`", icon="⚠️")
                else:
                    toast_message = st.toast(f"🔄 Model busy. Fallback to `{model}`", icon="⚠️")

            emitted_text = False
            collected_chunks: list[str] = []
            final_content: types.Content | None = None

            try:
                stream = await self.client.aio.models.generate_content_stream(
                    model=model,
                    contents=contents,
                    config=config,
                )
                async for chunk in stream:
                    chunk_text = str(chunk.text or "")
                    if chunk_text:
                        emitted_text = True
                        collected_chunks.append(chunk_text)
                        if on_chunk is not None:
                            on_chunk(chunk_text)

                    if chunk.candidates and chunk.candidates[0].content:
                        final_content = chunk.candidates[0].content

            except google_exceptions.APIError as e:
                # If streaming already started, we cannot safely fallback without duplicating content.
                if emitted_text or attempt_index == len(models_to_try) - 1:
                    raise e
                continue

            full_text = "".join(collected_chunks)
            if full_text.strip() or final_content is not None:
                return full_text, final_content
        raise RuntimeError("No models available to attempt generation.")

    async def analyze_request(
            self,
            history: list[types.Content],
            user_prompt: str,
            context: AppContext,
            selected_cadets: list[Cadet]
    ) -> AgentDecision:
        """Analyzes the user request to determine if a draft is needed."""
        system_instruction = self._build_system_instruction(context, selected_cadets, ANALYZE_REQUEST_ADDITION)

        new_history = history.copy()
        new_history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]))

        parsed_output, _ = await self._call_model(
            contents=new_history,
            system_instruction=system_instruction,
            structured_output=AgentDecision,
            temperature=self.analysis_temperature
        )
        return parsed_output

    async def generate_draft(
            self,
            history: list[types.Content],
            user_prompt: str,
            context: AppContext,
            selected_cadets: list[Cadet]
    ) -> tuple[MultipleSimulations, list[types.Content]]:
        """Generates or updates the simulation draft based on user input and context."""
        system_instruction = self._build_system_instruction(context, selected_cadets, GENERATE_DRAFT_ADDITION)

        new_history = history.copy()
        new_history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]))

        parsed_output, response = await self._call_model(
            contents=new_history,
            system_instruction=system_instruction,
            structured_output=MultipleSimulations,
            temperature=self.generation_temperature
        )

        if not response.candidates or not response.candidates[0].content:
            raise ValueError("No content generated by the model")

        new_history.append(response.candidates[0].content)
        return parsed_output, new_history

    async def generate_chat_response_stream(
            self,
            history: list[types.Content],
            user_prompt: str,
            context: AppContext,
            selected_cadets: list[Cadet],
            additional_directions: str | None = None,
            on_chunk: Callable[[str], None] | None = None,
    ) -> tuple[str, list[types.Content]]:
        """Generates a chat response and optionally streams text chunks through a callback."""
        system_instruction = self._build_system_instruction(context, selected_cadets, GENERATE_CHAT_ADDITION)
        if additional_directions:
            system_instruction += f"\n\n{additional_directions}"

        new_history = history.copy()
        new_history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)]))

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=self.generation_temperature
        )

        text, response_content = await self._stream_content_with_fallback(
            self.model_name,
            new_history,
            config,
            on_chunk=on_chunk,
        )

        if response_content:
            new_history.append(response_content)
        else:
            if not text.strip():
                raise ValueError("No content generated by the model")
            new_history.append(types.Content(role="model", parts=[types.Part.from_text(text=text)]))

        return text, new_history

    async def generate_chat_response(
            self,
            history: list[types.Content],
            user_prompt: str,
            context: AppContext,
            selected_cadets: list[Cadet],
            additional_directions: str | None = None,
    ) -> tuple[str, list[types.Content]]:
        """Generates a standard chat response for brainstorming or clarifying."""
        return await self.generate_chat_response_stream(
            history=history,
            user_prompt=user_prompt,
            context=context,
            selected_cadets=selected_cadets,
            additional_directions=additional_directions,
            on_chunk=None,
        )

    async def _call_model(
            self,
            contents: Any,
            system_instruction: str,
            structured_output: Type[ModelOutput],
            temperature: float = 1,
    ) -> tuple[ModelOutput, types.GenerateContentResponse]:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_json_schema=structured_output.model_json_schema(),
            temperature=temperature
        )
        return await self._generate_content_with_fallback(
            self.model_name, contents, config, is_structured=True, structured_output=structured_output
        )
