import streamlit.components.v1 as components

def show_copy_button(text: str) -> None:
    """
    Renders a styled button that copies the provided text to clipboard when clicked.
    This implementation uses inline HTML and JavaScript to create a custom, more compact button
    that integrates better with the Streamlit UI.

    Args:
        text: The text content to be copied to clipboard

    Example:
        sample_content = "This is some text that will be copied"
        show_copy_button(sample_content)
    """
    # Escape backticks in content for safe injection into the JS template
    # safe_text = text.replace("`", "\\`").replace("${", "\\${")
    # TODO: this seems to strip slashes in file paths and new lines mayber try json.dumps(text) approach again?


    # TODO: make the on-hover text and border color dynamic like native streamlit buttons
    html_code = f"""
    <div style="
        display: flex;
        justify-content: start;
        height: 100%;
        margin-top: -0.5rem;">
      <button id="copyButton"
        style="
          display: inline-flex;
          align-items: center;
          justify-content: center;
          appearance: button;
          background-color: rgb(128, 128, 128);
          border: 0.8px solid rgba(128, 128, 128, 0.2);
          border-radius: 8px;
          color: rgb(250, 250, 250);
          cursor: pointer;
          font-family: 'Source Sans Pro', sans-serif;
          font-size: 16px;
          font-weight: 400;
          height: 40px;
          line-height: 25.6px;
          padding: 4px 12px;
          width: 133px;
          white-space: nowrap;
          -webkit-font-smoothing: auto;
          -webkit-tap-highlight-color: rgba(0, 0, 0, 0);
          transition: background-color 0.3s ease;">
        <div data-testid="stMarkdownContainer">
          <p style="margin: 0;">📋 Copy</p>
        </div>
      </button>
    </div>
    <script>
      // NOTE: The current approach strictly relies on the system's dark mode preference for theming.
      // All native and non-native theme detection approaches as of 2025-02-04 are unsupported and will not work properly.
      const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

      // Uncomment the following line to simulate light mode during testing:
      // const isDark = false;

      const button = document.getElementById("copyButton");

      // Define a functional approach to apply theme-based styles
      const applyTheme = (darkMode) => {{
          if (darkMode) {{
              button.style.backgroundColor = "rgb(19, 23, 32)";
              button.style.color = "rgb(250, 250, 250)";
              button.style.border = "0.8px solid rgba(250, 250, 250, 0.2)";
          }} else {{
              button.style.backgroundColor = "rgb(240, 242, 246)";
              button.style.color = "rgb(49, 51, 63)";
              button.style.border = "0.8px solid rgba(49, 51, 63, 0.2)";
          }}
      }};

      // Set initial theme based on system mode
      applyTheme(isDark);

      // Add the copy button click handler using a functional pattern
      button.addEventListener("click", function() {{
          navigator.clipboard.writeText(`{text}`);

          // Visual feedback: Add success border
          const originalBorder = button.style.border;
          button.style.border = "2px solid rgb(45, 164, 78)";
          button.style.transition = "border 0.1s ease";

          // Reset border after delay
          setTimeout(() => {{
              button.style.border = originalBorder;
          }}, 200);
      }});

      // Listen for changes in the system theme preference and update styles dynamically
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {{
          applyTheme(e.matches);
      }});
    </script>
    """
    components.html(html_code, height=70)