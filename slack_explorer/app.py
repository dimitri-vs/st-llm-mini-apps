import streamlit as st
from pathlib import Path
import json
from typing import Dict, List, Optional
from data_loader import load_workspace_data, WorkspaceData
from ui_components import render_sidebar, render_conversation

st.set_page_config(
    page_title="Slack Export Explorer",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for navigation
if "selected_channel" not in st.session_state:
    st.session_state.selected_channel = None
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "workspace_data" not in st.session_state:
    st.session_state.workspace_data = None

def main():
    st.title("Slack Export Explorer")

    # Check if data is loaded
    if st.session_state.workspace_data is None:
        export_path = st.text_input(
            "Enter the path to your Slack export directory:",
            value=str(Path("exported").absolute()),
            help="This should be the directory containing channels.json, users.json, etc."
        )

        if st.button("Load Export Data"):
            with st.spinner("Loading workspace data..."):
                try:
                    st.session_state.workspace_data = load_workspace_data(export_path)
                    st.success("Data loaded successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading data: {str(e)}")
        return

    # Split into sidebar and main content
    with st.sidebar:
        render_sidebar()

    # Main content area
    if st.session_state.selected_channel:
        render_conversation()
    else:
        st.info("👈 Select a channel or DM from the sidebar to view conversations")

if __name__ == "__main__":
    main()