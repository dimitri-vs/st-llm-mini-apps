import os
import re
import urllib.parse
from typing import Dict, Any, List
from datetime import datetime

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

# Elevate Code Bot Settings: https://api.slack.com/apps/A06CZA1Q8D7

def post_message_to_channel(channel_id: str, message: str, use_markdown: bool = True) -> Dict[str, Any]:
    """
    Posts a message to a specific Slack channel using the SLACK_BOT_USER_TOKEN.
    Raises ValueError if token is not set, or SlackApiError if the API call fails.
    """
    slack_bot_token = os.environ.get("SLACK_BOT_USER_TOKEN")
    if not slack_bot_token:
        raise ValueError("SLACK_BOT_USER_TOKEN environment variable is not set")

    client = WebClient(token=slack_bot_token)
    try:
        response = client.chat_postMessage(
            channel=channel_id,
            text=message,
            mrkdwn=use_markdown
        )
        return {
            "channel": response["channel"],
            "ts": response["ts"],
            "message": response["message"],
            "ok": response["ok"]
        }
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")
        raise

def get_channel_messages(
    channel_id: str,
    start_time: str,
    end_time: str,
    get_threads: bool = False
) -> List[Dict[str, Any]]:
    """
    Retrieves messages from a Slack channel within a specified date range.
    Optionally fetches thread replies if get_threads is True.

    Args:
        channel_id: The ID of the channel to fetch messages from.
        start_time: ISO 8601 timestamp for start date (e.g., "2024-03-20T00:00:00").
        end_time: ISO 8601 timestamp for end date (e.g., "2024-03-21T00:00:00").
        get_threads: If True, any message with a thread_ts will have replies fetched and nested.

    Returns:
        A list of message objects with relevant fields and optional thread replies.

    Raises:
        ValueError: If token is not set.
        SlackApiError: If the API call fails.
    """
    slack_bot_token = os.environ.get("SLACK_BOT_USER_TOKEN")
    if not slack_bot_token:
        raise ValueError("Slack bot token not found in environment variables.")

    client = WebClient(token=slack_bot_token)

    user_map = fetch_user_map(client)
    channel_map = fetch_channel_map(client)

    messages = []

    try:
        start_ts = int(datetime.fromisoformat(start_time).timestamp())
        end_ts = int(datetime.fromisoformat(end_time).timestamp())
        cursor = None

        while True:
            result = client.conversations_history(
                channel=channel_id,
                limit=200,
                oldest=str(start_ts),
                latest=str(end_ts),
                cursor=cursor
            )

            for msg in result["messages"]:
                parsed = parse_message(msg, user_map, channel_map)

                if get_threads and "thread_ts" in msg and msg.get("reply_count", 0) > 0:
                    thread_replies = fetch_thread_replies(
                        client,
                        channel_id,
                        msg["thread_ts"],
                        user_map,
                        channel_map
                    )
                    parsed["thread_replies"] = thread_replies

                messages.append(parsed)

            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        return messages

    except SlackApiError as e:
        print(f"Error fetching messages: {e.response['error']}")
        raise

def simple_slackify(text: str) -> str:
    """
    Converts basic Markdown to Slack-flavored Markdown using regex patterns.
    Handles essential formatting: bold, italic, strike, code, links, and escaping.
    """
    # Store code blocks temporarily
    code_blocks = {}
    code_counter = 0

    def save_code_block(match):
        nonlocal code_counter
        placeholder = f"CODE_BLOCK_{code_counter}"
        code_blocks[placeholder] = match.group(0)
        code_counter += 1
        return placeholder

    # Save code blocks
    text = re.sub(r'```[\s\S]*?```', save_code_block, text)
    text = re.sub(r'`[^`]+`', save_code_block, text)

    # Save Slack special syntax
    special_mentions = {}
    counter = 0

    def save_special(match):
        nonlocal counter
        placeholder = f"SPECIAL_{counter}"
        special_mentions[placeholder] = match.group(0)
        counter += 1
        return placeholder

    # Save @mentions, #channels, and !commands
    text = re.sub(r'<[@#!][^>]+>', save_special, text)

    # Save already escaped mentions
    text = re.sub(r'&lt;!(?:channel|here|everyone)&gt;', save_special, text)

    # Basic character escaping
    text = text.replace("&", "&amp;")
    text = re.sub(r'<(?![@#!])', '&lt;', text)
    text = text.replace(">", "&gt;")

    # Basic formatting
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)  # Bold
    text = re.sub(r'(?<!_)_(.+?)_(?!_)', r'_\1_', text)  # Italic
    text = re.sub(r'~~(.+?)~~', r'~\1~', text)  # Strikethrough

    # Links
    def process_link(match):
        text, url = match.groups()
        if not url.startswith(('http://', 'https://', 'mailto:')):
            return text
        return f"<{url}|{text}>"

    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', process_link, text)

    # Lists
    text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)

    # Restore code blocks
    for placeholder, code in code_blocks.items():
        text = text.replace(placeholder, code)

    # Restore special mentions
    for placeholder, mention in special_mentions.items():
        text = text.replace(placeholder, mention)

    # Ensure single newline at end
    text = text.rstrip() + '\n'

    return text

def test_simple_slackify():
    """
    Comprehensive test suite for simple_slackify function, adapted from the original test cases
    but with simplified output expectations.
    """
    tests = [
        # Basic formatting
        ("**bold**", "*bold*\n"),
        ("_italic_", "_italic_\n"),
        ("~~strike~~", "~strike~\n"),
        ("normal **bold** _italic_ ~~strike~~ `code`",
         "normal *bold* _italic_ ~strike~ `code`\n"),

        # Lists
        ("- First item\n- Second item", "• First item\n• Second item\n"),
        ("* First\n* Second", "• First\n• Second\n"),

        # Links
        ("[test](http://example.com)", "<http://example.com|test>\n"),
        ("[test](/invalid)", "test\n"),  # Invalid URLs just return text

        # Code blocks
        ("```\ncode block\n```", "```\ncode block\n```\n"),
        ("some `inline *code*` here", "some `inline *code*` here\n"),

        # Special mentions and escaping
        ("<@USER123>", "<@USER123>\n"),
        ("<#C123ABC456>", "<#C123ABC456>\n"),
        ("<!here> <!channel> <!everyone>", "<!here> <!channel> <!everyone>\n"),
        ("Use &lt;!channel&gt; to escape", "Use &lt;!channel&gt; to escape\n"),

        # Character escaping
        ("Text with & < >", "Text with &amp; &lt; &gt;\n"),
        ("*h&ello>world<", "*h&amp;ello&gt;world&lt;\n"),

        # Mixed formatting
        ("**_bold italic_**", "*_bold italic_*\n"),
        ("normal **bold** *italic* ~~strike~~ `code`",
         "normal *bold* _italic_ ~strike~ `code`\n"),

        # URLs and links
        ("https://example.com/path with spaces",
         "https://example.com/path with spaces\n"),

        # Paragraphs and spacing
        ("para 1\n\npara 2", "para 1\n\npara 2\n"),
        ("text\n\n> quoted text\n\ntext", "text\n\n> quoted text\n\ntext\n"),

        # Nested lists
        ("- **top**\n  - sub\n    - sub-sub\n- **more?**",
         "• *top*\n  • sub\n    • sub-sub\n• *more?*\n"),

        # Indentation preservation
        ("Normal text\n    Indented text\n        Double indented",
         "Normal text\n    Indented text\n        Double indented\n"),

        # Code block with internal formatting
        ("```\n**bold** in code\n```", "```\n**bold** in code\n```\n"),
        ("`**bold** in inline`", "`**bold** in inline`\n"),

        # Multiple consecutive formatting
        ("**bold** _italic_ ~~strike~~ `code`",
         "*bold* _italic_ ~strike~ `code`\n"),

        # Edge cases
        ("", "\n"),
        # (" ", " \n"),
        ("**", "**\n"),
        ("__", "__\n"),
        ("```", "```\n"),
    ]

    failures = []
    for input_text, expected in tests:
        result = simple_slackify(input_text)
        if result != expected:
            failures.append({
                'name': f"Test for: {input_text[:30]}{'...' if len(input_text) > 30 else ''}",
                'input': input_text,
                'expected': expected,
                'got': result
            })

    # Test summary
    print("\n=== Simple Slackify Test Summary ===")
    if failures:
        print(f"❌ {len(failures)} tests failed:")
        for f in failures:
            print(f"\nTest: {f['name']}")
            print(f"Input   : {repr(f['input'])}")
            print(f"Expected: {repr(f['expected'])}")
            print(f"Got     : {repr(f['got'])}")
        print(f"\nTotal: {len(failures)} failed")
    else:
        print("✨ All simple_slackify tests passed successfully!")

def fetch_user_map(client: WebClient) -> Dict[str, str]:
    """
    Returns a dict mapping user IDs (e.g., 'U12345') to a user-friendly name (e.g., 'Dave Smith').
    """
    user_map = {}
    try:
        cursor = None
        while True:
            response = client.users_list(cursor=cursor)
            for user in response["members"]:
                user_id = user["id"]
                name = user["profile"].get("display_name") or user["profile"].get("real_name") or user["name"]
                user_map[user_id] = name

            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
    except SlackApiError as e:
        print(f"Error fetching users: {e.response['error']}")
        raise
    return user_map

def fetch_channel_map(client: WebClient) -> Dict[str, str]:
    """
    Returns a dict mapping channel IDs (e.g., 'C12345') to channel names (e.g., 'general').
    """
    channel_map = {}
    try:
        cursor = None
        while True:
            response = client.conversations_list(
                cursor=cursor,
                types="public_channel,private_channel"
            )
            for ch in response["channels"]:
                channel_map[ch["id"]] = ch["name"]
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
    except SlackApiError as e:
        print(f"Error fetching channels: {e.response['error']}")
        raise
    return channel_map

def replace_slack_ids_in_text(
    text: str,
    user_map: Dict[str, str],
    channel_map: Dict[str, str]
) -> str:
    """
    Detects patterns like <@U12345> and <#C12345> in the text
    and replaces them with a friendlier name.
    """
    pattern = r"<(@|#)([A-Z0-9]+)(?:\|[^>]+)?>"

    def replacer(match):
        prefix = match.group(1)
        id_part = match.group(2)

        if prefix == "@":
            return f"@{user_map.get(id_part, 'unknown_user')}"
        elif prefix == "#":
            return f"#{channel_map.get(id_part, 'unknown_channel')}"

    return re.sub(pattern, replacer, text)

def parse_message(
    message: Dict[str, Any],
    user_map: Dict[str, str],
    channel_map: Dict[str, str]
) -> Dict[str, Any]:
    """
    Extract only the relevant Slack message fields and replace ID placeholders in text.
    """
    user_id = message.get("user")

    parsed = {
        "user": user_id,
        "username": user_map.get(user_id, "Unknown User") if user_id else "Unknown User",
        "team": message.get("team"),
        "ts": message.get("ts"),
        "type": message.get("type"),
        "text": replace_slack_ids_in_text(
            message.get("text", ""),
            user_map,
            channel_map
        ),
    }
    if "thread_ts" in message:
        parsed["thread_ts"] = message["thread_ts"]
    if "reply_count" in message:
        parsed["reply_count"] = message["reply_count"]
    return parsed

def fetch_thread_replies(
    client: WebClient,
    channel_id: str,
    thread_ts: str,
    user_map: Dict[str, str],
    channel_map: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Fetch the full conversation (including replies) for a thread.
    """
    replies = []
    try:
        cursor = None
        while True:
            response = client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                cursor=cursor
            )
            child_messages = [
                m for m in response["messages"]
                if m["ts"] != thread_ts
            ]

            for msg in child_messages:
                replies.append(parse_message(msg, user_map, channel_map))

            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
    except SlackApiError as e:
        print(f"Error fetching thread replies: {e.response['error']}")
        raise
    return replies

if __name__ == "__main__":
    r = get_channel_messages(channel_id="C084CLRBW6L", start_time="2025-01-29T00:00:00", end_time="2025-01-30T23:59:59")
    print(r)
