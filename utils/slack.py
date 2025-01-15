import os
import re
import urllib.parse
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from typing import Dict, Any
import mistune

load_dotenv()

def post_message_to_channel(channel_id: str, message: str, use_markdown: bool = True) -> Dict[str, Any]:
    """
    Posts a message to a specific Slack channel using a bot token.

    Args:
        channel_id (str): The ID of the channel to post to (e.g., 'C01234567')
        message (str): The message text to post
        use_markdown (bool): Whether to parse the message as Slack's mrkdwn format. Defaults to True.

    Returns:
        Dict[str, Any]: Clean response with relevant message details

    Raises:
        SlackApiError: If the message fails to send
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

def preprocess_bullets(text: str) -> str:
    """
    Replace leading Markdown bullets with Slack bullets (•) and convert ALL leading spaces
    to non-breaking spaces to preserve indentation in Slack.
    """
    lines = text.splitlines()
    results = []

    # Regex to capture leading spaces, bullet marker, then the rest of the line
    bullet_pattern = re.compile(r"^(?P<spaces>\s*)(?:[-*]|(\d+\.))\s+(?P<rest>.*)")

    for line in lines:
        match = bullet_pattern.match(line)
        if match:
            # Found a bullet line
            spaces = match.group("spaces") or ""
            rest = match.group("rest") or ""

            # Convert ALL spaces (not just leading) to non-breaking spaces
            nb_spaces = spaces.replace(" ", "\u00A0")
            results.append(f"{nb_spaces}• {rest}")
        else:
            # Not a bullet line, but still convert leading spaces
            leading_spaces = re.match(r"^(?P<spaces>\s*)(?P<rest>.*)", line)
            if leading_spaces:
                spaces = leading_spaces.group("spaces")
                rest = leading_spaces.group("rest")
                nb_spaces = spaces.replace(" ", "\u00A0")
                results.append(f"{nb_spaces}{rest}")
            else:
                results.append(line)

    return "\n".join(results)

class SlackifyRenderer(mistune.HTMLRenderer):
    """
    Custom Mistune renderer to output Slack-compatible Markdown.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ZWS = "\u200B"  # Slack's zero-width space

    def text(self, text, **kwargs):
        patterns = {
            'user_mentions': r'<@[^>]+>',
            'channel_links': r'<#[^>]+>',
            'special_mentions': r'<!(?:here|channel|everyone)>',
            'escaped_mentions': r'&lt;!(?:here|channel|everyone)&gt;'
        }
        placeholders = {}
        counter = 0

        # Replace patterns with placeholders
        for pattern_type, pattern in patterns.items():
            def save_match(match):
                nonlocal counter
                placeholder = f"PLACEHOLDER_{counter}"
                placeholders[placeholder] = match.group(0)
                counter += 1
                return placeholder

            text = re.sub(pattern, save_match, text)

        # Escape special characters
        text = text.replace("&", "&amp;")
        text = re.sub(r'<(?!@)', '&lt;', text)
        text = text.replace(">", "&gt;")

        # Restore placeholders
        for placeholder, original in placeholders.items():
            text = text.replace(placeholder, original)

        return text

    def heading(self, text, level, **kwargs):
        # Keep the original text and add double newline
        return f"*{text}*\n\n"

    def paragraph(self, text, **kwargs):
        """Ensure proper paragraph spacing."""
        # Add double newline after paragraphs
        return f"{text}\n\n"

    def strong(self, text, **kwargs):
        """Consistent strong/bold formatting."""
        # Don't modify the input text, just wrap with asterisks
        return f"{self.ZWS}*{text}*{self.ZWS}"

    def emphasis(self, text, **kwargs):
        """Consistent emphasis/italic formatting."""
        # Don't modify the input text, just wrap with underscores
        return f"{self.ZWS}_{text}_{self.ZWS}"

    def del_text(self, text, **kwargs):
        # Slack strikethrough => zero-width-space + ~ + text + ~ + zero-width-space
        return f"{self.ZWS}~{text}~{self.ZWS}"

    def strikethrough(self, text, **kwargs):
        # Slack strikethrough => zero-width-space + ~ + text + ~ + zero-width-space
        return f"{self.ZWS}~{text}~{self.ZWS}"

    def link(self, text, url, title=None, **kwargs):
        """
        Convert [text](url) to Slack style: <url|text>, or <url> if no text.
        Invalid URLs become just the text itself.
        """
        if not url:
            return text or ""

        if is_valid_url(url):
            if text:
                return f"<{url}|{text}>"
            else:
                return f"<{url}>"
        return text or url

    def block_code(self, code, info=None, **kwargs):
        """
        Code blocks become triple backticks.
        Remove any `#!language` first (as in the slackify-markdown code).
        """
        # Remove the first line if it starts with #!something
        code = re.sub(r"^#![a-zA-Z0-9]+\n", "", code)
        # Remove trailing newlines before adding our own
        code = code.rstrip()
        return f"```\n{code}\n```\n"

    def codespan(self, text, **kwargs):
        # Slack prefers single backticks for inline code
        return f"`{text}`"

    def block_quote(self, text, **kwargs):
        """Format blockquotes with proper spacing."""
        text = text.rstrip('\n')
        lines = text.split('\n')
        quoted = "\n".join(f"> {line}" for line in lines)
        # Ensure double newline at end
        return f"{quoted}\n\n"

    def hrule(self, **kwargs):
        # Slack doesn’t have a special HR syntax, we can just return a line of dashes
        return "---\n\n"

    def newline(self):
        # Render soft line breaks as actual newlines
        return "\n"

def slackify_markdown(markdown_text: str) -> str:
    """
    Convert standard Markdown to Slack-flavored Markdown in one step.
    """
    # Step 1: Replace Markdown bullets with Slack bullets, preserve indentation
    preprocessed = preprocess_bullets(markdown_text)

    # Step 2: Use Mistune with our SlackifyRenderer
    md = mistune.create_markdown(
        renderer=SlackifyRenderer(),
        plugins=['strikethrough']
    )
    slack_text = md(preprocessed)

    # Only collapse multiple newlines if the text doesn't end with a blockquote
    if not slack_text.rstrip().endswith('\n\n') or not any(line.startswith('> ') for line in slack_text.splitlines()[-2:]):
        slack_text = re.sub(r"\n{2,}$", "\n", slack_text)

    # Ensure exactly one trailing newline
    if not slack_text.endswith("\n"):
        slack_text += "\n"

    return slack_text

def test_md_to_slack():
    """Test markdown to Slack conversion with key formatting cases."""
    ZWS = '\u200B'  # Zero-width space
    failures = []

    def run_test(name: str, input_md: str, expected: str):
        print(f"\nTesting: {name}")
        print(f"Input   : {repr(input_md)}")
        result = slackify_markdown(input_md)
        print(f"Result  : {repr(result)}")
        print(f"Expected: {repr(expected)}")

        if result != expected:
            failures.append({
                'name': name,
                'input': input_md,
                'expected': expected,
                'got': result
            })
            print("✗ Failed")
        else:
            print("✓ Passed")

    # Test cases with descriptive names
    run_test("Simple text",
        'hello world',
        'hello world\n')

    run_test("Escaped characters",
        '*h&ello>world<',
        '*h&amp;ello&gt;world&lt;\n')

    run_test("Headers simplification",
        'paragraph1\n\nparagraph2',
        'paragraph1\n\nparagraph2\n')

    run_test("Bold text",
        '**bold**',
        f'{ZWS}*bold*{ZWS}\n')

    run_test("Italic text",
        '*italic*',
        f'{ZWS}_italic_{ZWS}\n')

    run_test("Inline formatting",
        'he**l**lo',
        f'he{ZWS}*l*{ZWS}lo\n')

    run_test("Strikethrough",
        '~~strike~~',
        f'{ZWS}~strike~{ZWS}\n')

    run_test("Unordered lists",
        '* list\n* list',
        '• list\n• list\n')

    run_test("Links with text",
        '[test](http://example.com)',
        '<http://example.com|test>\n')

    run_test("Links without text",
        '[](http://example.com)',
        '<http://example.com>\n')

    run_test("Invalid links",
        '[test](/invalid)',
        'test\n')

    run_test("Code blocks",
        '```\ncode block\n```',
        '```\ncode block\n```\n')

    run_test("Code blocks with language",
        '```python\ncode block\n```',
        '```\ncode block\n```\n')

    run_test("Inline code",
        'some `inline *code*` here',
        'some `inline *code*` here\n')

    run_test("User mentions",
        '<@USER123>',
        '<@USER123>\n')

    run_test("Blockquotes",
        'text\n\n> quoted text\n\ntext',
        'text\n\n> quoted text\n\ntext\n')

    run_test("Nested formatting",
        '**_bold italic_**',
        f'{ZWS}*{ZWS}_bold italic_{ZWS}*{ZWS}\n')

    # run_test("Mixed lists",
    #     '1. numbered\n* bullet\n2. numbered again',
    #     '1.   numbered\n•   bullet\n2.   numbered again\n')

    run_test("Multiple paragraphs",
        'para 1\n\npara 2',
        'para 1\n\npara 2\n')

    run_test("Complex links",
        '[**bold** link](https://example.com)',
        f'<https://example.com|{ZWS}*bold*{ZWS} link>\n')

    run_test("Mixed inline formatting",
        'normal **bold** *italic* ~~strike~~ `code`',
        f'normal {ZWS}*bold*{ZWS} {ZWS}_italic_{ZWS} {ZWS}~strike~{ZWS} `code`\n')

    # Add new test case before the summary
    run_test("Complex nested list",
        """
- **top**
  - sub
    - sub-sub
- **more?**""".strip(),
        f"• {ZWS}*top*{ZWS}\n\u00A0\u00A0• sub\n\u00A0\u00A0\u00A0\u00A0• sub-sub\n• {ZWS}*more?*{ZWS}\n")

    # more complex nested list
    run_test("Extra new lines after list",
        """
Para

- bullet1
- bullet2
- bullet3

Para2
""".strip(),
        f"Para\n\n• bullet1\n• bullet2\n• bullet3\n\nPara2\n")

    # More test cases to match Slack's official formatting:

    # run_test("Basic formatting",
    #     '_italic_ *bold* ~strike~',
    #     f'{ZWS}_italic_{ZWS} {ZWS}*bold*{ZWS} {ZWS}~strike~{ZWS}\n')

    run_test("Channel links",
        '<#C123ABC456>',
        '<#C123ABC456>\n') # where #C123ABC456 is a channel id

    run_test("User mentions",
        '<@U123ABC456>',
        '<@U123ABC456>\n') # eg. "Hey <@U012AB3CD>!"

    run_test("Formatting of special mentions",
        '<!here> <!channel> <!everyone>',
        '<!here> <!channel> <!everyone>\n')

    run_test("Code blocks",
        '```\ncode block\n```',
        '```\ncode block\n```\n')

    run_test("Lists",
        '- First item\n- Second item',
        '• First item\n• Second item\n')

    run_test("URL with spaces (should not link)",
        'https://example.com/path with spaces',
        'https://example.com/path with spaces\n')

    run_test("Special mention escaping",
        'Use &lt;!channel&gt; to escape channel mention',
        'Use &lt;!channel&gt; to escape channel mention\n')

    run_test("Simple bullet list",
        '• First\n• Second',
        '• First\n• Second\n')

    # Add new test case for indentation preservation
    run_test("Indented list with formatting",
        """
- **top**
  - sub
    - sub-sub
""".strip(),
        f"• {ZWS}*top*{ZWS}\n\u00A0\u00A0• sub\n\u00A0\u00A0\u00A0\u00A0• sub-sub\n")

    # Add test for general indentation
    run_test("Indented paragraphs",
        """Normal text
    Indented text
        Double indented""",
        f"Normal text\n\u00A0\u00A0\u00A0\u00A0Indented text\n\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0Double indented\n")

    # After all tests complete
    print("\n=== Test Summary ===")
    if failures:
        print(f"\n❌ {len(failures)} tests failed:")
        for failure in failures:
            print(f"\nTest: {failure['name']}")
            print(f"Input   : {repr(failure['input'])}")
            print(f"Expected: {repr(failure['expected'])}")
            print(f"Got     : {repr(failure['got'])}")
        print(f"\nTotal: {len(failures)} failed")
    else:
        print("\n✨ All tests passed successfully!")

def is_valid_url(url: str) -> bool:
    """
    Check if a given string is a valid URL.

    Args:
        url (str): The URL string to validate

    Returns:
        bool: True if the URL is valid, False otherwise
    """
    try:
        parsed = urllib.parse.urlparse(url)
        return bool(parsed.scheme) and bool(parsed.netloc)
    except ValueError:
        return False

# Run the tests
if __name__ == "__main__":
    test_md_to_slack()