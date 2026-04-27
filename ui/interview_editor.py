import pandas as pd
import streamlit as st

from models.domain_models import Cadet
from ui.state_manager import SessionState


class InterviewEditor:
    EDITOR_KEY = "interview_data_editor"

    @staticmethod
    def _normalize_text(value: object) -> str:
        return str(value).strip()

    @staticmethod
    def _question_columns(df: pd.DataFrame, name_column: str) -> list[str]:
        return [str(column) for column in df.columns if str(column) != name_column]

    @staticmethod
    def _to_dataframe(cadets: list[Cadet], name_column: str) -> pd.DataFrame:
        if not cadets:
            return pd.DataFrame({name_column: []})

        # Preserve original column order
        all_questions = []
        for cadet in cadets:
            for q in cadet.interview_answers.keys():
                if q not in all_questions:
                    all_questions.append(q)
        
        data = []
        for cadet in cadets:
            cadet_data = {name_column: cadet.name}
            for question in all_questions:
                cadet_data[question] = cadet.interview_answers.get(question, "")
            data.append(cadet_data)
            
        return pd.DataFrame(data)

    @staticmethod
    def _from_dataframe(df: pd.DataFrame, name_column: str) -> tuple[list[Cadet], list[str]]:
        if name_column not in df.columns:
            raise ValueError(f"Missing required name column: '{name_column}'")

        cadets: list[Cadet] = []
        validation_warnings: list[str] = []
        seen_names_ci: dict[str, str] = {}

        for _, row in df.iterrows():
            raw_name = row[name_column]
            if pd.isna(raw_name):
                continue

            name = InterviewEditor._normalize_text(raw_name)
            if not name or name.lower() == "nan":
                continue

            normalized_name_key = name.casefold()
            if normalized_name_key in seen_names_ci:
                first_seen_name = seen_names_ci[normalized_name_key]
                raise ValueError(
                    f"Duplicate cadet name detected: '{name}'. "
                    f"Names must be unique (case-insensitive). First conflict: '{first_seen_name}'."
                )
            seen_names_ci[normalized_name_key] = name

            answers = {
                str(col): (
                    ""
                    if pd.isna(row[col]) or InterviewEditor._normalize_text(row[col]).lower() == "nan"
                    else InterviewEditor._normalize_text(row[col])
                )
                for col in df.columns
                if str(col) != name_column
            }
            cadets.append(Cadet(name=name, interview_answers=answers))
        return cadets, validation_warnings

    @staticmethod
    def _add_question(cadets: list[Cadet], question_name: str) -> None:
        for cadet in cadets:
            if question_name not in cadet.interview_answers:
                cadet.interview_answers[question_name] = ""

    @staticmethod
    def _rename_question(cadets: list[Cadet], old_name: str, new_name: str) -> None:
        for cadet in cadets:
            if old_name not in cadet.interview_answers:
                continue
            # Preserve insertion order while replacing one key.
            renamed_answers: dict[str, str] = {}
            for key, value in cadet.interview_answers.items():
                renamed_answers[new_name if key == old_name else key] = value
            cadet.interview_answers = renamed_answers

    @staticmethod
    def _delete_question(cadets: list[Cadet], question_name: str) -> None:
        for cadet in cadets:
            cadet.interview_answers.pop(question_name, None)

    @classmethod
    def _render_manage_questions(cls, context) -> None:
        context_name_column = context.name_column
        cadets = context.cadets

        df = cls._to_dataframe(cadets, context_name_column)
        question_columns = cls._question_columns(df, context_name_column)

        with st.expander("Manage Questions", expanded=False):
            add_tab, rename_tab, delete_tab = st.tabs(["Add", "Rename", "Delete"])

            with add_tab:
                new_question_raw = st.text_input("New question", key="question_add_input")
                new_question = cls._normalize_text(new_question_raw)
                if st.button("Add Question", key="question_add_button"):
                    existing_questions_ci = {column.casefold() for column in df.columns}
                    if not new_question:
                        st.warning("Please enter a question name.")
                    elif new_question == context_name_column:
                        st.warning("Question name cannot match the name column.")
                    elif new_question.casefold() in existing_questions_ci:
                        st.warning("Question already exists.")
                    elif not cadets:
                        st.warning("Add at least one cadet row before creating questions.")
                    else:
                        cls._add_question(cadets, new_question)
                        SessionState.update_context(context)
                        st.success(f"Added question: {new_question}")

            with rename_tab:
                if not question_columns:
                    st.caption("No questions available to rename.")
                else:
                    old_name = st.selectbox("Question to rename", question_columns, key="question_rename_select")
                    new_name_raw = st.text_input("New question name", value=old_name, key="question_rename_input")
                    new_name = cls._normalize_text(new_name_raw)
                    if st.button("Rename Question", key="question_rename_button"):
                        if not new_name:
                            st.warning("Please enter a valid new name.")
                        elif new_name.casefold() == context_name_column.casefold():
                            st.warning("Question name cannot match the name column.")
                        elif new_name.casefold() in {column.casefold() for column in question_columns if column != old_name}:
                            st.warning("A question with this name already exists.")
                        elif new_name == old_name:
                            st.info("No changes to apply.")
                        else:
                            cls._rename_question(cadets, old_name, new_name)
                            SessionState.update_context(context)
                            st.success(f"Renamed '{old_name}' to '{new_name}'.")

            with delete_tab:
                if not question_columns:
                    st.caption("No questions available to delete.")
                else:
                    question_to_delete = st.selectbox("Question to delete", question_columns, key="question_delete_select")
                    confirm_delete = st.checkbox(
                        f"Confirm deleting '{question_to_delete}' from all cadets",
                        key="question_delete_confirm",
                    )
                    if st.button("Delete Question", key="question_delete_button", disabled=not confirm_delete):
                        cls._delete_question(cadets, question_to_delete)
                        SessionState.update_context(context)
                        st.success(f"Deleted question: {question_to_delete}")

    @classmethod
    def render(cls):
        context = SessionState.get_context()
        name_column = context.name_column

        st.caption("Edit cadets and interview answers in one place")
        st.info(
            "Add new cadets by adding rows in the table. Use 'Manage Questions' to add, rename, or delete question columns.",
            icon="ℹ️",
        )

        cls._render_manage_questions(context)

        df = cls._to_dataframe(context.cadets, name_column)

        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            width="stretch",
            hide_index=True,
            key=cls.EDITOR_KEY,
            column_config={
                name_column: st.column_config.TextColumn(
                    name_column,
                    help="Cadet name. Empty rows are ignored on save.",
                )
            },
        )

        if st.button("Save Changes", type="primary"):
            try:
                updated_cadets, warnings = cls._from_dataframe(edited_df, name_column)
                if updated_cadets == context.cadets:
                    st.info("No changes detected.")
                    return

                context.cadets = updated_cadets
                SessionState.update_context(context)
                if warnings:
                    st.warning("Some rows were skipped due to validation issues.")
                    for warning in warnings:
                        st.caption(f"- {warning}")
                st.success(f"Saved {len(updated_cadets)} cadet records.")
            except ValueError as e:
                st.toast(str(e), icon="⚠️")
                st.warning(str(e))
            except Exception as e:
                st.error(f"Failed to save changes: {e}")