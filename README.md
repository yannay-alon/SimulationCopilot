# Military Simulation CoPilot

Military Simulation CoPilot is an AI-powered Streamlit application designed to assist military training officers in generating, brainstorming, and drafting customized training simulations for cadets. Powered by Google's Gemini LLMs, the app leverages contextual documents and cadet interview data to create highly tailored simulation scenarios.

## Features

- **Context-Aware AI:** Upload role descriptions and weekly themes (.docx) to ground the AI in your specific training requirements.
- **Cadet Data Management:** Upload cadet interviews via Excel (.xlsx).
- **In-App Interview Editor:** View, edit, add, rename, and delete cadet interview questions and answers directly within the application using an intuitive spreadsheet-like interface.
- **Example Simulations:** Upload past simulations to guide the AI's style and quality expectations, along with scores.
- **Interactive Chat Interface:** Brainstorm simulation ideas, ask for clarifications, and guide the AI before generating a final draft.
- **Automated Draft Generation:** Produce structured simulation drafts (Formal, Eruptive, or Personal) tailored to individual cadets or multiple cadets simultaneously.
- **Streaming Responses:** Enjoy real-time, streaming AI responses for a fluid chat experience.
- **Robust Model Fallback:** Automatically switches to alternative Gemini models if the primary model is busy or unavailable due to rate limits.
- **Persistent State:** Saves your uploaded context, cadets, and past simulations locally so you can resume where you left off.

## Project Structure

```text
SimulationCoPilot/
├── app.py                  # Main Streamlit application entry point
├── core/                   # Core business logic
│   ├── document_parser/    # Factory and parsers for Word, PDF, and Excel documents
│   ├── prompts/            # System instructions and prompt templates
│   └── llm_service.py      # Google Gemini API integration and logic
├── models/                 # Data models
│   ├── domain_models.py    # Pydantic models for simulation structures and cadets
│   └── state_models.py     # Pydantic models for application state
├── ui/                     # User interface components
│   ├── chat_interface.py   # Main chat and drafting UI
│   ├── interview_editor.py # In-app cadet interview data editor
│   ├── sidebar.py          # Sidebar for settings and file uploads
│   └── state_manager.py    # Session state management
├── utils/                  # Utility functions
│   ├── exceptions.py       # Custom exception classes
│   ├── formatters.py       # Output formatting for the UI
│   └── storage.py          # Local JSON storage handling
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (API Key)
```

## Prerequisites

- Python 3.11 or higher
- Google Gemini API Key (Get one from [Google AI Studio](https://aistudio.google.com/))

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yannay-alon/SimulationCopilot.git
   cd SimulationCoPilot
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your environment variables:
   Create a `.env` file in the root directory and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   MODEL_NAME=gemini-2.5-flash # Optional: set a default model
   ```
   *Alternatively, you can input the API key directly in the app's sidebar during runtime.*

## Usage

1. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```

2. Access the app in your browser (usually at `http://localhost:8501`).

3. **Settings:** Enter your Gemini API Key in the sidebar (if not using `.env`) and select your preferred model.
4. **Upload Context:** Upload the Role Description (.docx), Weekly Theme (.docx), and Cadet Interviews (.xlsx).
5. **Manage Cadets:** Click "Edit" next to the uploaded interviews to open the Interview Editor and refine the data, add new questions, or remove obsolete ones.
6. **Chat & Draft:** Select the cadets you want to create simulations for and use the chat interface to instruct the AI.

## Technologies Used

- [Streamlit](https://streamlit.io/) - Frontend web framework
- [Google GenAI SDK](https://github.com/google/genai-python) - LLM integration
- [Pydantic](https://docs.pydantic.dev/) - Data validation and schema generation
- [Pandas](https://pandas.pydata.org/) - Data manipulation (Excel parsing & editing)
- [python-docx](https://python-docx.readthedocs.io/) - Word document parsing
- [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) - PDF document parsing

