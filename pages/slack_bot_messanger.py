import streamlit as st
from utils.slack import post_message_to_channel, slackify_markdown
from slack_sdk.errors import SlackApiError
import re

st.title("Slack Message Sender")

def is_valid_channel_id(channel_id: str) -> bool:
    """Basic validation for Slack channel ID format"""
    return channel_id.startswith(('C', 'G', 'D')) and len(channel_id) >= 9

def preview_slack_formatting(text: str) -> str:
    """Convert Slack mrkdwn to similar Markdown for preview"""
    # NOTE: Regex-based transformation from Slack formatting to similar Markdown
    preview = re.sub(r'(?<!\\)\*\*?(.*?)(?<!\\)\*\*?', r'**\1**', text)  # bold
    preview = re.sub(r'(?<!\\)_(.*?)(?<!\\)_', r'*\1*', preview)         # italic
    preview = re.sub(r'(?<!\\)~(.*?)(?<!\\)~', r'~~\1~~', preview)       # strikethrough
    preview = re.sub(r'(?<!\\)`([^`]+?)(?<!\\)`', r'`\1`', preview)      # code
    preview = re.sub(r'(?m)^>', r'> ', preview)                          # blockquotes
    return preview

channel_id = st.text_input(
    "Channel ID",
    value="C06CZKPP2AV",
    help="Enter the Slack channel ID (e.g., C01234567). You can find this in Slack by right-clicking the channel and selecting 'Copy link' - the ID is in the URL."
)

with st.expander("Formatting Help"):
    st.markdown("""
    You can use these Slack formatting options:
    - `*bold*` or `**bold**` → **bold**
    - `_italic_` or `*italic*` → *italic*
    - `~strikethrough~` → ~~strikethrough~~
    - `` `code` `` → `code`
    - ````preformatted```` → preformatted block
    - `>blockquote` → quoted text
    - `•` or `-` for bullet points
    - `1.` for numbered lists
    """)

message_slack = st.text_area(
    "Message",
    help="Enter the message you want to send. You can use Slack's formatting syntax (see Formatting Help above)."
)

use_markdown = st.checkbox(
    "Enable message formatting",
    value=True,
    help="Turn this off if you want to send the message exactly as written, without formatting."
)

if message_slack and use_markdown:
    with st.container(border=True):
        st.markdown(preview_slack_formatting(message_slack))

if st.button("Send Message"):
    if not channel_id or not message_slack:
        st.error("Please fill in both the channel ID and message fields.")
    elif not is_valid_channel_id(channel_id):
        st.error("Invalid channel ID format. It should start with C, G, or D and be at least 9 characters long.")
    else:
        try:
            # Convert markdown to Slack mrkdwn if formatting is enabled
            formatted_message = slackify_markdown(message_slack) if use_markdown else message_slack

            response = post_message_to_channel(
                channel_id,
                formatted_message,
                use_markdown=use_markdown
            )
            if response.get("ok"):
                st.success(f"Message sent successfully to channel {channel_id}!")
                with st.expander("Message Details"):
                    st.write("Message Timestamp:", response.get("ts"))
                    st.write("Channel:", response.get("channel"))
                    if "message" in response:
                        st.write("Message Content:", response["message"].get("text", message_slack))
            else:
                st.warning("Message sent but response indicates potential issues.")
        except ValueError as e:
            st.error(str(e))
        except SlackApiError as e:
            st.error(f"Failed to send message: {e.response['error']}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")