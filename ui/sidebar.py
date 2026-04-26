import os
from pathlib import Path

import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from core.document_parser.parser_factory import DocumentParserFactory
from models.domain_models import PastSimulation
from ui.state_manager import SessionState
from utils.exceptions import FileParsingError
from utils.exceptions import NonTextPDFError


@st.cache_data(show_spinner=False)
def get_available_models(api_key: str) -> dict[str, str]:
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        models = client.models.list()
        
        available_models = {}
        for model in models:
            if model.supported_actions and "generateContent" in model.supported_actions:
                name = model.name.replace("models/", "")
                available_models[model.display_name] = name
        
        if not available_models:
            raise ValueError("No compatible models found in Gemini API response.")
        return available_models
    except Exception:
        return {"Gemini 3.1": "gemini-3.1-flash-lite-preview", "Gemini 2.5": "gemini-2.5-flash"}

@st.dialog("Add Example Simulations")
def add_example_simulations_dialog():
    uploaded_files: list[UploadedFile] = st.file_uploader("Upload Past Simulations (.docx, .pdf)", type=["docx", "pdf"], accept_multiple_files=True)
    if uploaded_files:
        scores = {}
        for file in uploaded_files:
            scores[file.name] = st.number_input(f"Score for {file.name}", 1, 10, 5, key=f"score_{file.name}")
        
        if st.button("Save Simulations"):
            context = SessionState.get_context()
            for file in uploaded_files:
                try:
                    parser = DocumentParserFactory.get_parser(Path(file.name))
                except FileParsingError as error:
                    st.error(f"Failed to parse file ({file.name}): {error}")
                    continue

                try:
                    content = parser.parse(file.read())
                except NonTextPDFError as e:
                    st.error(f"Non-text PDF Error ({file.name}): {e}. Please upload a text-based PDF.")
                    continue

                context.past_simulations.append(PastSimulation(filename=file.name, content=content, score=scores[file.name]))
            SessionState.update_context(context)
            st.rerun()

class SidebarComponent:
    MAX_CONTEXT_SAMPLE_LENGTH = 25
    SAMPLE_TRUNCATION_INDICATOR = "..."

    @classmethod
    def render(cls) -> tuple[str, list[str], str]:
        with st.sidebar:
            st.header("Settings")
            
            env_api_key = os.environ.get("GEMINI_API_KEY", "")
            
            # API Key Input
            api_key = st.text_input(
                "Gemini API Key", 
                value=env_api_key, 
                type="password",
                help="Enter your Gemini API key. If you don't have one, generate it in https://aistudio.google.com/api-keys"
            )

            available_models_dict = get_available_models(api_key)
            option_models = list(available_models_dict.keys())

            # Default model handling
            default_model = os.environ.get("MODEL_NAME", "").lower()
            default_model_index = 0
            if default_model:
                model_ids = [model_id.lower() for model_id in available_models_dict.values()]
                if default_model in model_ids:
                    default_model_index = model_ids.index(default_model)
            selected_model = st.selectbox("Select LLM Model", option_models, index=default_model_index)
            
            st.write("---")

            st.header("Upload Context Documents")
            context = SessionState.get_context()
            
            role_label = "Upload Role Description (.docx)"
            if context.role_description:
                sample = context.role_description[:cls.MAX_CONTEXT_SAMPLE_LENGTH] + cls.SAMPLE_TRUNCATION_INDICATOR
                role_label += f" ✅ (Loaded: {sample})"
            
            role_file = st.file_uploader(role_label, type=["docx"])
            if role_file:
                try:
                    parser = DocumentParserFactory.get_parser(Path(role_file.name))
                    context.role_description = parser.parse(role_file.read())
                    SessionState.update_context(context)
                    st.success("Role description updated.")
                except Exception as e:
                    st.error(f"Error: {e}")

            theme_label = "Upload Weekly Theme (.docx)"
            if context.weekly_theme:
                sample = context.weekly_theme[:cls.MAX_CONTEXT_SAMPLE_LENGTH] + cls.SAMPLE_TRUNCATION_INDICATOR
                theme_label += f" ✅ (Loaded: {sample})"
                
            theme_file = st.file_uploader(theme_label, type=["docx"])
            if theme_file:
                try:
                    parser = DocumentParserFactory.get_parser(Path(theme_file.name))
                    context.weekly_theme = parser.parse(theme_file.read())
                    SessionState.update_context(context)
                    st.success("Weekly theme updated.")
                except Exception as e:
                    st.error(f"Error: {e}")

            interviews_label = "Upload Interviews (.xlsx)"
            if context.cadets:
                interviews_label += f" ✅ (Loaded {len(context.cadets)} cadets)"
                
            interview_file = st.file_uploader(interviews_label, type=["xlsx"])
            name_column = st.text_input("Name column", value=context.name_column)
            
            if name_column != context.name_column:
                context.name_column = name_column
                SessionState.update_context(context)

            if interview_file:
                try:
                    parser = DocumentParserFactory.get_parser(Path(interview_file.name), name_column=name_column)
                    context.cadets = parser.parse(interview_file.read())
                    SessionState.update_context(context)
                    st.success(f"Loaded {len(context.cadets)} cadets.")
                except Exception as e:
                    st.error(f"Error: {e}")

            st.write("---")
            if st.button("Add example simulations"):
                add_example_simulations_dialog()
            
            if context.past_simulations:
                with st.expander("✅ Loaded Past Simulations"):
                    st.caption(f"Count: {len(context.past_simulations)}")
                    for idx, sim in enumerate(context.past_simulations):
                        col1, col2, col3 = st.columns([0.5, 0.3, 0.2])
                        col1.write(f"**{sim.filename}**")
                        
                        new_score = col2.number_input(
                            "Score",
                            min_value=1,
                            max_value=10,
                            value=sim.score,
                            key=f"update_score_{idx}_{sim.filename}",
                            label_visibility="collapsed"
                        )
                        if new_score != sim.score:
                            context.past_simulations[idx].score = new_score
                            SessionState.update_context(context)
                            
                        if col3.button("❌", key=f"remove_sim_{idx}_{sim.filename}"):
                            context.past_simulations.pop(idx)
                            SessionState.update_context(context)
                            st.rerun()
            else:
                st.info("No Past Simulations loaded yet.")
                
        return available_models_dict[selected_model], list(available_models_dict.values()), api_key