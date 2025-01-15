import streamlit as st

from utils.anthropic_llm import get_anthropic_completion, get_anthropic_json_completion, stream_anthropic_completion
from components.chat_component import chat_component
from components.dynamic_context_component import render_dynamic_context_sections

st.set_page_config(
    page_title="Agency Gen AI Mini-Apps",
    page_icon="🧪",
    layout="wide"
)
st.title("🥨 o1 Pro to Cursor")

st.markdown("Use the sections below to provide any client-related context (meeting transcripts, emails, etc.).")

# Provide a unique prefix to avoid collisions with other pages
context_snippets = render_dynamic_context_sections(st, prefix="o1_pro_to_cursor")

# display the context snippets, but it might be a list of strings
combined_context = "\n\n---\n\n".join(context_snippets)

st.text_area("combined_context", combined_context, disabled=True)

