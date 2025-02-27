import os

import streamlit as st
from components.chat_component import chat_component
from litellm import completion
from utils.people_roles import parse_people_roles

# Constants
LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL")

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

# Automatically detect participants when transcript changes
if transcript and (
    "participants" not in st.session_state or
    "last_transcript" not in st.session_state or
    st.session_state.get("last_transcript") != transcript
):
    participants = parse_people_roles(transcript)
    st.session_state.participants = participants
    st.session_state.last_transcript = transcript

def format_people_roles_for_prompt(participants):
    """Format participant data into a prompt-friendly string."""
    lines = []
    for p in participants:
        lines.append(f"- {p['name']}: {p['role']}")
    return "\n".join(lines)

if "participants" in st.session_state:
    st.markdown("### Participants & Roles")
    # Convert participants to formatted text and store in session state if not already present
    if "participant_text" not in st.session_state:
        st.session_state.participant_text = format_people_roles_for_prompt(st.session_state.participants)

    # Display editable text area with detected participants
    updated_participant_text = st.text_area(
        "Edit participants and roles as needed",
        value=st.session_state.participant_text,
        key="participant_text",
        help="Each line should follow the format: '- Name: Role'"
    )

    # Update recipient context directly from text area
    recipient_context = updated_participant_text

else:
    # Editable placeholder for manual recipient context
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
meeting_prompt_1 = """
Analyze the provided transcript and distill the key information.

### **Participants & Roles**
{recipient_context}

### **Output Sections:**

**⏩ Recap**
Summarize the meeting in 1-2 sentences - what was discussed and its primary purpose, include the following placeholder on a new line below that:
[MEETING LINK PLACEHOLDER🔴]


**✅ Action Items (Grouped by Person)**
- List each person's name followed by their tasks.
- Use bullet points for each action item.
- When there are multiple tasks with clear relationships or commonalities (eg. regarding the same client or project), group them together to improve readability.
- Avoid using markdown formatting like headers ("#"), bold, or italic text.

**Example 1: Standard Task List**
```
John:
• Set up CI/CD pipeline by next Friday
• Review PR #123 and provide feedback by EOD
• Schedule tech review with Sarah

Sarah:
• Send updated timeline to client by Wednesday
• Follow up with design team about mockups

Both:
• Write API documentation
```

**Example 2: Grouped by Workstream (When Clear Task Divisions Exist)**
```
Michael:
1. Client Dashboard
• Implement user authentication - Due Monday
• Add data visualization components
• Write API documentation
2. API Migration
• Update endpoint schemas

James:
• Review PR #123 and provide feedback by EOD
• Schedule tech review with Sarah
```

❓ Open Questions - List any:
  - Unresolved issues
  - Points needing clarification
  - Decisions pending
  - Questions raised but not fully addressed

### **⚠️ Accuracy Considerations**
Pay great attention when proper nouns and abbreviations are mentioned when reading the transcript, as these are often transcribed incorrectly due to the limitations of voice-to-text software. Consider quietly if the proper noun that is written is the correct one or if it should be interpreted as something else using the context of what is being discussed.

<Transcript>
{transcript}
</Transcript>
""".strip()

# Read-only text area for previewing the rendered prompt template
rendered_prompt = meeting_prompt_1.format(
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

Format your response using bullet points and maintain the same sections (TL;DR, Action Items, Open Questions) if you find new items to add.
""".strip()

# Meeting title prompt
meeting_title_prompt = """
Given a meeting transcript, create a brief title in this format:

Format: {{Names}}: {{Key Topics}}

Names:
- First names of 2-3 key speakers
- Add "..." if more than 3
- Separate with commas

Topics:
- 4-6 words max, brevity > grammar
- Use & between topics
- Capitalize key words

Examples:
"John, Sarah: Q4 Planning & Hiring"
"Mike, Ana, ...: Product Launch Strategy"

<Transcript>
{transcript}
</Transcript>
""".strip()

# Add button and handle LLM interactions

if st.button("✨ Generate Title & Action Items", type="primary", disabled=not is_valid_transcript):

    progress_bar = st.progress(0, text="Starting analysis...")

    with st.spinner("Generating meeting title..."):
        # First request - Get meeting title
        title_messages = [{"role": "user", "content": meeting_title_prompt.format(transcript=transcript)}]
        meeting_title = completion(
            model=LLM_MODEL,
            messages=title_messages
        ).choices[0].message.content

        # Store in session state
        st.session_state.meeting_title = meeting_title

        progress_bar.progress(25, text="Generating initial analysis...")

    with st.spinner("Generating initial analysis..."):
        # Second request - Get initial analysis
        messages = [{"role": "user", "content": rendered_prompt}]
        initial_response = completion(
            model=LLM_MODEL,
            messages=messages
        ).choices[0].message.content

        # Store in session state
        st.session_state.initial_response = initial_response

        progress_bar.progress(75, text="Generating additional insights...")

        # Third request - Get follow-up analysis
        messages = [
            {"role": "user", "content": rendered_prompt},
            {"role": "assistant", "content": initial_response},
            {"role": "user", "content": ln_chapters_prompt}
        ]
        followup_response = completion(
            model=LLM_MODEL,
            messages=messages
        ).choices[0].message.content

        # Store combined response in session state
        st.session_state.combined_analysis = (
            f"# {meeting_title}\n\n" +
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
                system_message = (
                    "You are helping answer questions about a meeting analysis.\n\n"
                    "Original Transcript:\n"
                    f"{transcript}\n\n"
                    "Current Analysis:\n"
                    f"{st.session_state.combined_analysis}\n\n"
                )
                full_messages = [{"role": "system", "content": system_message}] + messages

                return completion(
                    model=LLM_MODEL,
                    messages=full_messages,
                    stream=True
                )
            else:
                # Use messages as-is for subsequent exchanges
                return completion(
                    model=LLM_MODEL,
                    messages=messages,
                    stream=True
                )

        chat_component(
            messages_key="meeting_chat_messages",
            response_stream=stream_meeting_response,
            chat_height=500,
            prompt_label="Ask questions about the analysis...",
            border=True,
            show_debug=True
        )

        # Add warning about context loss
        st.warning(
            "Note: The chat context is limited to one message exchange. ",
            icon="⚠️"
        )