import pytest
from components.dynamic_context_component import extract_smart_name

# Run with:
# python -m pytest scripts/test_extract_smart_name.py -v

@pytest.mark.parametrize("test_input,expected", [
    # Invalid inputs
    ("Some random text", None),
    ("", None),

    # File paths
    ("CONTEXT: /path/to/my/file.txt", "file.txt"),
    ("CONTEXT: C:\\Users\\Documents\\report.pdf", "report.pdf"),

    # URLs
    ("CONTEXT: https://example.com/page", "page"),
    ("CONTEXT: https://example.com", "example.com"),
    ("CONTEXT: http://subdomain.example.com/path/doc.html", "doc.html"),

    # First few words
    ("CONTEXT: This is a test", "This is a..."),
    ("CONTEXT: Short text", "Short text"),
    ("CONTEXT: A very long description of something", "A very long..."),

    # Edge cases
    ("CONTEXT:", None),
    ("CONTEXT: 🔴", "🔴"),
    ("CONTEXT: /path/with/no/extension/", ""),
    ("CONTEXT: ", None),
    ("Not a context", None),
    ("CONTEXT: /path/", ""),  # Empty filename
])
def test_extract_smart_name(test_input, expected):
    assert extract_smart_name(test_input) == expected

# def test_malformed_url():
#     """Test that malformed URLs fall back to word extraction"""
#     result = extract_smart_name("CONTEXT: http:// malformed url")
#     assert result == "http:// malformed url..."
