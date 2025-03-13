import os

import streamlit as st
from components.chat_component import chat_component
from litellm import completion

# Constants
LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL")

st.set_page_config(
    page_title="Agency Gen AI Mini-Apps",
    page_icon="🧪",
    layout="wide"
)

st.title("⏱️ Retime Prompts")
st.caption("Generate abbreviated titles for events and tasks")

# Input text area for the long-form description
longform_descr = st.text_area(
    "Enter your long-form description",
    help="Enter the full description of your event or task here. The app will generate shortened titles for it."
)

# Build the prompt template with the user input
def get_prompt(longform_descr):
    return '''
Give me a variety of four highly abbreviated titles for the following task:

"""
{}
"""

You don't need to identify it as a event/task. They all needs to be at or under 16 characters but still be intuitive at a glance.
'''.strip().format(longform_descr)

# Create a button to generate titles
if st.button("Generate Titles", type="primary", disabled=not longform_descr):
    with st.spinner("Generating titles..."):
        prompt = get_prompt(longform_descr)
        messages = [{"role": "user", "content": prompt}]
        response = completion(
            model=LLM_MODEL,
            messages=messages
        ).choices[0].message.content

        # Store the response in session state
        st.session_state.generated_titles = response

# Display the generated titles if they exist
if "generated_titles" in st.session_state:
    st.markdown("### Generated Titles")
    st.text_area(
        label="Titles",
        value=st.session_state.generated_titles,
        height=200
    )

    # Add pre-filled text area for copying selected title with original description
    st.markdown("### Save Your Selected Title")
    st.text_area(
        label="Copy this snippet",
        value=f"""TASK: {longform_descr}
TITLE: YOUR_SELECTED_TITLE🔴""",
        height=150
    )

# Add a separator between the two features
st.markdown("---")

# Habit Naming Section
st.markdown("### 🔄 Habit Name Generator")
st.caption("Generate abbreviated names for habits you are trying to build")

# Input text area for habits description
habits_descr = st.text_area(
    "Enter your habit descriptions (one per line)",
    help="Enter descriptions of habits you're trying to build. Put each habit on a separate line.",
    key="habits_input"
)

# Build the habit prompt template with the user input
def get_habit_prompt(habits_descr):
    return '''
Give me highly abbreviated "short names" for each of the following habit(s) I am trying to build:

"""
{}
"""

You don't need to identify it as a habit/task. They all need to be under 25 characters but still be intuitive at a glance and might follow the format of `<Action> <Who/What> <When/Where> <Other Details>`
'''.strip().format(habits_descr)

# Create a button to generate habit names
if st.button("Generate Habit Names", type="primary", disabled=not habits_descr, key="generate_habits"):
    with st.spinner("Generating habit names..."):
        prompt = get_habit_prompt(habits_descr)
        messages = [{"role": "user", "content": prompt}]
        response = completion(
            model=LLM_MODEL,
            messages=messages
        ).choices[0].message.content

        # Store the response in session state
        st.session_state.generated_habit_names = response

# Display the generated habit names if they exist
if "generated_habit_names" in st.session_state:
    st.markdown("### Generated Habit Names")
    st.text_area(
        label="Habit Names",
        value=st.session_state.generated_habit_names,
        height=200
    )

    # Add pre-filled text area for copying selected habit name with original description
    st.markdown("### Save Your Selected Habit Name")
    st.text_area(
        label="Copy this snippet",
        value=f"""TASK: {habits_descr}
TITLE: YOUR_SELECTED_TITLE🔴""",
        height=150
    )


