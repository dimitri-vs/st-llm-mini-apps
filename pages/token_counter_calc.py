import streamlit as st
import tiktoken
import re
from dotenv import load_dotenv
import anthropic
import time

load_dotenv()

st.set_page_config(
    page_title="llm-token-calculator",
    page_icon="🧮",
    layout="wide"  # "centered" constrains page content to a fixed width; "wide" uses the entire screen
)

st.title("🧮 LLM Token Calculator")

def num_tokens_from_string(string: str, model_name: str) -> int:
    """
    Returns the number of tokens in a text string for a given model.
    For OpenAI models, uses tiktoken.
    For Anthropic models, uses their token counting endpoint.
    """
    # Handle empty strings
    if not string.strip():
        return 0

    # Handle Anthropic models
    if model_name.startswith('claude-'):
        try:
            # Add small delay between API calls (0.6s = max 100 requests/minute)
            time.sleep(0.6)
            client = anthropic.Anthropic()
            response = client.messages.count_tokens(
                model=model_name,
                messages=[{
                    "role": "user",
                    "content": [{"type": "text", "text": string}]
                }]
            )
            return response.input_tokens
        except Exception as e:
            st.error(f"Error counting tokens for Anthropic model: {e}")
            # Fallback to tiktoken cl100k_base as approximate estimation
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(string))

    # For all other models, use tiktoken
    encoding = tiktoken.encoding_for_model(model_name)
    return len(encoding.encode(string))


def analyze_string(s):
    # Number of characters (excluding spaces)
    num_characters = len(s.replace(' ', ''))
    # Number of words
    words = s.split()
    num_words = len(words)
    # Number of proper sentences
    # This uses a regular expression to count occurrences of patterns that typically end sentences: . ! ?
    # Note that this will not work for text that contains non-standard sentence endings
    num_sentences = len(re.findall(r"[.!?]", s))
    return num_characters, num_words, num_sentences

def calculate_cost(model_name, in_tokens, out_tokens):
    if model_name not in MODEL_CONFIG:
        raise ValueError("Unknown model name")
    input_cost_per_token, output_cost_per_token = MODEL_CONFIG[model_name]['pricing']
    total_request_cost = in_tokens * input_cost_per_token + out_tokens * output_cost_per_token
    return total_request_cost

MODEL_CONFIG = {
    # pricing format is like this: (input_cost_per_token, output_cost_per_token),

    # ======================= Anthropic pricing =======================

    'claude-3-5-sonnet-latest': {'max_tokens': 200000, 'pricing': (3 / 1000000, 15 / 1000000)},
    'claude-3-5-haiku-latest': {'max_tokens': 200000, 'pricing': (0.80 / 1000000, 4 / 1000000)},
    'claude-3-opus-latest': {'max_tokens': 200000, 'pricing': (15 / 1000000, 75 / 1000000)},

    # ======================= OpenAI pricing =======================

    # OpenAI GPT-4o models
    'gpt-4o': {'max_tokens': 128000, 'pricing': (2.50 / 1000000, 10.00 / 1000000)},
    'gpt-4o-2024-11-20': {'max_tokens': 128000, 'pricing': (2.50 / 1000000, 10.00 / 1000000)},

    # OpenAI GPT-4o mini models
    'gpt-4o-mini': {'max_tokens': 128000, 'pricing': (0.150 / 1000000, 0.600 / 1000000)},
    'gpt-4o-mini-2024-07-18': {'max_tokens': 128000, 'pricing': (0.150 / 1000000, 0.600 / 1000000)},

    # OpenAI o1 models
    'o1': {'max_tokens': 200000, 'pricing': (15.00 / 1000000, 60.00 / 1000000)},
    'o1-2024-12-17': {'max_tokens': 200000, 'pricing': (15.00 / 1000000, 60.00 / 1000000)},
    'o1-preview': {'max_tokens': 128000, 'pricing': (15.00 / 1000000, 60.00 / 1000000)},
    'o1-preview-2024-09-12': {'max_tokens': 128000, 'pricing': (15.00 / 1000000, 60.00 / 1000000)},

    # OpenAI o1-mini models
    'o1-mini': {'max_tokens': 128000, 'pricing': (3.00 / 1000000, 12.00 / 1000000)},
    'o1-mini-2024-09-12': {'max_tokens': 128000, 'pricing': (3.00 / 1000000, 12.00 / 1000000)},

    # OpenAI embedding models
    'text-embedding-3-small': {'max_tokens': 8191, 'pricing': (0.020 / 1000000, 0)},
    'text-embedding-3-large': {'max_tokens': 8191, 'pricing': (0.130 / 1000000, 0)},
    'text-embedding-ada-002': {'max_tokens': 8191, 'pricing': (0.100 / 1000000, 0)},
}

st.write("Pricing last updated: `2025-01-22`")
st.write("Calculates the number of tokens and estimated cost for a given input/output text and LLM model.")
with st.expander("Sources"):
    st.markdown('''
    - https://openai.com/api/pricing/
    - https://platform.openai.com/docs/models # for token limits
    - https://www.anthropic.com/pricing#anthropic-api

    NOTE: Use this prompt to update pricing:
    """
    Looking at the provided website: @anthropic_pricing.md

    Please update the MODEL_CONFIG for Anthropic models, adding any new models found on the website to MODEL_CONFIG.
    """
    ''')

def display_total_section(input_tokens: int, out_tokens: int, model_name: str):
    """Helper function to display total tokens and cost calculations"""
    model_max_tokens = MODEL_CONFIG[model_name]['max_tokens']
    total_cost = calculate_cost(model_name, input_tokens, out_tokens)
    st.write(f":orange[**Total Request Cost:**] ${total_cost:,.4f}")
    total_tokens = input_tokens + out_tokens
    percentage = total_tokens / model_max_tokens * 100
    if percentage > 100:
        st.markdown(f"**{total_tokens}** request tokens (**:red[{percentage:.0f}%]** of {model_max_tokens} max)")
        st.write(":red[**Warning:**] This request will exceed the maximum number of tokens allowed for this model.")
    else:
        st.write(f"**{total_tokens}** request tokens ({percentage:.0f}% of {model_max_tokens} max)")

# Create tabs
tab1, tab2 = st.tabs(["Text to Tokens", "Words to Tokens"])

with tab1:
    llm_model = st.selectbox("LLM Model", tuple(MODEL_CONFIG.keys()), key="text_model")

    st.subheader("Input Tokens")
    input_text = st.text_area("Sys + User Text", height=350)

    if llm_model.startswith('claude-'):
        in_tokens = num_tokens_from_string(input_text, llm_model)
    elif llm_model in ['ft:gpt-3.5-turbo']:
        # hacky way to accommodate finetuned models
        in_tokens = num_tokens_from_string(input_text, 'gpt-3.5-turbo')
    else:
        in_tokens = num_tokens_from_string(input_text, llm_model)

    # calculate string stats
    char_count, word_count, sentence_count = analyze_string(input_text)
    st.write(f"Characters: {char_count} || Words: {word_count} || Proper Sentences: {sentence_count}")

    # calculate tokens
    model_max_tokens = MODEL_CONFIG[llm_model]['max_tokens']
    in_cost = calculate_cost(llm_model, in_tokens, out_tokens=0)
    st.write(f"**{in_tokens}** request tokens ({in_tokens / model_max_tokens * 100:.0f}% of {model_max_tokens} max) || **Cost:** ${in_cost:,.4f}")

    st.subheader("Output Tokens")
    out_tokens = st.number_input("Plus Estimated Response Tokens", value=800, key="text_out_tokens")

    st.divider()
    st.subheader("Total")
    display_total_section(in_tokens, out_tokens, llm_model)

with tab2:
    llm_model_words = st.selectbox("LLM Model", tuple(MODEL_CONFIG.keys()), key="words_model")

    st.subheader("Input Words")
    word_count_input = st.number_input("Number of Words", min_value=0, value=100)

    # Estimate tokens (rough approximation: 1 word ≈ 1.3 tokens)
    estimated_tokens = int(word_count_input * 1.3)

    model_max_tokens = MODEL_CONFIG[llm_model_words]['max_tokens']
    in_cost = calculate_cost(llm_model_words, estimated_tokens, out_tokens=0)
    st.write(f"**Estimated {estimated_tokens}** request tokens ({estimated_tokens / model_max_tokens * 100:.0f}% of {model_max_tokens} max) || **Cost:** ${in_cost:,.4f}")

    st.subheader("Output Tokens")
    out_tokens = st.number_input("Plus Estimated Response Tokens", value=800, key="words_out_tokens")

    st.divider()
    st.subheader("Total")
    display_total_section(estimated_tokens, out_tokens, llm_model_words)


