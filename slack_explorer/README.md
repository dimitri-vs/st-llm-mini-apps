# Slack Data Explorer

A Streamlit app for exploring Slack workspace exports locally. View channels, messages, and attachments in a clean, minimal interface.

## Features
- Browse public and private channels
- Search/filter channels by name
- View chronological messages with user info and timestamps
- See attachment names (files shared in conversations)
- Local-only operation (no cloud/external dependencies)

## Usage

1. Export your Slack data (see below)
2. Extract the zip contents to the `exported/` directory
3. Run the app:
   ```bash
   streamlit run app.py
   ```

## Export Data

Export URL: https://ecomanalyticsco.slack.com/services/export

1. Export your Slack data (creates a zip file)
2. Extract the zip contents to the `exported/` directory in this project


## Exported Data Structure

The export contains several types of folders:

```
├── channel_name/           # Public/private channel messages
│   ├── canvas_in_the_conversation.json    # Canvas data
│   ├── yyyy-mm-dd.json    # Daily message logs
│   ├── yyyy-mm-dd.json
│   └── ...
├── mpdm-user1-user2-user3/  # Multi-person direct messages
│   └── yyyy-mm-dd.json
├── Dxxxxxxxx/             # Direct messages (DMs) between two users
│   └── yyyy-mm-dd.json
├── Fxxxxxxxx:xxxxxxxxx/     # Slack Canvas (new feature)
│   └── yyyy-mm-dd.json
├── users.json              # User information and profiles
├── groups.json            # Private channel information
├── channels.json          # Public channel information
└── ...more JSON files... (see below)
```

### Folder Types

See: https://slack.com/help/articles/220556107-How-to-read-Slack-data-exports

All folders contain seem to contain daily JSON files with messages (e.g., `2024-01-03.json`)
Only dates with messages will have corresponding JSON files
If a conversation cotnains a canvas, it will also contain a `canvas_in_the_conversation.json` file.

1. **Channels**: Named folders containing daily JSON files with messages
   - Directory name format: `{channel_name}` (e.g., `general`, `random`)
   - Each JSON file contains messages and metadata for that specific date
   - Only dates with messages will have corresponding JSON files
   - Can include both public and private channels

2. **Direct Messages (DMs)**: One-on-one conversation folders
   - Directory name format: `D` followed by ID (e.g., `D066318NDTM`, `D088HKPH9PA`)
   - Metadata found in `dms.json`

3. **Multi-Person Direct Messages (MPDM)**: Group conversation folders
   - Directory name format: `mpdm-[username1]--[username2]--[username3]-{id}`
   - Eg. `mpdm-dimitri--jana--pawan-1`, `mpdm-clayton.bell--luis--kareem-1`
   - Contains group conversations between 3+ people
   - Only present in full exports

4. **Canvas Folders**: Two types of canvas-related folders
   - Directory name format: `FC_Fxxxxxxxx_{name}` or `FC_Fxxxxxxxx_Untitled`
   - e.g., `FC_F088HKPH9PA_Untitled`, `FC_F0877TYJMGS_Zaks Brainstorming Space`
   - Canvas data can be downloaded via URLs in the JSON files

5. **Reference Files**: Special JSON files containing metadata
   - `users.json`: User information and IDs
   - `channels.json`: Information about public channels
   - `groups.json`: Information about private channels
   - `dms.json`: Information about direct messages
   - `mpims.json`: Group direct message information
   - `canvases.json`: Canvas data and download URLs
   - `integration_logs.json`: App activity logs (loom, google calendar, etc.)

Note: Folders will only be included in the export if there are messages present for the selected date range and if your export permissions include that type of conversation.

## Identifying Conversations and Users

### Users
- Users are identified by their IDs, which start with a U in @ mentions ("Hey <@U086ZR6K123> - I just sent...")
- User metadata (name, email, etc.) can be found in `users.json` ("id":"U086ZR6K123", ... "real_name":"David Anderson")

### Channels
- As an Admin, public and private channels are easily identifiable by their folder names in the export directory
- Channel metadata (creation date, members, etc.) can be found in `groups.json` and `channels.json`

Partial channel excerpt from `groups.json`:
```json
{
    "id": "C086N3ANL5D",
    "name": "ecom-opsec-intel-chris",
    "created": 1735828689,
    "creator": "U01PYFFRV1Q",
    "is_archived": false,
    "members": [
        "U01PYFFRV1Q",
        "U027QNGNAG5",
        "U03BQ7VAG56",
        "U086ZR6K7BP"
    ],
    ...
}
```

### Direct Messages & Multi-Person DMs
The best methods to locate specific conversations:

1. **Using Reference Files**:
   - Check `groups.json` or `dms.json` to map channel IDs to names
   - Look up member IDs (starting with 'U') in `users.json`

2. **Text Search (Recommended)**:
   - Find a unique, plain-text segment (around 10 words) from the conversation
   - Use VS Code/Cursor's global search
   - Important: Disable "use exclude settings" and "ignore files" options
   - Works best for DMs, MPDMs, and Canvas content

