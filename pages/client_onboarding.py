import os
import streamlit as st
from litellm import completion
from components.chat_component import chat_component
from components.dynamic_context_component import render_dynamic_context_sections

# Constants
LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL")

st.set_page_config(
    page_title="Agency Gen AI Mini-Apps",
    page_icon="🧪",
    layout="wide"
)
st.title("👋 Client Onboarding")

st.info("""
### 📝 Recommended Context Sources

Make sure to include relevant information from these sources:
- Meeting transcripts or notes
- Client's original job posting
- Company website (landing page, team/about page)
- Client's LinkedIn profile and company page
- Any email threads discussing requirements or scope
""")

def build_initial_prompt(context_snippets, people_and_roles):
    """
    Build a basic prompt referencing the dynamic context and placeholders.
    # TODO: More advanced prompts for generating the client profile, project goals, etc.
    """
    base_questions = """
Using the provided context, answer the following questions:

1. Does the client mention the name of their business or can it be inferred?
2. Was there any mention of the client's location, time zone, or anything?
3. Was there any kind of estimate quoted for the project or the discovery?

People & Roles Information:
{}

I will provide various snippets of text that may provide additional context about the client/project. They might be document excerpts, message exchanges, etc. Note that these snippets may not be directly relevant to the task at hand. Only reference them if pertinent.
""".strip().format(people_and_roles)

    if context_snippets:
        combined_context = "\n\n---\n\n".join(context_snippets)
    else:
        combined_context = "No context snippets provided."

    prompt = f"{base_questions}\n\n<Context Provided>\n{combined_context}\n</Context Provided>"
    return prompt

def build_detailed_profile_prompt(context_snippets, people_and_roles):
    """
    Builds a prompt for generating a detailed client and project profile.
    """
    base_prompt = """
Use the provided context to write a client and project profile. Include the following sections:

👤 Client Description - Two or three sentences about who the client is, their business sector, what they do, our primary contact and their partners/associates.
🎯 Project Goals - What are the main problems they were facing and/or what are their initial goals with the project
📝 Specs & Scope - An overview of the tentative plan for executing the project, explain the proposed approach or solution, and if applicable, break the project down into Phases.

People & Roles Information:
{}

I will provide various snippets of text that may provide context about the client/project. They might be document excerpts, message exchanges, etc. Note that these snippets may not be directly relevant to the task at hand. Only reference them if pertinent.
""".strip().format(people_and_roles)

    if context_snippets:
        combined_context = "\n\n---\n\n".join(context_snippets)
    else:
        combined_context = "No context snippets provided."

    prompt = f"{base_prompt}\n\n<Context Provided>\n{combined_context}\n</Context Provided>"
    return prompt

def build_title_and_summary_prompt(context_snippets, people_and_roles):
    """
    Builds a prompt for generating project titles and summary.
    """
    base_prompt = """
Based on the provided context, complete these two tasks:

1. Create three descriptive titles (around 10 words each) that describe this project. The titles should:
   - Succinctly capture the goal, scope and main platform/framework
   - Use industry-specific terms and core technology names
   - Be concise and abbreviation-heavy
   - Focus on technical/internal style (not marketing)

2. Write one paragraph (~5 sentences) summarizing the project from our agency's perspective:
   - Use simple, direct language and common abbreviations
   - Write short, declarative sentences
   - Include specific examples in parentheses where relevant
   - Focus on concrete details over marketing language
   - Use simple verbs (e.g., "uses", "builds" instead of "leverages", "crafts")

People & Roles Information:
{}

I will provide various snippets of text that may provide context about the client/project. They might be document excerpts, message exchanges, etc. Note that these snippets may not be directly relevant to the task at hand. Only reference them if pertinent.
""".strip().format(people_and_roles)

    if context_snippets:
        combined_context = "\n\n---\n\n".join(context_snippets)
    else:
        combined_context = "No context snippets provided."

    prompt = f"{base_prompt}\n\n<Context Provided>\n{combined_context}\n</Context Provided>"
    return prompt

def render_people_and_roles_field():
    """
    Render a text area to describe the relevant people mentioned
    and their roles in this client engagement.
    Includes placeholder text and validation.
    """
    PEOPLE_ROLES_PLACEHOLDER = """
Dimitri is the web app development agency founder.
______ is a client of the agency.
______ is the agency ______. 🔴
    """.strip()

    people_and_roles = st.text_area(
        "People & Roles",
        value=st.session_state.get("people_and_roles", PEOPLE_ROLES_PLACEHOLDER),
        key="people_and_roles",
        help="List the key individuals involved and their roles in the project."
    )

    is_valid_roles = "🔴" not in people_and_roles
    if not is_valid_roles:
        st.warning("Complete the people & roles details and remove the red dot (🔴) for validation.", icon="⚠️")

    return people_and_roles, is_valid_roles

# =============================================================================
# Main App
# =============================================================================

with st.expander("ChatGPT Deep Research Prompt"):
    # Add research prompt section below the extraction details
    st.write("Use the following prompt to conduct deep research on the client and add that to the context sources.")

    research_prompt = """
    CONTEXT: I am the founder of a small web app development agency specializing in generative AI, employing around 10 people who are international and fully remote.

    I want you to help me with the process of conducting background research on a client "{client_name}"🔴

    To make sure you are finding the right person, here is some tentative profile I have on them so far:

    [name, email, location, etc.]🔴

    I want you to gather additional publicly available information such as:

    - Any sources confirming their location or address
    - Attempt to find their business registration
    - A description of their core business activities and industry focus
    - Link to their personal social media profile (Twitter, Facebook, etc.)
    - Link to their business and/or personal website
    - Any news articles or industry publications about them or their business
    """.strip()

    st.text_area(
        label="Client Research Prompt",
        value=research_prompt
    )

# NOTE: We'll gather multiple context snippets (transcripts, job postings, etc.)
st.markdown("Use the sections below to provide any client-related context (meeting transcripts, emails, etc.).")

# Replace the old render_dynamic_context_sections function with the new component call
context_snippets = render_dynamic_context_sections(st, prefix="client_onboarding", use_tabs=True)

# Renders field for describing the relevant people and their roles
people_and_roles, is_valid_roles = render_people_and_roles_field()

# Build and display an initial prompt example
prompt_placeholder = build_initial_prompt(context_snippets, people_and_roles)
st.text_area("Initial Prompt (Preview)", value=prompt_placeholder, height=100, disabled=True,
    help="This is a starter prompt referencing your context. Future expansions will generate deeper client details."
)

if st.button("Extract Onboarding Details", type="primary", disabled=not is_valid_roles):
    with st.spinner("Extracting details..."):
        messages = [{"role": "user", "content": prompt_placeholder}]
        response = completion(
            model=LLM_MODEL,
            messages=messages
        ).choices[0].message.content
        st.session_state.extracted_onboard_details = response

if 'extracted_onboard_details' in st.session_state:
    st.markdown("### 📋 Onboarding Details Extraction")
    st.text_area(
        label="Extracted Details",
        value=st.session_state.extracted_onboard_details,
        height=300
    )

st.markdown("---")
st.markdown("### 📋 Generate Client Profile")

profile_prompt = build_detailed_profile_prompt(context_snippets, people_and_roles)
# Preview of the detailed profile prompt
st.text_area(
    "Detailed Profile Prompt (Preview)",
    value=profile_prompt,
    height=100,
    disabled=True,
    help="This is the prompt that will be used to generate a detailed client and project profile."
)

if st.button("Generate Detailed Profile", type="primary", disabled=not is_valid_roles):
    with st.spinner("Generating detailed profile..."):
        messages = [{"role": "user", "content": profile_prompt}]
        response = completion(
            model=LLM_MODEL,
            messages=messages
        ).choices[0].message.content
        st.session_state.detailed_profile = response

if 'detailed_profile' in st.session_state:
    profile_col, chat_col = st.columns([0.5, 0.5])

    with profile_col:
        st.markdown("### 📊 Generated Profile")
        st.text_area(
            label="Generated Profile",
            value=st.session_state.detailed_profile,
            height=400
        )

    with chat_col:
        st.markdown("### 💬 Profile Refinement Chat")

        # Initialize chat messages in session state if not present
        if "profile_chat_messages" not in st.session_state:
            st.session_state.profile_chat_messages = []

        # This function is called whenever a new user message is sent
        def handle_profile_refinement(conversation_so_far):
            """
            Streams refinement responses from the LLM in response to user queries,
            and appends them to session state messages for display.

            Args:
                conversation_so_far: List of message dicts containing the conversation history
            """
            # Extract the last user message
            last_user_prompt = conversation_so_far[-1]["content"]

            # Combine the user's prompt with existing context
            additional_instructions = (
                "You are helping refine and clarify details about a client profile and project scoping.\n\n"
                "Original Context Snippets:\n"
                + "\n\n---\n\n".join(context_snippets)
                + "\n\nPeople & Roles:\n"
                + people_and_roles
                + "\n\nCurrent Profile:\n"
                + st.session_state.detailed_profile
                + "\n\nUser Query:\n"
                + last_user_prompt
            )

            # Build updated messages list for the LLM
            updated_messages = conversation_so_far[:-1]  # Everything except last user message
            updated_messages.append({
                "role": "user",
                "content": additional_instructions
            })

            return completion(
                model=LLM_MODEL,
                messages=updated_messages,
                stream=True
            )

        # Render the new generic chat component
        chat_component(
            messages_key="profile_chat_messages",
            response_stream=handle_profile_refinement,
            chat_height=400,
            prompt_label="Ask for clarification or details..."
        )

st.markdown("---")
st.markdown("### 📑 Project Title & Summary")

title_summary_prompt = build_title_and_summary_prompt(context_snippets, people_and_roles)
st.text_area(
    "Title & Summary Prompt (Preview)",
    value=title_summary_prompt,
    height=100,
    disabled=True,
    help="This prompt will generate project titles and a concise summary."
)

if st.button("Generate Titles & Summary", type="primary", disabled=not is_valid_roles):
    with st.spinner("Generating titles and summary..."):
        messages = [{"role": "user", "content": title_summary_prompt}]
        response = completion(
            model=LLM_MODEL,
            messages=messages
        ).choices[0].message.content
        st.session_state.title_summary = response

if 'title_summary' in st.session_state:
    summary_col, chat_col = st.columns([0.5, 0.5])

    with summary_col:
        st.markdown("### 📝 Generated Titles & Summary")
        st.text_area(
            label="Generated Content",
            value=st.session_state.title_summary,
            height=400
        )

    with chat_col:
        st.markdown("### 💬 Title & Summary Refinement Chat")

        if "title_summary_chat_messages" not in st.session_state:
            st.session_state.title_summary_chat_messages = []

        def handle_title_summary_refinement(conversation_so_far):
            """
            Streams refinement responses from the LLM in response to user queries,
            and appends them to session state messages for display.

            Args:
                conversation_so_far: List of message dicts containing the conversation history
            """
            # Extract the last user message
            last_user_prompt = conversation_so_far[-1]["content"]

            # Combine the user's prompt with existing context
            additional_instructions = (
                "You are helping refine and clarify the project titles and summary.\n\n"
                "Original Context Snippets:\n"
                + "\n\n---\n\n".join(context_snippets)
                + "\n\nPeople & Roles:\n"
                + people_and_roles
                + "\n\nCurrent Titles & Summary:\n"
                + st.session_state.title_summary
                + "\n\nUser Query:\n"
                + last_user_prompt
            )

            # Build updated messages list for the LLM
            updated_messages = conversation_so_far[:-1]  # Everything except last user message
            updated_messages.append({
                "role": "user",
                "content": additional_instructions
            })

            return completion(
                model=LLM_MODEL,
                messages=updated_messages,
                stream=True
            )

        chat_component(
            messages_key="title_summary_chat_messages",
            response_stream=handle_title_summary_refinement,
            chat_height=400,
            prompt_label="Ask for title/summary refinements..."
        )

