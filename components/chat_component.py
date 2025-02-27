import streamlit as st

def chat_component(
    messages_key="chat_messages",
    response_stream=None,
    chat_height=400,
    prompt_label="Type your message...",
    border=True,
    show_debug=False,
):
    """
    Renders a general-purpose chat UI using Streamlit.

    Parameters:
        messages_key (str): Key for storing chat messages in session state
        response_stream (Generator[str, Any, None]): Function that yields response chunks
        chat_height (int): Height of chat container in pixels
        prompt_label (str): Placeholder text for the input field
        border (bool): Whether to show container border
        show_debug (bool): Whether to show debug information about the message thread

    Examples:
        # Basic usage with default model settings
        chat_component(
            messages_key="chat_messages",
            response_stream=stream_anthropic_completion
        )

        # Using Claude with custom temperature and max tokens
        chat_component(
            messages_key="chat_messages",
            response_stream=lambda messages: stream_anthropic_completion(
                messages,
                temperature=0.3,
                max_tokens=2000
            )
        )

        # Using a specific Claude model with custom settings
        def custom_claude_stream(messages):
            return stream_anthropic_completion(
                messages,
                model="claude-3-opus-20240229",
                temperature=0.7,
                max_tokens=4000
            )

        chat_component(
            messages_key="chat_messages",
            response_stream=custom_claude_stream,
            chat_height=600
        )
    """

    # Add debug view before the chat container if enabled
    if show_debug:
        with st.expander("🔍 Debug: Message Thread", expanded=False):
            st.code(
                str(st.session_state.get(messages_key, [])),
                language="python"
            )

    # Create the scrollable container for the chat area
    chat_container = st.container(border=border, height=chat_height)

    with chat_container:
        # Show a Reset Chat button if we already have messages in session state.
        if st.session_state.get(messages_key, []):
            if st.button("Reset Chat", key=f"reset_btn_{messages_key}"):
                st.session_state[messages_key] = []
                st.rerun()

        # Display existing messages from session state
        for msg in st.session_state.get(messages_key, []):
            st.chat_message(msg["role"]).write(msg["content"])

        # Provide an input box for the user's next prompt
        user_text = st.chat_input(prompt_label, key=f"chat_input_{messages_key}")
        if user_text:

            if messages_key not in st.session_state:
                st.session_state[messages_key] = []

            # Add user message and prepare context
            st.session_state[messages_key].extend([
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": ""}  # Empty placeholder for streaming
            ])
            chat_container.chat_message("user").write(user_text)

            # Stream the response if a streaming function is provided
            if response_stream:
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    response_content = ""

                    print(st.session_state[messages_key])
                    for chunk in response_stream(st.session_state[messages_key][:-1]):
                        # Extract content from the LiteLLM streaming format
                        # LiteLLM uses OpenAI-compatible format where content is in choices[0].delta.content
                        chunk_content = ""
                        if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                            if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content'):
                                chunk_content = chunk.choices[0].delta.content or ""

                        response_content += chunk_content
                        st.session_state[messages_key][-1]["content"] = response_content
                        response_placeholder.markdown(response_content)

            st.rerun()