import streamlit as st
from datetime import datetime
from typing import Optional, Dict
from data_loader import Channel
from collections import defaultdict
import re

def render_sidebar() -> None:
    """Render the sidebar with channel navigation and search"""
    workspace_data = st.session_state.workspace_data

    # Initialize conversation type if not set
    if "conversation_type" not in st.session_state:
        st.session_state.conversation_type = "channels"

    # Conversation type selector
    st.session_state.conversation_type = st.sidebar.radio(
        "Show conversations",
        options=["channels", "dms", "mpdms"],
        format_func=lambda x: {
            "channels": "💬 Channels",
            "dms": "👤 Direct Messages",
            "mpdms": "👥 Group Messages"
        }[x],
        horizontal=True
    )

    # Search box at the top with on_change callback
    search_label = {
        "channels": "Search channels",
        "dms": "Search direct messages",
        "mpdms": "Search group messages"
    }[st.session_state.conversation_type]

    st.sidebar.text_input(
        search_label,
        value=st.session_state.get("search_query", ""),
        key="search_query",
        placeholder=f"Filter {st.session_state.conversation_type}...",
        on_change=lambda: None  # This triggers rerun on input change
    )

    search_query = st.session_state.search_query.lower().strip()

    # Filter conversations based on type and search
    conversations: Dict[str, Channel] = {}

    if st.session_state.conversation_type == "channels":
        # Group channels by visibility
        public_channels = {
            cid: c for cid, c in workspace_data.channels.items()
            if not c.is_private and getattr(c, "type", "channel") == "channel"
            and (not search_query or search_query in c.name.lower())
        }
        private_channels = {
            cid: c for cid, c in workspace_data.channels.items()
            if c.is_private and getattr(c, "type", "channel") == "channel"
            and (not search_query or search_query in c.name.lower())
        }

        # Public channels section
        if public_channels:
            st.sidebar.markdown("### 📢 Public Channels")
            for channel_id, channel in sorted(public_channels.items(), key=lambda x: x[1].name):
                if st.sidebar.button(
                    f"# {channel.name}",
                    key=f"channel_{channel_id}",
                    use_container_width=True,
                ):
                    st.session_state.selected_channel = channel_id

        # Private channels section
        if private_channels:
            st.sidebar.markdown("### 🔒 Private Channels")
            for channel_id, channel in sorted(private_channels.items(), key=lambda x: x[1].name):
                if st.sidebar.button(
                    f"🔒 {channel.name}",
                    key=f"channel_{channel_id}",
                    use_container_width=True,
                ):
                    st.session_state.selected_channel = channel_id

    elif st.session_state.conversation_type == "dms":
        dms = {
            cid: c for cid, c in workspace_data.channels.items()
            if getattr(c, "type", "channel") == "dm"
            and (not search_query or search_query in (getattr(c, "display_name", "") or "").lower())
        }

        if dms:
            st.sidebar.markdown("### 👤 Direct Messages")
            for channel_id, channel in sorted(dms.items(), key=lambda x: x[1].display_name or ""):
                if st.sidebar.button(
                    channel.display_name or "Unknown User",
                    key=f"dm_{channel_id}",
                    use_container_width=True,
                ):
                    st.session_state.selected_channel = channel_id
        else:
            st.sidebar.info("No direct messages found")

    else:  # MPDMs
        mpdms = {
            cid: c for cid, c in workspace_data.channels.items()
            if getattr(c, "type", "channel") == "mpdm"
            and (not search_query or search_query in (getattr(c, "display_name", "") or "").lower())
        }

        if mpdms:
            st.sidebar.markdown("### 👥 Group Messages")
            for channel_id, channel in sorted(mpdms.items(), key=lambda x: x[1].display_name or ""):
                if st.sidebar.button(
                    channel.display_name or "Group Message",
                    key=f"mpdm_{channel_id}",
                    use_container_width=True,
                ):
                    st.session_state.selected_channel = channel_id
        else:
            st.sidebar.info("No group messages found")

def format_timestamp(ts: float) -> str:
    """Format a Unix timestamp into a readable date/time"""
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%Y-%m-%d %I:%M %p")

def parse_user_mentions(text: str, users_dict: dict) -> str:
    """
    Replace Slack-style user mentions (<@U123ABC>) with @RealName, falling back to @UserName.
    """
    pattern = re.compile(r"<@([A-Z0-9]+)(?:\|[^>]+)?>")
    def replacer(match):
        user_id = match.group(1)
        if user_id in users_dict:
            user = users_dict[user_id]
            # Prioritize real_name over user_name
            name = user.real_name or user.user_name or "UnknownUser"
            return f"@{name}"
        return "@UnknownUser"
    return pattern.sub(replacer, text)

def render_conversation() -> None:
    """Render the selected conversation/channel"""
    workspace_data = st.session_state.workspace_data
    channel_id = st.session_state.selected_channel

    if not channel_id or channel_id not in workspace_data.channels:
        st.error("Invalid conversation selected")
        return

    channel = workspace_data.channels[channel_id]
    messages = workspace_data.messages.get(channel_id, [])

    # Conversation header
    channel_type = getattr(channel, "type", "channel")
    if channel_type == "channel":
        title = f"{'🔒 ' if channel.is_private else '# '}{channel.name}"
    else:
        title = getattr(channel, "display_name", None) or "Conversation"
        icon = "👤" if channel_type == "dm" else "👥"
        title = f"{icon} {title}"

    st.markdown(f"### {title}")
    st.markdown(f"Created on {format_timestamp(channel.created.timestamp())}")
    st.markdown("---")

    # Group messages by threads
    messages_sorted = sorted(messages, key=lambda m: m.ts)
    parent_map = {}
    replies_map = defaultdict(list)

    for msg in messages_sorted:
        if not msg.thread_ts or msg.thread_ts == msg.ts:
            parent_map[msg.ts] = msg
        else:
            replies_map[msg.thread_ts].append(msg)

    # Build final message list with threaded replies
    final_message_list = []
    for ts_value in sorted(parent_map.keys()):
        parent_msg = parent_map[ts_value]
        final_message_list.append(parent_msg)

        if ts_value in replies_map:
            child_replies = sorted(replies_map[ts_value], key=lambda r: r.ts)
            final_message_list.extend(child_replies)

    # Render messages with thread context
    for msg in final_message_list:
        user = workspace_data.users.get(msg.user)
        user_name = user.real_name or user.user_name if user else "Unknown User"

        threaded_note = ""
        if msg.thread_ts and msg.thread_ts != msg.ts:
            parent_msg = parent_map.get(msg.thread_ts)
            if parent_msg:
                parent_user = workspace_data.users.get(parent_msg.user)
                parent_user_name = parent_user.real_name or parent_user.user_name if parent_user else "Unknown User"
                parent_time = format_timestamp(parent_msg.ts)
                threaded_note = f" (Threaded reply to {parent_user_name} - {parent_time})"

        st.markdown(f"**{user_name}** - {format_timestamp(msg.ts)}{threaded_note}")
        # Transform Slack user mentions in the text
        rendered_text = parse_user_mentions(msg.text, workspace_data.users)
        st.text(rendered_text)

        if msg.attachments:
            st.markdown("📎 **Attachments:**")
            for attachment in msg.attachments:
                st.markdown(f"- {attachment.get('name', 'Unnamed attachment')}")

        st.markdown("---")