import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import metadata, categorize, suggest_deletions, search
import streamlit as st
import file_interaction

# -- Constants --
DOWNLOADS_PATH = os.path.expanduser("~\\Downloads")


def _stream_callback_factory():
    if "last_thinking" not in st.session_state:
        st.session_state.last_thinking = ""
    if "last_response" not in st.session_state:
        st.session_state.last_response = ""

    think_box = st.empty()
    response_box = st.empty()

    def callback(text):
        if "</think>" not in text:
            clean_text = text.replace("<think>", "")
            st.session_state.last_thinking = clean_text
            with think_box.expander("### Thinking...", expanded=True):
                st.markdown(
                    f"<div style='color: gray; font-size: 0.9em;'>{clean_text}</div>",
                    unsafe_allow_html=True
                )
        else:
            response_text = text.split("</think>")[-1]
            st.session_state.last_response = response_text
            response_box.markdown("### Response\n" + response_text)

    return callback


class LLMFileOrganizer:
    def __init__(self):
        self.df = st.session_state.get("df", metadata.get_files_metadata(DOWNLOADS_PATH))

    def run(self):
        st.set_page_config(page_title="LLM File Manager")
        st.markdown("<h2 style='font-size:1.5em;'>LLM File Manager</h2>",
                    unsafe_allow_html=True)

        tabs = st.tabs(["Overview", "Categorize", "Suggest Deletions", "Search Files"])
        with tabs[0]: self._overview()
        with tabs[1]: self._categorize()
        with tabs[2]: self._suggest_deletions()
        with tabs[3]: self._search_files()

    def _overview(self):
        st.write("This table shows all files in your Downloads folder with metadata.")
        st.dataframe(self.df[['Filename', 'Type', 'Size', 'Last Modified']])

    def _categorize(self):
        st.write("Use the LLM to categorize files into directories.")

        user_input = st.text_area("Enter custom categories (one per line)", height=100)
        user_categories = [line.strip() for line in user_input.splitlines() if line.strip()] or None

        if "run_categorization_flag" not in st.session_state:
            st.session_state.run_categorization_flag = False

        if "categorized_df" not in st.session_state:
            st.session_state.categorized_df = None

        if st.button("Run Categorization", disabled=st.session_state.run_categorization_flag,
                     key="run_categorization_button"):
            st.session_state.run_categorization_flag = True
            st.session_state.categorized_df = None

            progress_text = st.empty()
            progress_bar = st.progress(0)

            def keyword_progress_callback(i, total):
                progress_text.markdown(f"Generating file keywords: **{i}/{total}**")
                progress_bar.progress(i / total)

            callback = _stream_callback_factory()
            categorized_df = categorize.categorize(
                self.df,
                user_categories=user_categories,
                stream_callback=callback,
                progress_callback=keyword_progress_callback
            )
            st.session_state.categorized_df = categorized_df
            st.session_state.run_categorization_flag = False
            st.session_state.df = categorized_df
            self.df = categorized_df
            st.rerun()

        if "last_thinking" in st.session_state and st.session_state.last_thinking:
            with st.expander("### Thinking...", expanded=True):
                st.markdown(
                    f"<div style='color: gray; font-size: 0.9em;'>{st.session_state.last_thinking}</div>",
                    unsafe_allow_html=True
                )

        if "last_response" in st.session_state and st.session_state.last_response:
            st.markdown("### Response\n" + st.session_state.last_response)

        if st.session_state.categorized_df is not None:
            st.markdown("### Categorized Files")
            categorized_df = st.session_state.categorized_df
            edited_subset = st.data_editor(
                categorized_df[['Filename', 'Keywords', 'LLM-Categorized']],
                disabled=['Filename'],
                num_rows="dynamic",
                use_container_width=True
            )
            categorized_df.update(edited_subset)
            st.session_state.categorized_df = categorized_df
            self.df = categorized_df

            if st.button("Organize Into Folders"):
                file_interaction.move_to_category_folders(categorized_df)
                st.success("Files moved into category folders.")

    def _suggest_deletions(self):
        col1, col2, col3, col4, _ = st.columns([1, 1, 1, 1, 2])

        with col1:
            max_age = st.number_input("Max age", min_value=0, value=30)
        with col2:
            age_unit = st.radio("Age unit", options=["days", "weeks", "months", "years"], index=0)
        with col3:
            max_size = st.number_input("Max size", min_value=0, value=1024)
        with col4:
            size_unit = st.radio("Size unit", options=["KB", "MB", "GB"], index=0)

        size_multipliers = {"KB": 1, "MB": 1024, "GB": 1024 * 1024}
        age_multipliers = {"days": 1, "weeks": 7, "months": 30, "years": 365}

        max_size_kb = max_size * size_multipliers[size_unit]
        max_age_days = max_age * age_multipliers[age_unit]

        if "get_suggestions_flag" not in st.session_state:
            st.session_state.get_suggestions_flag = False

        if st.button("Get Suggestions", disabled=st.session_state.get_suggestions_flag, key="get_suggestions_button"):
            st.session_state.get_suggestions_flag = True
            st.rerun()

        if "last_thinking" in st.session_state and st.session_state.last_thinking:
            with st.expander("### Thinking...", expanded=True):
                st.markdown(
                    f"<div style='color: gray; font-size: 0.9em;'>{st.session_state.last_thinking}</div>",
                    unsafe_allow_html=True
                )

        if "last_response" in st.session_state and st.session_state.last_response:
            st.markdown("### Response\n" + st.session_state.last_response)

        if "suggestions" in st.session_state and not st.session_state.get_suggestions_flag:
            st.write("### Files Suggested for Deletion:")
            if "deletion_checkboxes" not in st.session_state:
                st.session_state.deletion_checkboxes = {
                    file_name: True for file_name in st.session_state.suggestions
                }

            selected_files = []
            for file_name, reason in st.session_state.suggestions.items():
                checked = st.checkbox(f"**{file_name}**: {reason}",
                                      value=st.session_state.deletion_checkboxes.get(file_name, True),
                                      key=f"del_cb_{file_name}")
                st.session_state.deletion_checkboxes[file_name] = checked
                if checked:
                    selected_files.append(file_name)

            if st.button("Delete Suggested Files", key="delete_suggested_button") and selected_files:
                paths = [os.path.join(DOWNLOADS_PATH, file_name) for file_name in selected_files]
                file_interaction.delete_suggested_files(paths)
                st.success("Selected files deleted.")
                del st.session_state.suggestions
                del st.session_state.deletion_checkboxes

        if st.session_state.get_suggestions_flag:
            with st.spinner("Analyzing metadata..."):
                callback = _stream_callback_factory()
                suggestions_df = suggest_deletions.suggest_deletions(self.df, max_age_days, max_size_kb,
                                                                     stream_callback=callback)
                suggestions_df = suggestions_df[suggestions_df['LLM-Delete'] == 'Delete']
                suggestions = {row['Filename']: row['LLM-Delete-Reason'] for _, row in suggestions_df.iterrows()}

            st.session_state.get_suggestions_flag = False
            st.session_state.suggestions = suggestions
            st.rerun()

    def _search_files(self):
        outer_col = st.container()
        with outer_col:
            input_col1, input_col2, _ = st.columns([6, 2, 1])

            with input_col1:
                query = st.text_input("Search query", key="search_query")
            with input_col2:
                max_num_results = st.number_input("Max number of results", min_value=1, value=5, key="max_num_results")

            if "search_triggered" not in st.session_state:
                st.session_state.search_triggered = False

            if st.button("Search", disabled=st.session_state.search_triggered, key="search_button"):
                st.session_state.search_triggered = True
                st.rerun()

            if st.session_state.search_triggered:
                with st.spinner("Searching files..."):
                    callback = _stream_callback_factory()
                    results = search.search(self.df,
                                            st.session_state.search_query,
                                            st.session_state.max_num_results,
                                            stream_callback=callback)

                st.session_state.search_triggered = False

                if results:
                    st.write(f"### Search Results for '{st.session_state.search_query}':")
                    for file_name in results:
                        file_path = os.path.join(DOWNLOADS_PATH, file_name)
                        st.code(file_path, language='text')
                else:
                    st.warning("No files found matching your query.")


def main():
    app = LLMFileOrganizer()
    app.run()


if __name__ == "__main__":
    main()
