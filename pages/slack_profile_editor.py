import streamlit as st
import os
import json
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load environment variables
load_dotenv(override=True)

# --- Constants and Configuration ---
# NOTE: Token needs 'users.profile:write' (to update) and 'users.profile:read' (to fetch fields).
# Token user's role must be higher than the target user's role.
SLACK_USER_TOKEN = os.environ.get("SLACK_ADMIN_TOOLS_USER_TOKEN")

# --- Initialize Session State ---
# Use setdefault for cleaner initialization
st.session_state.setdefault('field_definitions', None)
st.session_state.setdefault('selected_indices', [])
st.session_state.setdefault('field_inputs', {}) # {field_id: {'value': '', 'alt': ''}}
st.session_state.setdefault('target_user_info', None)

# --- Core Slack Functions ---

def fetch_custom_field_definitions(client: WebClient) -> list:
    """Fetches custom profile field definitions (requires 'users.profile:read')."""
    response = client.team_profile_get(visibility="all")
    return response.get("profile", {}).get("fields", [])

def fetch_user_info(client: WebClient, user_id: str) -> dict:
    """Fetches user information (requires 'users:read')."""
    response = client.users_info(user=user_id)
    return response.get("user")

def update_user_profile(client: WebClient, user_id: str, profile_data: dict) -> dict:
    """Updates user profile (requires 'users.profile:write')."""
    response = client.users_profile_set(user=user_id, profile=profile_data)
    return response

# --- Streamlit UI ---

st.set_page_config(layout="wide")
st.title("Slack User Profile Editor")

with st.expander("Important Information & How-To"):
    # Keep the expander content for now, but remove the extensive curl example
    st.markdown(f"""
    ### How-To

    1) Get the user's ID by clicking on their profile picture in chat, then clicking the three dots menu (ellipsis) and selecting "Copy Member ID".

    2) Modify and run this prompt template in an LLM to get phonetic spelling:
    ```
    Can you give me the English phonetic spelling of "FIRST_NAME🔴" from CITY_AND_COUNTRY_NAME🔴?

    In this format: "(pronounced {{pronunciation_NA}} or {{pronunciation}} - ____ as in ___)" (eg. "(pronounced '...')"). For pronunciation_NA use the common "North American" pronunciation and for pronunciation use the slightly more native variant. If there really is only one pronunciation, just use that. For the `____ as in ___` part include a example of a part of the name that might be hard for one to distinguish how to say in the phonetic spelling (eg. for João: " 'zh' as in 'beige'") only that no other commentary, few words max. Finally, include around two sentences on your reasoning.
    ```

    3) To get the Timezone code, use https://apidocs.geoapify.com/playground/geocoding to search and get the timezone > name (eg. "America/New_York")

    4) To get the Compare Time Zones link, search "worldtimebuddy {{CITY_COUNTRY_NAME}}" on Google and copy the link (eg. "https://www.worldtimebuddy.com/united-states-pennsylvania-philadelphia"). Make the Alt text a shorter version: worldtimebuddy.com/united-states-pennsylvania
    """)

with st.expander("Auth, Permissions, & Custom Field IDs"):
    st.markdown("""
    ### Authentication & Permissions
    - **Token:** Uses `SLACK_ADMIN_TOOLS_USER_TOKEN` from `.env`.
    - **Scopes:** `users.profile:write` (update), `users.profile:read` (fetch fields), `users:read` (show user name). Ensure token has these scopes.
    - **Role Hierarchy:** Token user must have a higher role than the target user.

    ### Finding Custom Field IDs (`Xf...`)
    - **Use the 'Fetch Custom Field IDs' button.** This uses the `team.profile.get` API (requires `users.profile:read`).
    - IDs starting with `Xf` are custom fields. SCIM-managed fields (`"is_scim": true`) usually cannot be updated via this API.

    ### Payload Structure
    - Updates are sent like: `{{"user": "U...", "profile": {{"fields": {{"Xf...": {{"value": "...", "alt": ""}}}}}}}}`
    - `"alt"` is usually empty. Ensure `value` matches field type (text, date `YYYY-MM-DD`, link `http://...`).
    """)

# Check for token and initialize client
if not SLACK_USER_TOKEN:
    st.error("`SLACK_ADMIN_TOOLS_USER_TOKEN` environment variable not set in `.env`.")
    st.info("Token requires `users.profile:write`, `users.profile:read`, and potentially `users:read` scopes.")
    st.stop()

# Initialize client - subsequent API calls will fail if token is invalid
slack_client = WebClient(token=SLACK_USER_TOKEN)

# --- User Input Area ---
st.header("Target User and Profile Fields")

target_user_id = st.text_input(
    "Target User ID",
    help="Enter the Slack User ID (e.g., U12345678)."
)

# --- Display User Info ---
if target_user_id:
    # Fetch user info directly if ID is provided
    # Let Streamlit handle potential SlackApiError
    user_info = fetch_user_info(slack_client, target_user_id)
    st.session_state.target_user_info = user_info # Store for potential reuse if needed
    real_name = user_info.get("real_name", "N/A")
    display_name = user_info.get("profile", {}).get("display_name", "N/A")
    st.caption(f"**Target:** {real_name} ({display_name})")
else:
    # Clear info if ID is removed
    st.session_state.target_user_info = None

# --- Field Definitions ---
st.subheader("Select Fields to Edit")

if st.button("Fetch Custom Field IDs", help="Requires 'users.profile:read' scope."):
    with st.spinner("Fetching custom field definitions..."):
        # Let Streamlit handle potential SlackApiError
        fetched_definitions = fetch_custom_field_definitions(slack_client)
        st.session_state.field_definitions = fetched_definitions
        st.success(f"Fetched {len(fetched_definitions)} definitions.")
        # Clear selections if definitions are re-fetched
        st.session_state.selected_indices = []
        st.session_state.field_inputs = {}

# --- Display Field Definitions Table ---
display_fields = []
if st.session_state.field_definitions is not None:
    for field in st.session_state.field_definitions:
        # Filter out SCIM fields (API write permission is usually false)
        if field.get("permissions", {}).get("api"):
            display_fields.append({
                "label": field.get("label", "N/A"),
                "id": field.get("id", "N/A"),
                "type": field.get("type", "N/A"),
                "hint": field.get("hint", "")
            })

    if display_fields:
        st.caption("Select rows to choose fields for editing.")
        event = st.dataframe(
            display_fields,
            use_container_width=True,
            key="field_selector_df",
            on_select="rerun",
            selection_mode="multi-row"
        )
        st.session_state.selected_indices = event.selection.rows
    else:
        st.info("No editable (non-SCIM) custom fields found or fetch returned empty.")
else:
    st.caption("Click 'Fetch Custom Field IDs' to load available fields.")


# --- Dynamic Input Area for Selected Fields ---
st.subheader("Edit Selected Field Values")
st.caption("Note: The 'Alt/Label Text' field often sets the display text for link fields.")

if not st.session_state.selected_indices:
    st.caption("Select fields from the table above to edit their values.")
else:
    # Headers
    col_label, col_id, col_type, col_value, col_alt = st.columns([1.5, 1, 0.5, 2, 2])
    col_label.markdown("**Label**")
    col_id.markdown("**Field ID**")
    col_type.markdown("**Type**")
    col_value.markdown("**Value**")
    col_alt.markdown("**Alt/Label Text** (Optional)")

    # Store fields actually being edited in this run
    editable_fields_metadata = []

    for index in st.session_state.selected_indices:
        if index < len(display_fields): # Check index validity
            selected_field = display_fields[index]
            field_id = selected_field['id']
            field_label = selected_field['label']
            field_type = selected_field['type']
            editable_fields_metadata.append(selected_field) # Track metadata

            # Ensure input state exists
            st.session_state.field_inputs.setdefault(field_id, {'value': '', 'alt': ''})

            # Input Row
            col_l, col_i, col_t, col_v, col_a = st.columns([1.5, 1, 0.5, 2, 2])
            col_l.text(field_label)
            col_i.text(field_id)
            col_t.text(field_type)

            # Get current state for inputs
            current_value = st.session_state.field_inputs[field_id]['value']
            current_alt = st.session_state.field_inputs[field_id]['alt']

            # Value Input
            input_help = selected_field.get("hint", "")
            if field_type == 'date': input_help += " (YYYY-MM-DD)"
            elif field_type == 'link': input_help += " (http://...)"

            new_value = col_v.text_input(
                f"Value_{field_id}", # Use field ID in key for uniqueness
                value=current_value,
                key=f"value_{field_id}",
                label_visibility="collapsed",
                help=input_help if input_help else None
            )
            # Update state directly if changed (avoids complex callbacks)
            if new_value != current_value:
                st.session_state.field_inputs[field_id]['value'] = new_value
                # No rerun needed here, handled by button press

            # Alt Input
            new_alt = col_a.text_input(
                f"Alt_{field_id}", # Use field ID in key
                value=current_alt,
                key=f"alt_{field_id}",
                label_visibility="collapsed",
                placeholder="Link display text"
            )
            if new_alt != current_alt:
                st.session_state.field_inputs[field_id]['alt'] = new_alt

# --- Update Action ---
update_button = st.button(
    "Update Profile",
    type="primary",
    disabled=not st.session_state.selected_indices, # Disable if no rows selected
    help="Requires 'users.profile:write' scope. Select fields first."
)

if update_button:
    if not target_user_id:
        st.warning("Please enter a Target User ID.")
    # Check if editable_fields_metadata is populated (means rows were selected and processed)
    elif 'editable_fields_metadata' not in locals() or not editable_fields_metadata:
         st.warning("No fields selected or processed for update. Please select from table.")
    else:
        profile_fields = {}
        has_value_to_update = False
        for field_meta in editable_fields_metadata:
            field_id = field_meta['id']
            # Get the latest value from the input state
            value = st.session_state.field_inputs[field_id]['value']
            alt = st.session_state.field_inputs[field_id]['alt']

            # Only include fields where a value was actually entered
            if value:
                profile_fields[field_id] = {"value": value, "alt": alt}
                has_value_to_update = True
            # Basic check - though filtering should prevent non-Xf IDs
            if not field_id.startswith("Xf"):
                 st.warning(f"Selected Field ID '{field_id}' ('{field_meta['label']}') may not be a custom field.")

        if not has_value_to_update:
            st.warning("Please enter a value for at least one selected field.")
        else:
            profile_payload = {"fields": profile_fields}
            st.info("Sending update payload (check terminal/browser console for details if needed):")
            st.json(profile_payload) # Show payload in UI

            with st.spinner(f"Updating profile for {target_user_id}..."):
                # Let Streamlit handle potential SlackApiError or other exceptions
                response = update_user_profile(slack_client, target_user_id, profile_payload)

                if response.get("ok"):
                    st.success(f"Successfully updated profile for user {target_user_id}!")
                    st.write("Updated profile data snippet from response:")
                    st.json(response.get("profile", {}))
                else:
                    # Error details might be in response.data even if ok is false
                    error_msg = response.get('error', 'Unknown error')
                    st.error(f"Slack API Error: {error_msg}")
                    st.warning("Check the full API response details if the error isn't clear.")
                    # No need for explicit print, error should propagate if needed
