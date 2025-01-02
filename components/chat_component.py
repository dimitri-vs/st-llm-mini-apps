import streamlit as st

def chat_component(
    messages_key="chat_messages",
    on_send_message=None,
    chat_height=400,
    reset_button_label="Reset Chat",
    prompt_label="Type your message...",
    border=True,
):
    """
    Renders a general-purpose chat UI using Streamlit.
    Minimally requires:
       - A messages_key in st.session_state for storing chat messages.
       - An on_send_message callback to handle new user messages.

    :param messages_key: Session state key where chat messages are stored as a list of dicts
                         with "role" and "content" entries.
    :param on_send_message: (callable) A function that is called with the user input text
                            whenever the user sends a new message.
    :param chat_height: Height for the chat container (in pixels).
    :param reset_button_label: Label for the button that resets the chat.
    :param prompt_label: Placeholder label for the user's chat input field.
    :param border: Whether to show a border around the chat container.
    """

    # Show a Reset Chat button if we already have messages in session state.
    if st.session_state.get(messages_key, []):
        if st.button(reset_button_label, key=f"reset_btn_{messages_key}"):
            st.session_state[messages_key] = []
            st.rerun()

    # Create the scrollable container for the chat area
    chat_container = st.container(border=border, height=chat_height)

    with chat_container:
        # Display existing messages from session state
        for msg in st.session_state.get(messages_key, []):
            st.chat_message(msg["role"]).write(msg["content"])

    # Provide an input box for the user's next prompt
    user_text = st.chat_input(prompt_label, key=f"chat_input_{messages_key}")
    if user_text and on_send_message is not None:
        # Immediately display user's message in the UI
        # chat_container.chat_message("user").write(user_text)

        # Call the provided callback to handle the new user message
        on_send_message(user_text)