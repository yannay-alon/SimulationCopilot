import streamlit as st

from core.llm_service import LLMService
from ui.state_manager import SessionState
from models.state_models import ChatMessage, AppContext
from models.domain_models import Cadet
from utils.formatters import OutputFormatter


class ChatInterface:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    @staticmethod
    def _set_auto_text_direction():
        st.markdown(
            """
            <style>
            .stChatMessage {
                unicode-bidi: plaintext;
                text-align: start;
            }
            .stChatInputContainer textarea {
                unicode-bidi: plaintext;
                text-align: start;
            }
            /* Ensure markdown and paragraphs correctly adapt to the text direction */
            .stMarkdown, .stMarkdown p {
                unicode-bidi: plaintext;
                text-align: start;
            }
            details > summary {
                cursor: pointer;
                font-weight: bold;
                margin-bottom: 0.5rem;
                font-size: 0.8rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    @staticmethod
    def _render_cadet_selection(context: AppContext) -> list[Cadet] | None:
        if not context.cadets:
            st.info("Please upload the interview (.xlsx) file to load cadets.")
            return None

        cadet_names = [cadet.name for cadet in context.cadets]
        selected_names = st.multiselect("Select Cadet(s)", cadet_names)
        if not selected_names:
            st.warning("Please select at least one cadet to generate a simulation.")
            return None

        return [cadet for cadet in context.cadets if cadet.name in selected_names]

    @classmethod
    def _render_chat_history(cls):
        for message in st.session_state.messages:
            with st.chat_message(message.role):
                if isinstance(message.content, dict):
                    cls._display_drafts(message.content)
                else:
                    cls._display_answer(message.content)

    async def _handle_chat_input(self, context: AppContext, selected_cadets: list[Cadet]):
        if prompt := st.chat_input("Enter your instructions or feedback for the simulation..."):
            st.session_state.messages.append(ChatMessage(role="user", content=prompt))

            with st.chat_message("user"):
                self._display_answer(prompt)

            with st.chat_message("assistant"):
                assistant_placeholder = st.empty()
                with st.spinner("Thinking...", show_time=True):
                    try:
                        is_draft_created, assistant_response = await self._generate_answer(
                            prompt,
                            context,
                            selected_cadets,
                            stream_placeholder=assistant_placeholder,
                        )
                    except Exception as error:
                        st.error(f"Error generating response: {error}")
                    else:
                        if is_draft_created:
                            self._display_drafts(assistant_response)
                        st.session_state.messages.append(ChatMessage(role="assistant", content=assistant_response))

    async def render(self):
        self._set_auto_text_direction()

        context = SessionState.get_context()
        selected_cadets = self._render_cadet_selection(context)
        
        if not selected_cadets:
            return

        self._render_chat_history()
        await self._handle_chat_input(context, selected_cadets)

    async def _generate_answer(
            self,
            prompt: str,
            context: AppContext,
            selected_cadets: list[Cadet],
            stream_placeholder: st.delta_generator.DeltaGenerator,
    ) -> tuple[bool, str | dict[str, str]]:
        decision = await self.llm_service.analyze_request(
            st.session_state.chat_history,
            prompt,
            context,
            selected_cadets
        )
        st.toast(f"LLM analysis complete. Should draft: {decision.is_draft_needed}", icon="💡")

        if decision.is_draft_needed:
            draft, history = await self.llm_service.generate_draft(
                st.session_state.chat_history,
                prompt,
                context,
                selected_cadets
            )
            assistant_response = OutputFormatter.format_draft(draft)
        else:
            partial_chunks: list[str] = []

            def on_chunk(chunk: str):
                partial_chunks.append(chunk)
                stream_placeholder.markdown("".join(partial_chunks))

            assistant_response, history = await self.llm_service.generate_chat_response_stream(
                st.session_state.chat_history,
                prompt,
                context,
                selected_cadets,
                additional_directions=decision.next_step_directions,
                on_chunk=on_chunk,
            )

            if not partial_chunks:
                stream_placeholder.markdown(assistant_response)

        st.session_state.chat_history = history
        return decision.is_draft_needed, assistant_response
    
    @staticmethod
    def _display_answer(content: str):
        st.markdown(content)
    
    @staticmethod
    def _display_drafts(drafts: dict[str, str]):
        for cadet_name, draft_content in drafts.items():
            st.markdown(draft_content)
