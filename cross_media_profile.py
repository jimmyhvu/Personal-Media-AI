from openai import OpenAI
import json

client = OpenAI()

MEDIA_FILE = "media_log.jsonl"
SPOTIFY_FILE = "spotify_summary.json"
STEAM_PREFS_FILE = "steam_preferences.json"
OUTPUT_FILE = "cross_media_profile.json"


# -----------------------
# Load explicit media reviews
# -----------------------

media_records = []

with open(MEDIA_FILE, "r", encoding="utf-8") as f:
    for line in f:
        media_records.append(json.loads(line))

with open(CONVERSATION_FILE, "r", encoding="utf-8") as f:
    conversation_profile = json.load(f)

# Keep this compact
media_summary = []

for item in media_records:
    media_summary.append({
        "title": item.get("title"),
        "type": item.get("type"),
        "rating": item.get("rating"),
        "liked_elements": item.get("liked_elements", []),
        "disliked_elements": item.get("disliked_elements", []),
        "taste_signals": item.get("taste_signals", [])
    })


# -----------------------
# Load Spotify summary
# -----------------------

with open(SPOTIFY_FILE, "r", encoding="utf-8") as f:
    spotify_summary = json.load(f)


# -----------------------
# Load Steam preferences
# -----------------------

with open(STEAM_PREFS_FILE, "r", encoding="utf-8") as f:
    steam_data = json.load(f)


# -----------------------
# Build one combined object
# -----------------------

combined = {
    "explicit_media_reviews": media_summary,
    "spotify_behavior": spotify_summary,
    "steam_behavior_and_answers": steam_data,
    "conversation_derived_profile": conversation_profile
}

response = client.responses.create(
    model="gpt-5.6",
input=f"""
You are building a unified taste profile for one person.

You have four evidence sources:

1. EXPLICIT MEDIA REVIEWS
Direct reactions and ratings. Strong evidence for specific media preferences.

2. SPOTIFY BEHAVIOR
Long-term listening behavior. Strong behavioral evidence, but listening time
does not always equal preference.

3. STEAM BEHAVIOR AND ANSWERS
Playtime is behavioral evidence. Explicit follow-up answers are stronger than
playtime alone.

4. CONVERSATION-DERIVED PROFILE
Higher-level patterns inferred from many conversations with this person.
Treat high-confidence traits as useful general priors, but do not let them
override contradictory direct behavioral evidence.

Combined evidence:

{json.dumps(combined, ensure_ascii=False)}

Produce a unified cross-media taste profile.

Distinguish:
- high-confidence preferences supported by multiple sources
- medium-confidence preferences
- meaningful contradictions
- medium-specific preferences
- general cognitive/aesthetic preferences
- hypotheses that still need evidence

Do not merely summarize the four sources separately.
"""
)

profile_text = response.output_text

print("\nCROSS-MEDIA TASTE PROFILE\n")
print(profile_text)


output = {
    "profile": profile_text,
    "source_files": {
        "media": MEDIA_FILE,
        "spotify": SPOTIFY_FILE,
        "steam": STEAM_PREFS_FILE
    }
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(
        output,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"\nSaved to {OUTPUT_FILE}")