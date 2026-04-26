import streamlit as st
from models.state_models import AppContext
from utils.storage import StorageManager

class SessionState:
    @staticmethod
    def initialize():
        if "context" not in st.session_state:
            st.session_state.context = StorageManager.load_context()
        if "selected_cadets" not in st.session_state:
            st.session_state.selected_cadets = []
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "messages" not in st.session_state:
            st.session_state.messages = []

    @staticmethod
    def get_context() -> AppContext:
        return st.session_state.context

    @staticmethod
    def update_context(context: AppContext):
        st.session_state.context = context
        StorageManager.save_context(context)

    @staticmethod
    def clear_chat():
        st.session_state.chat_history = []
        st.session_state.messages = []