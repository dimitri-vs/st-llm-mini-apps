import os
import re
import urllib.parse
from typing import Dict, Any

import mistune
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv()

# Elevate Code Bot Settings: https://api.slack.com/apps/A06CZA1Q8D7

# Slack's zero-width space for avoiding certain in-word formatting issues
ZWS = "\u200B"

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
    ZWS = '\u200B'  # Zero-width space, though we won't use it in simple version
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

def invite_bot_to_channel(channel_id: str) -> dict:
    """
    Invites the bot to the specified channel.

    Args:
        channel_id (str): The ID of the channel to invite the bot to

    Returns:
        dict: Slack API response
    """
    slack_bot_token = os.environ.get("SLACK_BOT_USER_TOKEN")
    if not slack_bot_token:
        raise ValueError("SLACK_BOT_USER_TOKEN environment variable is not set")

    client = WebClient(token=slack_bot_token)
    # Get bot user ID from the auth test
    auth_response = client.auth_test()
    bot_user_id = auth_response["user_id"]

    # Invite bot to channel
    response = client.conversations_invite(
        channel=channel_id,
        users=[bot_user_id]
    )
    return response

if __name__ == "__main__":
    test_simple_slackify()
