import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from utils.slack import get_channel_messages
from slack_sdk.errors import SlackApiError
import re

st.title("Slack Conversation Viewer")

# Date range selection
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime.now().date() - timedelta(days=7),
        help="Select the start date for the conversation range"
    )
with col2:
    end_date = st.date_input(
        "End Date",
        value=datetime.now().date(),
        help="Select the end date for the conversation range"
    )

# Channel ID input
channel_id = st.text_input(
    "Channel ID",
    help="Enter the Slack channel ID (e.g., C01234567). You can find this in Slack by right-clicking the channel and selecting 'Copy link' - the ID is in the URL."
)

# Option to include thread replies
include_threads = st.checkbox("Include thread replies", value=True)

st.caption("Remember to add the bot (Integrations > Apps) to the channel!")

# Function to format timestamp
def format_timestamp(ts):
    dt = datetime.fromtimestamp(float(ts))
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Function to convert messages to markdown
def messages_to_markdown(messages):
    # Reverse the messages list to show newest first
    messages = list(reversed(messages))

    markdown = ""
    for msg in messages:
        # Skip messages without text
        if not msg.get("text"):
            continue

        # Format timestamp
        time_str = format_timestamp(msg["ts"])

        # Get user info - now using the username field directly
        user_name = msg.get("username", "Unknown User")

        # Format the message
        markdown += f"**{user_name} - {time_str}**\n\n"
        markdown += f"{msg['text']}\n\n"

        # Add thread replies if available
        if include_threads and "thread_replies" in msg and msg["thread_replies"]:
            markdown += "#### Thread replies:\n\n"
            # Thread replies should still be in chronological order (oldest first)
            for reply in msg["thread_replies"]:
                reply_time = format_timestamp(reply["ts"])
                reply_user_name = reply.get("username", "Unknown User")

                markdown += f"**{reply_user_name}** - {reply_time}\n\n"
                markdown += f"{reply['text']}\n\n"

            markdown += "---\n\n"
        else:
            markdown += "---\n\n"

    return markdown

if st.button("Fetch Conversation"):
    if not channel_id:
        st.error("Please enter a channel ID.")
    else:
        try:
            with st.spinner("Fetching messages..."):
                # Convert dates to ISO format for the API
                start_time = f"{start_date}T00:00:00"
                end_time = f"{end_date}T23:59:59"

                # Get messages
                messages = get_channel_messages(
                    channel_id=channel_id,
                    start_time=start_time,
                    end_time=end_time,
                    get_threads=include_threads
                )

                if not messages:
                    st.info("No messages found in the selected date range.")
                else:
                    # Display message count
                    st.success(f"Found {len(messages)} messages")

                    # Convert to markdown
                    markdown_content = messages_to_markdown(messages)

                    # Display raw markdown in a disabled text area
                    st.text_area("Raw Markdown", markdown_content, height=300, disabled=True)

                    # Provide download option
                    st.download_button(
                        "Download as Markdown",
                        markdown_content,
                        file_name=f"slack_conversation_{channel_id}_{start_date}_to_{end_date}.md",
                        mime="text/markdown"
                    )

                    # Display the conversation
                    with st.expander("Conversation Preview", expanded=False):
                        st.markdown(markdown_content)

        except SlackApiError as e:
            st.error(f"Slack API Error: {e.response['error']}")
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

with st.expander("How to find a Channel ID"):
    st.markdown("""
    1. **In Slack Desktop App**: Right-click on the channel name → Select "Copy link" → The ID is the part after the last slash in the URL
    2. **In Slack Web App**: Click on the channel name in the sidebar → The ID will be in the URL (e.g., `.../browse/C01234567`)

    The Channel ID typically starts with:
    - `C` for public and private channels
    - `D` for direct messages
    - `G` for group messages/multi-person DMs
    """)