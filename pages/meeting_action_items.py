import json

import streamlit as st

from utils.anthropic_llm import get_anthropic_completion, get_anthropic_json_completion

st.set_page_config(
    page_title="Agency Gen AI Mini-Apps",
    page_icon="🧪",
    layout="wide"
)

st.title("🗣️→✅ Meeting Action Items")
st.caption("Convert any meeting or video transcript into actionable insights")

st.warning("This app page is currently under development. The generation component needs to be implemented.", icon="⚠️")

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


transcript = st.text_area(
    "Paste your meeting transcript here (from Loom, Google Meet, Zoom, etc.)",
    help="All these platforms have a way to download the transcript. Make sure they include timestamps and correct speaker names, if applicable."
)

# Editable placeholder for recipient context
RECIPIENT_CONTEXT_PLACEHOLDER = """
- Dimitri: web app development agency owner
- ______: a client of the agency 🔴
- ______: the agency ______🔴
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
is_valid_transcript = transcript and len(transcript.strip()) >= 50

if not is_valid_recipient:
    st.warning("Complete the recipient details and remove the red dot (🔴)", icon="⚠️")

# Initial LLM prompt to generate Loom video notes
loom_prompt_1 = """
Analyze the provided transcript and distill the key information.

Create these sections:
⏩ TL;DR - What the meeting was about in 1-2 sentences.
✅ Action Items - List all action items with:
  - Who is responsible (mark as "UNCLEAR" if not specified)
  - What needs to be done
  - Any relevant deadlines or context
❓ Open Questions - List any:
  - Unresolved issues
  - Points needing clarification
  - Decisions pending
  - Questions raised but not fully addressed

Key Names & Relations:
{recipient_context}

Pay great attention when proper nouns and abbreviations are mentioned when reading the transcript, as these are often transcribed incorrectly due to the limitations of voice-to-text software. Consider quietly if the proper noun that is written is the correct one or if it should be interpreted as something else using the context of what is being discussed.

<Transcript>
{transcript}
</Transcript>
""".strip()

# Read-only text area for previewing the rendered prompt template
rendered_prompt = loom_prompt_1.format(
    recipient_context=recipient_context,
    transcript=transcript
)
st.text_area(
    "Prompt Preview",
    value=rendered_prompt,
    disabled=True,
    help="This is the complete prompt that will be used to generate action items and notes."
)

# === 🟩 AND THEN ln() Video Chapters ===
ln_chapters_prompt = """
Great, now please review the transcript again and identify:
1. Any subtle or implied action items that weren't explicitly stated
2. Additional questions or decisions that need follow-up
3. Any dependencies between action items

Format your response using bullet points and maintain the same sections (TL;DR, Action Items, Open Questions) if you find new items to add.
""".strip()

# Add button and handle LLM interactions
if st.button("Generate Action Items", type="primary", disabled=not is_valid_transcript):

    with st.spinner("Generating action items..."):
        # First request - Get initial analysis
        messages = [{"role": "user", "content": rendered_prompt}]
        initial_response = get_anthropic_completion(messages)
        # Store in session state
        st.session_state.initial_response = initial_response

        # Second request - Get condensed chapters
        messages = [
            {"role": "user", "content": rendered_prompt},
            {"role": "assistant", "content": initial_response},
            {"role": "user", "content": ln_chapters_prompt}
        ]
        chapters_response = get_anthropic_completion(messages)
        # Store chapters response directly in session state
        st.session_state.chapters_data = chapters_response

# Display the content if it exists in session state
if 'initial_response' in st.session_state:
    st.markdown("### Initial Analysis")
    st.text_area(
        label="Initial Analysis",
        value=st.session_state.initial_response,
        height=300,
    )

if 'chapters_data' in st.session_state:
    st.markdown("### Action Items")
    # Remove the JSON parsing and display directly
    st.markdown(st.session_state.chapters_data)

# ---- made changes to around here ----

# # Create a button for generating the follow-up message
# if st.button("Generate Follow-up Message", type="primary", disabled=not is_valid_transcript):
#     with st.spinner("Generating follow-up message..."):
#         # Use initial_response from session state
#         initial_response = st.session_state.get('initial_response', '')
#         if not initial_response:
#             st.error("Please generate the title and summary first!")
#             st.stop()

#         follow_up_template = """
# Write a message to the Loom recipient using the following template. The template is more of a general suggestion, don't feel constrained by it, I just want the overall message to be concise. Persist the orange block and placeholders (eg. ________🟧) as they are a reminder for me review/edit.

# <template>
# {recipient_name}, {OPTIONAL_reply_or_engagement_with_their_last_message} {transition} made a short video to {purpose_of_video}🟧 and show {concise_engagement_hook_on_what_they_might_want_to_see}. Here are the key points:
# - {key_point_1}
# - {more_detailed_key_point_2}
# - {more_detailed_key_point_3}
# - {key_point_4}

# {loom_video_link}🟧
# </template>

# Use the following context and transcript to craft the message:

# <Additional Context>
# {recipient_context}
# </Additional Context>

# <Loom Video Transcript>
# {loom_transcript}
# </Loom Video Transcript>
#         """.strip()

#         messages = [
#             {"role": "user", "content": rendered_prompt},
#             {"role": "assistant", "content": initial_response},
#             {"role": "user", "content": follow_up_template}
#         ]

#         follow_up_message = get_anthropic_completion(messages)
#         # Store follow-up message in session state
#         st.session_state.follow_up_message = follow_up_message

# # Display the follow-up message if it exists in session state
# if 'follow_up_message' in st.session_state:
#     st.markdown("### 📧 Follow-up Message")
#     st.text_area(
#         label="Message Template",
#         value=st.session_state.follow_up_message,
#         height=350
#     )
#     st.warning("Remember to review and edit all sections marked with 🟧 before sending the message.", icon="⚠️")

