import os

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="LLM/VLM Playground",
    page_icon="🧪",
    layout="wide"
)

st.title("LLM/VLM Playground")
st.write("This app is intended to be a collection of mini-apps for AI experimentation and prototyping.")
st.markdown("""
### Current Apps

- **Better Loom Info**: Enhances Loom video transcripts with AI-generated summaries and chapter markers.
- **New Upwork Contract**: Draft standardized contract titles and descriptions for new or existing Upwork contracts, with an eye toward SEO marketing value.
- **Claude Better Chat UI**: A work in progress chat UI using Streamlit's chat components to explore advanced conversation flows.

### Coming Soon

- **Client Onboarding** (Name TBD): Will help capture and generate the core content needed for initial client engagements—like summarizing transcripts, creating a client profile, and drafting a project plan.
  (We haven't created a "pages/client_onboarding.py" file yet, but we'll likely add it soon!)
""")

