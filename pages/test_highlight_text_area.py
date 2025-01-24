import streamlit as st
from typing import Optional

st.title("Text Area Highlighter Test")

text_area_value = st.text_area(
    "Text Area",
    value="""
Using the provided context, answer the following questions:

1. Does the client mention the name of their business or can it be inferred?
2. Was there any mention of the client's location, time zone, or anything?
3. Was there any kind of estimate quoted for the project or the discovery?

{{estimate quoted}}

People & Roles Information:
Dimitri is the web app development agency founder.
{{example}} is a client of the agency.
______ is the agency ______. 🔴

""".strip(),
    help="Enter text with {{placeholders}} to highlight"
)

text_input_value = st.text_input(
    "Text Input",
    value="some {{example}} text"
)

st.write("some {{example}} text")
