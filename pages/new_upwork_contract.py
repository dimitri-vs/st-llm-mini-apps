import streamlit as st
from utils.anthropic_llm import get_anthropic_completion

st.set_page_config(
    page_title="Agency Gen AI Mini-Apps",
    page_icon="🧪",
    layout="wide"
)

st.title("📝 Upwork Contract Info")

st.warning("This app page is currently under development. The generation component needs to be implemented.", icon="⚠️")

# Reset button in top-right
_, reset_col = st.columns([4, 1])
with reset_col:
    if st.button("Reset", icon="🗑️", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.cache_data.clear()
        st.rerun()

# Initialize text areas counter in session state
if 'text_areas_count' not in st.session_state:
    st.session_state.text_areas_count = 1

# Controls for adding/removing text areas
control_col1, control_col2 = st.columns(2)
with control_col1:
    if st.button("Add Section", icon="➕"):
        st.session_state.text_areas_count += 1
with control_col2:
    if st.button("Remove Section", icon="➖") and st.session_state.text_areas_count > 1:
        st.session_state.text_areas_count -= 1
        # Clean up removed text area from session state
        if f"text_area_{st.session_state.text_areas_count}" in st.session_state:
            del st.session_state[f"text_area_{st.session_state.text_areas_count}"]

st.warning("""
Make sure to use the following format for each context section:

> CONTEXT: A few words explaining what the snippet is about, why its relevant...
>
> {actual_context_snippet}
""".strip(), icon="ℹ️")

# Dynamic text areas for context sections
context_inputs = []
for i in range(st.session_state.text_areas_count):
    context_input = st.text_area(
        f"Context Section {i+1}",
        key=f"text_area_{i}",
        help="Paste relevant context, document excerpts, or message exchanges for this section"
    )
    if context_input:
        context_inputs.append(context_input)

# Combine all context inputs for the prompt
additional_context = "\n\n---\n\n".join(context_inputs) if context_inputs else ""

# Prompt template
contract_prompt = """
Your task is to draft a title and description for a new Upwork contract. I will provide you with what was discussed as requirements and scope so far and you can infer the future direction to help you craft an appropriate title and description for this new contract phase.

Additional Text Snippets

I will provide various snippets of text that may provide additional context about the client/project. They might be document excerpts, message exchanges, etc. Note that these snippets may not be directly relevant to the task at hand. Only reference them if pertinent.

<Additional Text Snippets>
{additional_context}
</Additional Text Snippets>

Response Guidelines

First, help me create a variety of three descriptive contract titles, each around 8 words. These titles should succinctly encapsulate the goal, scope and main platform/framework of the project as outlined above. The title should be in a concise, terms-focused, and abbreviation-heavy style with the use of industry-specific terms.

Then, write a description. The first half can a summary/overview of the project. The second half should also be in paragraph form and focus on the next steps, but subtly being open ended.

Lastly, list out any things that I might want to censor in this description for confidentiality or proprietary reasons. Prefix this section with an "⚠️" emoji
""".strip()

# Preview prompt
rendered_prompt = contract_prompt.format(
    additional_context=additional_context
)
st.text_area(
    "Rendered Prompt",
    value=rendered_prompt,
    disabled=True,
    help="This is the complete prompt that will be used to generate the contract info."
)

# # Generate button and results
# if st.button("Generate Contract Info", type="primary", disabled=not requirements_scope):
#     with st.spinner("Generating contract info..."):
#         messages = [{"role": "user", "content": rendered_prompt}]
#         response = get_anthropic_completion(messages)
#         st.session_state.contract_info = response

# # Display results
# if 'contract_info' in st.session_state:
#     st.markdown("### Generated Contract Info")
#     st.text_area(
#         label="Contract Titles and Description",
#         value=st.session_state.contract_info,
#         height=400
#     )