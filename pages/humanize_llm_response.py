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
        '“': '"',  # Left double quotation mark U+201C
        '”': '"',  # Right double quotation mark U+201D
        '‘': "'",  # Left single quotation mark U+2018
        '’': "'",  # Right single quotation mark U+2019
        '—': '-',  # Em dash U+2014
        '–': '-',  # En dash U+2013
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

    st.markdown("""
    > BEFORE: “This response—replete with smart quotes, Oxford commas, and meticulous abbreviations (e.g., “this” and “that”)—is unmistakably the handiwork of ChatGPT.”
    >
    > AFTER: “This response-replete with smart quotes, Oxford commas, and meticulous abbreviations (eg. "this" and "that")-is unmistakably the handiwork of ChatGPT.”
    """)

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

        # Render the cleaned text as markdown in its own container
        st.markdown("Rendered preview:")
        render_container = st.container(border=True)
        with render_container:
            st.markdown(cleaned_text)

if __name__ == "__main__":
    main()
