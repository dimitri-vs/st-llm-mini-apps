# utils/people_roles.py
import re
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from .anthropic_llm import get_anthropic_json_completion

# Hard-coded participants dictionary: name -> role
KNOWN_PARTICIPANTS = {
    "Dimitri": "Elevate Code web app development agency founder",
    "Clayton": "agency sales & accounts manager",
    "Pawan (VTT: Pollen, Pawel, Paul)": "agency full-stack dev and AI engineer",
    "Luis (VTT: Lewis)": "agency full-stack dev and AI engineer",
    "Talha": "agency full-stack dev and AI engineer",
    "Kareem": "agency full-stack dev and AI engineer",
    "Ikechi (VTT: Akachi)": "agency no-code Bubble dev and AI engineer",
    "Joao (VTT: Drow, Draw)": "agency no-code Bubble dev and AI engineer",
}


def detect_participants_with_llm(transcript):
    """
    Calls the LLM to parse out the participants from the transcript and guess their roles.
    Returns a list of dicts: [{'name': 'Dimitri', 'role': 'Guessed or known role'}, ...].
    """
    known_participants_str = "\n".join([f"- {name}: {role}" for name, role in KNOWN_PARTICIPANTS.items()])

    llm_prompt = f"""
    Here are some known participants and their roles that may appear in transcripts:
    {known_participants_str}

    Note: Voice-to-text software often mistranscribes proper nouns and names. For example,
    "Dimitri" might appear as "Dimitry" or "Jimmy Tree" in transcripts. Please use context
    to accurately identify participants even when names are slightly mistranscribed.

    From the following transcript, extract a list of participants.
    A "participant" is anyone who spoke in the meeting, or is mentioned multiple times in the transcript.
    Do NOT include people who are only mentioned once or twice in passing.

    For each participant:
    - If they match a known participant above (including possible mistranscriptions), use that role
    - Otherwise, guess their role or relationship based on context
    - Identify which team/organization they belong to based on context clues
    - When confident, use the correct canonical name in your response

    Return your answer as JSON with structure:
    [
      {{
        "name": "...",
        "role": "...",
        "confidence": "... (optional rating if uncertain about role)"
      }},
      ...
    ]

    Transcript:
    {transcript}
    """
    # Use existing JSON completion function
    response_json = get_anthropic_json_completion([{"role": "user", "content": llm_prompt}])

    try:
        participants = json.loads(response_json)
        # Handle case where response is wrapped in a 'participants' key
        if isinstance(participants, dict) and 'participants' in participants:
            participants = participants['participants']
        if not isinstance(participants, list):
            participants = []
    except json.JSONDecodeError:
        participants = []

    return participants


def merge_known_roles(detected_participants):
    """
    Merges a list of detected participants with the known participants dictionary.
    Returns a new list of participants with updated roles where known.
    """
    print(f"detected_participants: {detected_participants}")
    merged = []
    for p in detected_participants:
        # Convert name to lower to match your KNOWN_PARTICIPANTS dictionary
        key = p["name"].lower()
        if key in KNOWN_PARTICIPANTS:
            p["role"] = KNOWN_PARTICIPANTS[key]
        merged.append(p)
    return merged


def parse_people_roles(transcript):
    """
    High-level function to:
    1. Detect participants via LLM.
    2. Merge with known roles.
    3. Return final participant list.
    """
    detected = detect_participants_with_llm(transcript)
    merged = merge_known_roles(detected)
    return merged

if __name__ == '__main__':
    # Get the project root directory (2 levels up from this file)
    project_root = Path(__file__).parent.parent
    sys.path.append(str(project_root))

    # Load environment variables from .env file
    load_dotenv(project_root / '.env')

    # Sample transcript for testing
    test_transcript = """
    """.strip()

    print("\nTesting participant detection:")
    participants = parse_people_roles(test_transcript)
    print("\nParticipants detected:")
    for p in participants:
        print(f"- {p['name']}: {p['role']}")
