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

# Add prompt instructions text area
prompt_instructions = st.text_area(
    "Prompt",
    placeholder="Enter your instructions here.",
    help="Write instructions for how the LLM should use the context above. For example: 'Based on the context provided, summarize the key requirements.'",
    height=200
)

# Provide a unique prefix to avoid collisions with other pages
context_snippets = render_dynamic_context_sections(st, prefix="llm_context_builder", use_tabs=True)

# display the context snippets, but it might be a list of strings
combined_context = "\n\n---\n\n".join(context_snippets)

# Combine all context snippets with clear separation and XML tags
combined_context = f"<context>\n{combined_context}\n</context>" if combined_context.strip() else ""

# with st.expander("View Combined Context", expanded=False):
#     st.text_area("combined_context", combined_context, disabled=True)

full_prompt = f"""
{prompt_instructions}

Here is some relevant context:

{combined_context}
""".strip()


st.text_area("Full Prompt", full_prompt, disabled=True, height=200)
show_copy_button(full_prompt)

#TODO: switch to this UX after testing
# full_prompt = prompt_instructions + "\n\n" + combined_context
# col1, col2 = st.columns([1, 4])
# with col1:
#     show_copy_button(full_prompt)
# with col2:
#     if st.checkbox("Show full prompt (debug)", False):
#         st.text_area("Full Prompt", full_prompt, disabled=True, height=300)