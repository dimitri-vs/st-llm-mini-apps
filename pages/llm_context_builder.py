import streamlit as st

from utils.anthropic_llm import get_anthropic_completion, get_anthropic_json_completion, stream_anthropic_completion
from components.chat_component import chat_component
from components.dynamic_context_component import render_dynamic_context_sections

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
context_snippets = render_dynamic_context_sections(st, prefix="llm_context_builder")

# display the context snippets, but it might be a list of strings
combined_context = "\n\n---\n\n".join(context_snippets)

# Combine all context snippets with clear separation and XML tags
combined_context = f"<context>\n{combined_context}\n</context>" if combined_context.strip() else ""

st.text_area("combined_context", combined_context, disabled=True)

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

