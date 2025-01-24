import json

import streamlit as st

from utils.anthropic_llm import get_anthropic_completion, get_anthropic_json_completion

st.set_page_config(
    page_title="Agency Gen AI Mini-Apps",
    page_icon="🧪",
    layout="wide"
)

st.title("🎥 Better Loom Info")

# Create columns for layout - one for spacing and one for the reset button
_, reset_col = st.columns([4, 1])
with reset_col:
    if st.button("Reset", icon="🗑️", type="primary"):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # Clear cache
        st.cache_data.clear()
        st.rerun()


loom_transcript = st.text_area(
    "Paste your Loom video transcript here",
    help="You can copy the entire transcript from the Transcript tab found in the sidebar of your recorded Loom video."
)

# Editable placeholder for recipient context
RECIPIENT_CONTEXT_PLACEHOLDER = """
The intended recipient is __________, and they are __________ 🔴
""".strip()

recipient_context = st.text_area(
    "Recipient Context",
    value=st.session_state.get("recipient_context", RECIPIENT_CONTEXT_PLACEHOLDER),
    key="recipient_context",
    help="""**Examples:**
- The intended recipient is John, and he is a developer that works for the agency.
- The intended recipient is Leon, and they are a prospective client on Upwork with the following job: ...
""".strip()
)

is_valid_recipient = "🔴" not in recipient_context
is_valid_transcript = loom_transcript and len(loom_transcript.strip()) >= 50

if not is_valid_recipient:
    st.warning("Complete the recipient details and remove the red dot (🔴)", icon="⚠️")

# Initial LLM prompt to generate Loom video notes
loom_prompt_1 = """
Write Loom video notes using the provided Loom Video Transcript and the Additional Context.

Create sections for:
🎦 Loom Title - Create a title for the video that is at least 10 words long. If the intended recipient of the video is clear and their name is mentioned, prefix the video title with their name - for example, if the transcript starts with something  like "Hey David, ..." then you might prefix the video title with `@David: `. Additionally, you should add a relevant emoji to the end of the title, but avoid using the robot emoji (🤖). The recipient name and emoji don't count towards the title word limit.
📝 Summary - A summary of the video content. Limit your summary to 5 sentences. Write the summary from the speakers first-person perspective.

<Additional Context>
The person speaking in the transcript is Dimitri, and he is a web app development agency owner
{recipient_context}
</Additional Context>

Pay great attention when proper nouns and abbreviations are mentioned when reading the transcript, as these are often transcribed incorrectly due to the limitations of voice-to-text software. Consider quietly if the proper noun that is written is the correct one or if it should be interpreted as something else using the context of what is being discussed.

<Loom Video Transcript>
{loom_transcript}
</Loom Video Transcript>
""".strip()

# Read-only text area for previewing the rendered prompt template
rendered_prompt = loom_prompt_1.format(
    recipient_context=recipient_context,
    loom_transcript=loom_transcript
)
st.text_area(
    "Rendered Loom Prompt",
    value=rendered_prompt,
    disabled=True,
    help="This is the complete prompt that will be used to analyze the Loom transcript."
)

# === 🟩 AND THEN ln() Video Chapters ===
ln_chapters_prompt = """
Given the Loom video timestamps, create a response with:
1. Your step-by-step thinking about how to condense the chapters based on video length
2. The final condensed chapters

Adjust chapter count using the following video length to chapter number mapping, capped at 15 chapters:
- 3:00 video = 3 chapters
- 5:00 = 4 chapters
- 10:00 = 7 chapters
- 15:00 = 10 chapters
- 20:00 = 13 chapters
- 30:00 = 14 chapters
For video times between mapped values, interpolate appropriately.

Limit chapter titles to 5-7 words, prioritizing brevity over grammar.

Return your response as JSON with this structure:
{
    "thinking": "Your step-by-step thought process (use \\n for new lines)",
    "chapters": "The condensed chapters with timestamps (use \\n for new lines)"
}
""".strip()

# Add button and handle LLM interactions
if st.button("Generate Title, Summary, and Chapters", type="primary", disabled=not is_valid_transcript):

    with st.spinner("Generating better Loom info..."):
        # First request - Get initial analysis
        messages = [{"role": "user", "content": rendered_prompt}]
        initial_response = get_anthropic_completion(messages)
        # Store in session state
        st.session_state.initial_response = initial_response

        # Second request - Get condensed chapters as JSON
        messages = [
            {"role": "user", "content": rendered_prompt},
            {"role": "assistant", "content": initial_response},
            {"role": "user", "content": ln_chapters_prompt}
        ]
        chapters_response = get_anthropic_json_completion(messages)
        chapters_data = json.loads(chapters_response)
        # Store chapters data in session state
        st.session_state.chapters_data = chapters_data

# Display the content if it exists in session state
if 'initial_response' in st.session_state:
    st.markdown("### Initial Analysis")
    st.text_area(
        label="Initial Analysis",
        value=st.session_state.initial_response,
        height=300,
    )

if 'chapters_data' in st.session_state:
    st.markdown("### Chapter Analysis")
    with st.expander("Thought process"):
        st.markdown(st.session_state.chapters_data["thinking"])
    st.markdown("### 🎞️ Video Chapters (Full)")
    st.code(st.session_state.chapters_data["chapters"], language=None)

# Create a button for generating the follow-up message
if st.button("Generate Follow-up Message", type="primary", disabled=not is_valid_transcript):
    with st.spinner("Generating follow-up message..."):
        # Use initial_response from session state
        initial_response = st.session_state.get('initial_response', '')
        if not initial_response:
            st.error("Please generate the title and summary first!")
            st.stop()

        follow_up_template = """
Write a message to the Loom recipient using the following template. The template is more of a general suggestion, don't feel constrained by it, I just want the overall message to be concise. Persist the orange block and placeholders (eg. ________🟧) as they are a reminder for me review/edit.

<template>
{recipient_name}, {OPTIONAL_reply_or_engagement_with_their_last_message} {transition} made a short video to {purpose_of_video}🟧 and show {concise_engagement_hook_on_what_they_might_want_to_see}. Here are the key points:
- {key_point_1}
- {more_detailed_key_point_2}
- {more_detailed_key_point_3}
- {key_point_4}

{loom_video_link}🟧
</template>

Use the following context and transcript to craft the message:

<Additional Context>
{recipient_context}
</Additional Context>

<Loom Video Transcript>
{loom_transcript}
</Loom Video Transcript>
        """.strip()

        messages = [
            {"role": "user", "content": rendered_prompt},
            {"role": "assistant", "content": initial_response},
            {"role": "user", "content": follow_up_template}
        ]

        follow_up_message = get_anthropic_completion(messages)
        # Store follow-up message in session state
        st.session_state.follow_up_message = follow_up_message

# Display the follow-up message if it exists in session state
if 'follow_up_message' in st.session_state:
    st.markdown("### 📧 Follow-up Message")
    st.text_area(
        label="Message Template",
        value=st.session_state.follow_up_message,
        height=350
    )
    st.warning("Remember to review and edit all sections marked with 🟧 before sending the message.", icon="⚠️")

