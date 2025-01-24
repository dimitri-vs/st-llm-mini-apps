from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Optional, Set

@dataclass
class User:
    id: str # "U01PYFFRV1Q"
    user_name: str # "dimitri_01"
    real_name: Optional[str] = None # "Dimitri Sudomoin"
    avatar_url: Optional[str] = None # "https://avatars.slack-edge.com/..."
    avatar_hash: Optional[str] = None # "7792edda081a"

@dataclass
class Channel:
    # This will be used to represent channels, groups, dms, and mpdms
    # TODO: maybe rename to `Conversation`?
    id: str  # "C0287UMPB5M", "D066318NDTM"
    name: str  # "clockify-reminder", "dm-dimitri--clayton.bell-1"
    is_private: bool  # kind of useless as 99% of channels and conversations are private
    created: datetime
    members: Set[str]  # ["U01PYFFRV1Q", "U027QNGNAG5", ...]
    creator: Optional[str] = None  # "U01PYFFRV1Q", None if dm
    is_archived: Optional[bool] = None  # None if dm
    type: str = "channel"  # or "dm" or "mpdm"
    display_name: Optional[str] = None  # Human-readable name as shown in Slack UI:
                                       # - Channels: "#general"
                                       # - DMs: "John Smith"
                                       # - MPDMs: "John Smith, Jane Doe, Bob Wilson"

@dataclass
class Message:
    user: str
    text: str
    ts: float
    attachments: List[Dict]
    thread_ts: Optional[float] = None

@dataclass
class WorkspaceData:
    users: Dict[str, User]
    channels: Dict[str, Channel]
    messages: Dict[str, List[Message]]  # channel_id -> messages

def parse_timestamp(ts: str) -> float:
    """Convert Slack timestamp to float for easier sorting/comparison"""
    # return float(ts.split(".")[0])
    return float(ts) # Trying out keeping fractional part to better sort simultaneous messages

def load_workspace_data(export_path: str) -> WorkspaceData:
    """Load and parse all workspace data from the export directory"""
    export_dir = Path(export_path)

    # Load users
    users = {}
    with open(export_dir / "users.json", "r", encoding="utf-8") as f:
        users_data = json.load(f)
        for user in users_data:
            users[user["id"]] = User(
                id=user["id"],
                user_name=user["name"],
                real_name=user.get("real_name_normalized"),
                avatar_url=user.get("image_32"), # also avail: "image_48", "image_72", etc.
                avatar_hash=user.get("avatar_hash"),
            )

    # Load channels (both public and private)
    channels = {}

    # Public channels?
    # NOTE: channels.json seems to be empty in the export, keeping this for reference
    # with open(export_dir / "channels.json", "r", encoding="utf-8") as f:
    #     channels_data = json.load(f)
    #     for channel in channels_data:
    #         channels[channel["id"]] = Channel(
    #             id=channel["id"],
    #             name=channel["name"],
    #             is_private=False,
    #             created=datetime.fromtimestamp(channel["created"]),
    #             creator=channel.get("creator"),
    #             is_archived=channel.get("is_archived", False),
    #             members=set(channel.get("members", [])),
    #             type="channel"
    #         )

    # Private channels
    try:
        with open(export_dir / "groups.json", "r", encoding="utf-8") as f:
            groups_data = json.load(f)
            for group in groups_data:
                channels[group["id"]] = Channel(
                    id=group["id"],
                    name=group["name"],
                    is_private=True, # All channels in groups.json are private?
                    created=datetime.fromtimestamp(group["created"]),
                    creator=group.get("creator"),
                    is_archived=group.get("is_archived", False),
                    members=set(group.get("members", [])),
                    type="channel",
                    display_name=f"#{group['name']}"
                )
    except FileNotFoundError:
        pass  # No private channels in export

    # Load DMs
    try:
        with open(export_dir / "dms.json", "r", encoding="utf-8") as f:
            dms_data = json.load(f)
            for dm in dms_data:
                members = set(dm.get("members", []))
                if len(members) != 2:  # DMs should have exactly 2 members
                    continue

                # Get member names for the DM channel name
                member_names = [
                    users[uid].user_name
                    for uid in members if uid in users
                ]

                # Create display name from both users' real names or usernames
                display_names = [
                    users[uid].real_name or users[uid].user_name
                    for uid in members if uid in users
                ]
                display_name = " & ".join(sorted(display_names))

                channels[dm["id"]] = Channel(
                    id=dm["id"],
                    name=f"dm-{'--'.join(sorted(member_names))}-{dm['id']}", # Internal name with usernames
                    is_private=True,
                    created=datetime.fromtimestamp(dm["created"]),
                    members=members,
                    type="dm",
                    display_name=display_name
                )
    except FileNotFoundError:
        pass  # No DMs in export

    # Load MPDMs
    try:
        with open(export_dir / "mpims.json", "r", encoding="utf-8") as f:
            mpdms_data = json.load(f)
            for mpdm in mpdms_data:
                members = set(mpdm.get("members", []))
                if len(members) <= 2:  # MPDMs should have more than 2 members
                    continue

                # Create display name from member names
                member_names = [
                    users[uid].real_name or users[uid].user_name
                    for uid in members if uid in users
                ]
                display_name = ", ".join(sorted(member_names))

                channels[mpdm["id"]] = Channel(
                    id=mpdm["id"],
                    name=mpdm["name"],
                    is_private=True,
                    created=datetime.fromtimestamp(mpdm["created"]),
                    members=members,
                    type="mpdm",
                    display_name=display_name
                )
    except FileNotFoundError:
        pass  # No MPDMs in export

    # Load messages for each channel/DM/MPDM
    # TODO: probably should pull this out into a separate function
    # load all the data into memory or session storage one time, as this might be run frequently when
    # switching between channels/dms/mpdms
    messages = {}
    for channel_id, channel in channels.items():
        # Determine the correct directory path based on channel type
        if channel.type == "channel":
            channel_dir = export_dir / channel.name
        elif channel.type == "dm":
            channel_dir = export_dir / channel_id
        elif channel.type == "mpdm":
            # MPDM folders use double dashes between usernames and end with -1
            member_names = [users[uid].user_name for uid in channel.members if uid in users]
            channel_dir = export_dir / f"mpdm-{'--'.join(sorted(member_names))}-1"
        else:
            continue

        if not channel_dir.exists():
            continue

        channel_messages = []
        for msg_file in channel_dir.glob("*.json"):
            if msg_file.name == "canvas_in_the_conversation.json":
                continue

            with open(msg_file, "r", encoding="utf-8") as f:
                day_messages = json.load(f)
                for msg in day_messages:
                    if "subtype" in msg:  # Skip system messages
                        continue

                    channel_messages.append(Message(
                        user=msg["user"],
                        text=msg["text"],
                        ts=parse_timestamp(msg["ts"]),
                        thread_ts=parse_timestamp(msg["thread_ts"]) if "thread_ts" in msg else None,
                        attachments=msg.get("files", [])
                    ))

        if channel_messages:
            messages[channel_id] = sorted(channel_messages, key=lambda m: m.ts)

    return WorkspaceData(users=users, channels=channels, messages=messages)