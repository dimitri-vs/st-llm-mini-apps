import json

import streamlit as st
from components.chat_component import chat_component
from utils.anthropic_llm import get_anthropic_completion, get_anthropic_json_completion, stream_anthropic_completion

st.set_page_config(
    page_title="Agency Gen AI Mini-Apps",
    page_icon="🧪",
    layout="wide"
)

st.title("🗣️→✅ Meeting Action Items")
st.caption("Convert any meeting or video transcript into actionable insights")

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
⏩ Recap - What the meeting was about in 1-2 sentences.
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

    progress_bar = st.progress(0, text="Starting analysis...")

    with st.spinner("Generating initial analysis..."):
        # First request - Get initial analysis
        messages = [{"role": "user", "content": rendered_prompt}]
        initial_response = get_anthropic_completion(messages)
        # Store in session state
        st.session_state.initial_response = initial_response

        progress_bar.progress(50, text="Generating additional insights...")

        # Second request - Get follow-up analysis
        messages = [
            {"role": "user", "content": rendered_prompt},
            {"role": "assistant", "content": initial_response},
            {"role": "user", "content": ln_chapters_prompt}
        ]
        followup_response = get_anthropic_completion(messages)
        # Store combined response in session state
        st.session_state.combined_analysis = (
            initial_response +
            "\n\n═══════════════════════════════════════════\n" +
            "📝 Additional Insights\n" +
            "═══════════════════════════════════════════\n\n" +
            followup_response
        )

        progress_bar.progress(100, text="Analysis complete!")

# Display the combined content if it exists in session state
if 'combined_analysis' in st.session_state:
    st.markdown("### Action Items and Analysis")

    # Create two columns for the analysis and chat
    analysis_col, chat_col = st.columns([1, 1])

    with analysis_col:
        st.text_area(
            label="Complete Analysis",
            value=st.session_state.combined_analysis,
            height=500,
        )

    with chat_col:
        def stream_meeting_response(messages):
            """
            Streams responses for meeting analysis questions, maintaining context
            of the original transcript and analysis.
            """
            # Only add the context if this is the first message in the conversation
            if len(messages) == 1:
                additional_context = (
                    "You are helping answer questions about a meeting analysis.\n\n"
                    "Original Transcript:\n"
                    f"{transcript}\n\n"
                    "Current Analysis:\n"
                    f"{st.session_state.combined_analysis}\n\n"
                )
                # Add context to just the first message
                context_messages = messages.copy()
                context_messages[0]["content"] = additional_context + context_messages[0]["content"]
            else:
                # Use messages as-is for subsequent exchanges
                context_messages = messages

            return stream_anthropic_completion(
                context_messages,
                temperature=0.7,
                max_tokens=1000
            )

        chat_component(
            messages_key="meeting_chat_messages",
            response_stream=stream_meeting_response,
            chat_height=500,
            prompt_label="Ask questions about the analysis...",
            border=True,
            show_debug=True
        )