def render_dynamic_context_sections(st, prefix="context"):
    """
    A reusable, functional component that renders and validates an indeterminate number of text areas
    with metadata headers (e.g., "CONTEXT: ...") to capture contextual snippets.

    By default, it manages Streamlit session state keys using a unique prefix to avoid collisions with
    other pages that also use this component. For example:

        prefix="my_page"

    This will store relevant session keys like "my_page_context_sections_count".

    Returns:
        list: A list of validated context snippet strings.
    """

    # Build dynamic namespaced keys based on prefix
    count_key = f"{prefix}_context_sections_count"

    # Initialize if not already set
    if count_key not in st.session_state:
        st.session_state[count_key] = 1

    # Controls for adding and removing text areas
    control_col1, control_col2 = st.columns(2)
    with control_col1:
        if st.button("Add Snippet", key=f"{prefix}_add_snippet", icon="➕"):
            st.session_state[count_key] += 1
            new_key = f"{prefix}_context_section_{st.session_state[count_key] - 1}"
            if new_key not in st.session_state:
                # Initialize new text area with template
                st.session_state[new_key] = "CONTEXT: ______ 🔴\n\n"
    with control_col2:
        if (
            st.button("Remove Snippet", key=f"{prefix}_remove_snippet", icon="➖")
            and st.session_state[count_key] > 1
        ):
            st.session_state[count_key] -= 1
            removed_key = f"{prefix}_context_section_{st.session_state[count_key]}"
            if removed_key in st.session_state:
                del st.session_state[removed_key]

    # Collect context inputs
    context_inputs = []
    all_valid = True

    # Render each text area snippet
    for i in range(st.session_state[count_key]):
        key = f"{prefix}_context_section_{i}"
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
            f"Context Snippet {i+1}{metadata}",
            value=current_text,
            key=key,
            height=100,
            help=(
                "Start with 'CONTEXT: description' header, followed by the content. "
                "Remove the red dot (🔴) once completed."
            ),
        )

        # Validation: user must remove the 🔴 symbol
        is_valid = "🔴" not in context_input
        if not is_valid:
            all_valid = False
            st.warning(
                f"Complete context snippet {i+1} and remove the red dot (🔴).",
                icon="⚠️"
            )

        # Collect snippet if user has removed the red dot
        if context_input and is_valid:
            context_inputs.append(context_input)

    # Store overall validation state in session state
    st.session_state[f"{prefix}_context_snippets_valid"] = all_valid

    return context_inputs