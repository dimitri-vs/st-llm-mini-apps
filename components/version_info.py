import streamlit as st
from build_info import BUILD_TIMESTAMP

def show_version_info():
    st.sidebar.markdown(
        f"<div style='text-align: center; color: gray; font-size: 0.8em; margin: -1em 0 -1em 0; line-height: 1;'>App Version: {BUILD_TIMESTAMP}</div>",
        unsafe_allow_html=True
    ) 