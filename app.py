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
- **New Upwork Contract**: (WIP) Draft standardized contract titles and descriptions for new or existing Upwork contracts.
- **Meeting Action Items**: Converts meeting transcripts into actionable insights and summaries.
- **Slack Explorer**: Browse and search Slack workspace exports locally.
- **Token Counter**: Calculate token usage and costs for various LLM models.
- **LLM Context Builder**: Build and manage context for LLM interactions.

### Coming Soon

- **Client Onboarding** (Name TBD): Will help capture and generate the core content needed for initial client engagements—like summarizing transcripts, creating a client profile, and drafting a project plan.
  (We haven't created a "pages/client_onboarding.py" file yet, but we'll likely add it soon!)
""")

