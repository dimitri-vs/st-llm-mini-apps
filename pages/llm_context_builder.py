import streamlit as st

from utils.anthropic_llm import get_anthropic_completion, get_anthropic_json_completion, stream_anthropic_completion
from components.chat_component import chat_component
from components.dynamic_context_component import render_dynamic_context_sections
from components.clipboard_button import show_copy_button

st.set_page_config(
    page_title="Agency Gen AI Mini-Apps",
    page_icon="🧪",
    layout="wide"
)
st.title("🎯 LLM Context Builder")

st.markdown("""
Build and manage context for your LLM interactions. Add relevant information like documentation,
meeting notes, requirements, or any other context that will help shape the LLM's responses.
""")

# Provide a unique prefix to avoid collisions with other pages
context_snippets = render_dynamic_context_sections(st, prefix="llm_context_builder", use_tabs=True)

# display the context snippets, but it might be a list of strings
combined_context = "\n\n---\n\n".join(context_snippets)

# Combine all context snippets with clear separation and XML tags
combined_context = f"<context>\n{combined_context}\n</context>" if combined_context.strip() else ""

with st.expander("View Combined Context", expanded=False):
    st.text_area("combined_context", combined_context, disabled=True)


# Add prompt instructions text area
prompt_instructions = st.text_area(
    "Prompt",
    placeholder="Enter your instructions here.",
    help="Write instructions for how the LLM should use the context above. For example: 'Based on the context provided, summarize the key requirements.'"
)

if prompt_instructions and combined_context:
    full_prompt = prompt_instructions + "\n\n" + combined_context
    col1, col2 = st.columns([1, 4])
    with col1:
        show_copy_button(full_prompt)
    with col2:
        if st.checkbox("Show full prompt (debug)", False):
            st.text_area("Full Prompt", full_prompt, disabled=True, height=300)


# # Add a button to generate response
# if prompt_instructions and combined_context and st.button("Generate Response"):
#     with st.spinner("Generating response..."):
#         # Construct the full prompt with context and instructions
#         full_prompt = f"""Here is the relevant context:

# {combined_context}

# Instructions:
# {prompt_instructions}"""

#         # Stream the response using Anthropic's Claude
#         response_container = st.empty()
#         stream_anthropic_completion(
#             full_prompt,
#             response_container,
#             max_tokens=1000,
#             temperature=0.7
#         )

# # Add copy to clipboard button
# if combined_context.strip():  # Only show if there's content to copy
#     if st.button("📋 Copy to Clipboard"):
#         st.write("Context copied to clipboard! ✅")
#         st.session_state['clipboard'] = combined_context
#         # Using JavaScript to copy to clipboard
#         st.markdown(
#             f"""
#             <script>
#                 navigator.clipboard.writeText({repr(combined_context)});
#             </script>
#             """,
#             unsafe_allow_html=True
#         )

