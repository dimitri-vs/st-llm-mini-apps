def extract_smart_name(context_text):
    """Extract a smart name from context text for tabs/labels.

    Only processes first line of text starting with 'CONTEXT:', attempting to extract:
    1. Filename from file paths
    2. Page title from URLs
    3. First few words after CONTEXT:
    """
    if not context_text.startswith("CONTEXT:"):
        return None

    # Get the text after CONTEXT:
    header = context_text.split("\n", 1)[0].replace("CONTEXT:", "").strip()

    # Look for file paths
    if "/" in header or "\\" in header:
        # Split on both types of slashes and take the last part
        parts = header.replace("\\", "/").split("/")
        return parts[-1].strip()

    # Look for URLs
    if "http://" in header or "https://" in header:
        # Extract domain and path
        try:
            from urllib.parse import urlparse
            parsed = urlparse(header)
            # Take the last path component or domain if no path
            path_parts = parsed.path.split("/")
            return path_parts[-1] if path_parts[-1] else parsed.netloc
        except:
            pass

    # Default to first few words
    words = header.split()
    if words:
        return " ".join(words[:10]) + ("..." if len(words) > 10 else "")

    return None

def render_dynamic_context_sections(st, prefix="context", use_tabs=False):
    """
    A reusable, functional component that renders and validates an indeterminate number of text areas
    with metadata headers using expanders for better UX.

    By default, it manages Streamlit session state keys using a unique prefix to avoid collisions with
    other pages that also use this component. For example:

        prefix="my_page"

    This will store relevant session keys like "my_page_context_sections_count".

    Args:
        st: The Streamlit module instance
        prefix (str): Prefix for session state keys to avoid collisions
        use_tabs (bool): If True, renders snippets in tabs instead of stacked layout

    Returns:
        list: A list of validated context snippet strings.
    """

    # Build dynamic namespaced keys based on prefix
    count_key = f"{prefix}_context_sections_count"

    # Initialize if not already set
    if count_key not in st.session_state:
        st.session_state[count_key] = 1

    # Single key to track which snippet is being edited
    active_key = f"{prefix}_active_snippet"
    if active_key not in st.session_state:
        st.session_state[active_key] = 0  # Start with first snippet expanded

    # Controls for adding and removing text areas
    control_col1, control_col2, _ = st.columns(3)
    with control_col1:
        if st.button("Add Snippet", key=f"{prefix}_add_snippet", icon="➕"):
            st.session_state[count_key] += 1
            new_key = f"{prefix}_context_section_{st.session_state[count_key] - 1}"
            if new_key not in st.session_state:
                st.session_state[new_key] = "CONTEXT: ______ 🔴\n\n..."
            # Set only the new snippet to be expanded
            st.session_state[active_key] = st.session_state[count_key] - 1
    with control_col2:
        if (
            st.button("Remove Snippet", key=f"{prefix}_remove_snippet", icon="➖")
            and st.session_state[count_key] > 1
        ):
            st.session_state[count_key] -= 1
            removed_key = f"{prefix}_context_section_{st.session_state[count_key]}"
            if removed_key in st.session_state:
                del st.session_state[removed_key]
            # Clamp the active snippet index if needed
            if st.session_state[active_key] >= st.session_state[count_key]:
                st.session_state[active_key] = st.session_state[count_key] - 1

    # Collect context inputs
    context_inputs = []
    all_valid = True

    # Render snippets using expanders
    for i in range(st.session_state[count_key]):
        key = f"{prefix}_context_section_{i}"
        current_text = st.session_state.get(key, "CONTEXT: ______ 🔴\n\n")

        # Always use smart names now
        smart_name = extract_smart_name(current_text)
        label = smart_name if smart_name else f"Snippet {i+1}"

        with st.expander(label, expanded=(i == st.session_state[active_key])):
            # Store old value for comparison
            old_value = st.session_state.get(key)

            # When user interacts with text area, this snippet becomes active
            context_input, is_valid = render_single_snippet(st, i, prefix)

            # If text changed, make this snippet active
            if old_value and context_input != old_value:
                st.session_state[active_key] = i

            if not is_valid:
                all_valid = False
            if context_input:
                context_inputs.append(context_input)

    # Store overall validation state
    st.session_state[f"{prefix}_context_snippets_valid"] = all_valid

    return context_inputs

def render_single_snippet(st, index, prefix):
    """Helper function to render a single context snippet with validation."""
    key = f"{prefix}_context_section_{index}"
    if key not in st.session_state:
        st.session_state[key] = "CONTEXT: ______ 🔴\n\n"

    current_text = st.session_state[key]
    # Extract metadata for label if it exists
    metadata = ""
    if current_text.startswith("CONTEXT:"):
        first_line = current_text.split("\n", 1)[0].replace("CONTEXT:", "").strip()
        if first_line and "🔴" not in first_line:
            truncated = first_line[:80] + ("..." if len(first_line) > 80 else "")
            metadata = f" - {truncated}"

    # Render the text area
    context_input = st.text_area(
        f"Context Snippet {index+1}{metadata}",
        value=current_text,
        key=key,
        height=200,
        help=(
            "Start with 'CONTEXT: description' header, followed by the content. "
            "Remove the red dot (🔴) once completed."
        ),
    )

    # Validation: user must remove the 🔴 symbol
    is_valid = "🔴" not in context_input
    if not is_valid:
        st.warning(
            f"Complete context snippet {index+1} and remove the red dot (🔴).",
            icon="⚠️"
        )

    return context_input, is_valid