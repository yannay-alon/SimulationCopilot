import asyncio
import os

import streamlit as st
from ui.sidebar import SidebarComponent
from ui.chat_interface import ChatInterface
from ui.state_manager import SessionState
from core.llm_service import LLMService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Simulation CoPilot", layout="wide")

def main():
    st.title("Military Simulation CoPilot")
    SessionState.initialize()
    
    selected_model, available_models, api_key = SidebarComponent.render()
    
    try:
        if not api_key:
            st.info("Please enter your Gemini API Key in the sidebar to proceed.")
            return

        llm_service = LLMService(
            api_key=api_key,
            model_name=selected_model,
            available_models=available_models
        )
        chat_interface = ChatInterface(llm_service)
        asyncio.run(chat_interface.render())
    except ValueError as e:
        st.error(f"Initialization Error: {e}")

if __name__ == "__main__":
    main()