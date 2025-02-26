import streamlit as st

def setup_page():
    st.set_page_config(
        page_title="Humanize LLM Response",
        page_icon="🤖",
        layout="wide"
    )
    st.title("Humanize LLM Response")

def replace_typography_marks(text: str) -> str:
    # Typography marks replacements
    replacements = {
        '"': '"',  # Fancy double quotes to regular
        '"': '"',
        ''': "'",  # Fancy single quotes to regular
        ''': "'",
        '—': '-',  # Em dash to regular dash
        '–': '-',  # En dash to regular dash
    }

    # Latin abbreviation simplifications
    latin_abbrev = {
        'e.g.,': 'eg.',
        'i.e.,': 'ie.',
        'etc.)': 'etc)',
        'etc.,': 'etc.'
    }

    # First replace typography marks
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Then simplify Latin abbreviations
    for old, new in latin_abbrev.items():
        text = text.replace(old, new)

    return text

def main():
    setup_page()

    input_text = st.text_area(
        "Paste LLM response here:",
        height=300,
        help="Paste text containing fancy typography marks to convert them to plain ASCII characters"
    )

    if input_text:
        cleaned_text = replace_typography_marks(input_text)
        st.text_area(
            "Cleaned text:",
            value=cleaned_text,
            height=300,
            disabled=True
        )

if __name__ == "__main__":
    main()
