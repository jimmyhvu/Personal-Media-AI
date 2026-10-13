from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import math
import os

load_dotenv()

client = OpenAI()

PROFILE_FILE = "cross_media_profile.json"
MEDIA_FILE = "media_log.jsonl"
EMBEDDINGS_FILE = "media_embeddings.jsonl"
WATCHLIST_FILE = "watchlist.jsonl"
STEAM_FILE = "steam_library_enriched.jsonl"
DRAFTS_FILE = "review_drafts.json"
VISUALS_FILE = "media_visuals.json"
CHAT_FILE = "media_chats.json"
CHAT_NOTES_FILE = "media_chat_notes.json"
MANUAL_SIGNALS_FILE = "manual_taste_signals.json"



# -----------------------------
# Structured outputs
# -----------------------------

class DiscoveryResult(BaseModel):
    interpretation: str
    recommendations: list[str]
    recommendation_types: list[str]
    why_these_fit: list[str]
    cautions: list[str]


class EvaluationResult(BaseModel):
    fit_score: int
    confidence: str
    likely_positives: list[str]
    likely_negatives: list[str]
    relevant_past_examples: list[str]
    verdict: str


class MediaAnalysis(BaseModel):
    genres: list[str]
    themes: list[str]
    liked_elements: list[str]
    disliked_elements: list[str]
    taste_signals: list[str]

class VisualSearchResult(BaseModel):
    image_url: str | None


class ReviewMemoryCandidate(BaseModel):
    title: str
    media_type: str
    reason: str
    confidence: str


class ReviewMemoryResult(BaseModel):
    suggestions: list[ReviewMemoryCandidate]


class TasteSignalCandidate(BaseModel):
    signal: str
    confidence: str
    rationale: str


class ReviewDraftFromChat(BaseModel):
    thoughts: str
    suggested_rating: int | None


# -----------------------------
# Utilities
# -----------------------------

def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))

    if mag_a == 0 or mag_b == 0:
        return 0

    return dot / (mag_a * mag_b)


def load_profile():
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    profile = data["profile"]

    # Explicitly approved signals are kept separately so the original generated
    # profile is never destructively rewritten. They still become live context
    # everywhere the app calls load_profile().
    manual_signals = load_manual_taste_signals()
    if manual_signals:
        lines = [
            f"- {item.get('signal', '').strip()}"
            for item in manual_signals
            if item.get("signal", "").strip()
        ]
        if lines:
            profile += (
                "\n\nUSER-APPROVED TASTE SIGNALS\n"
                + "\n".join(lines)
            )

    return profile


def load_media_log():
    reviews = []

    if not os.path.exists(MEDIA_FILE):
        return reviews

    with open(MEDIA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                reviews.append(json.loads(line))

    return reviews


def load_embeddings():
    reviews = []

    if not os.path.exists(EMBEDDINGS_FILE):
        return reviews

    with open(EMBEDDINGS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            reviews.append(json.loads(line))

    return reviews


def embed_text(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


def retrieve_reviews(query, limit=5):
    reviews = load_embeddings()

    if not reviews:
        return []

    query_embedding = embed_text(query)

    results = []

    for review in reviews:
        similarity = cosine_similarity(
            query_embedding,
            review["embedding"]
        )

        results.append((similarity, review))

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return results[:limit]


def build_review_context(matches):
    context = ""

    for similarity, review in matches:
        context += f"""
Title: {review['title']}
Type: {review['type']}
Rating: {review['rating']}
Thoughts: {review['thoughts']}
Taste signals: {", ".join(review.get('taste_signals', []))}
Similarity: {similarity:.3f}

"""

    return context


def load_steam_library():
    games = []

    if not os.path.exists(STEAM_FILE):
        return games

    with open(STEAM_FILE, "r", encoding="utf-8") as f:
        for line in f:
            games.append(json.loads(line))

    return games


def get_unplayed_steam_games(max_hours=2.0):
    games = load_steam_library()

    candidates = [
        game for game in games
        if game.get("playtime_hours", 0) <= max_hours
    ]

    return candidates

def load_review_drafts():
    if not os.path.exists(DRAFTS_FILE):
        return {}

    with open(DRAFTS_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()

        if not content:
            return {}

        return json.loads(content)


def save_review_draft(title, media_type, rating, thoughts):
    drafts = load_review_drafts()

    key = f"{media_type}::{title}".lower()

    drafts[key] = {
        "title": title,
        "type": media_type,
        "rating": rating,
        "thoughts": thoughts
    }

    with open(DRAFTS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            drafts,
            f,
            ensure_ascii=False,
            indent=2
        )


def delete_review_draft(title, media_type):
    drafts = load_review_drafts()

    key = f"{media_type}::{title}".lower()

    drafts.pop(key, None)

    with open(DRAFTS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            drafts,
            f,
            ensure_ascii=False,
            indent=2
        )

# -----------------------------
# Media chat and explicit taste memory
# -----------------------------

def _load_json_object(path):
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        return json.loads(content) if content else {}


def _save_json_object(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _media_key(title, media_type):
    return f"{media_type}::{title}".strip().lower()


def load_media_chat(title, media_type):
    chats = _load_json_object(CHAT_FILE)
    record = chats.get(_media_key(title, media_type), {})
    return record.get("messages", [])


def save_media_chat(title, media_type, messages):
    chats = _load_json_object(CHAT_FILE)
    chats[_media_key(title, media_type)] = {
        "title": title,
        "type": media_type,
        "messages": messages
    }
    _save_json_object(CHAT_FILE, chats)


def clear_media_chat(title, media_type):
    chats = _load_json_object(CHAT_FILE)
    chats.pop(_media_key(title, media_type), None)
    _save_json_object(CHAT_FILE, chats)


def load_media_notes(title, media_type):
    notes = _load_json_object(CHAT_NOTES_FILE)
    record = notes.get(_media_key(title, media_type), {})
    return record.get("notes", [])


def save_media_note(title, media_type, text, source="user"):
    notes = _load_json_object(CHAT_NOTES_FILE)
    key = _media_key(title, media_type)
    record = notes.get(key, {
        "title": title,
        "type": media_type,
        "notes": []
    })

    normalized = text.strip()
    if normalized and not any(
        item.get("text", "").strip() == normalized
        for item in record.get("notes", [])
    ):
        record.setdefault("notes", []).append({
            "text": normalized,
            "source": source
        })

    notes[key] = record
    _save_json_object(CHAT_NOTES_FILE, notes)


def load_manual_taste_signals():
    data = _load_json_object(MANUAL_SIGNALS_FILE)
    return data.get("signals", [])


def save_manual_taste_signal(title, media_type, signal, source_excerpt=""):
    data = _load_json_object(MANUAL_SIGNALS_FILE)
    signals = data.setdefault("signals", [])

    normalized = signal.strip()
    if normalized and not any(
        item.get("signal", "").strip().lower() == normalized.lower()
        for item in signals
    ):
        signals.append({
            "title": title,
            "type": media_type,
            "signal": normalized,
            "source_excerpt": source_excerpt.strip()
        })

    _save_json_object(MANUAL_SIGNALS_FILE, data)


def remove_manual_taste_signal(index):
    data = _load_json_object(MANUAL_SIGNALS_FILE)
    signals = data.get("signals", [])

    if 0 <= index < len(signals):
        signals.pop(index)

    data["signals"] = signals
    _save_json_object(MANUAL_SIGNALS_FILE, data)


def chat_about_media(
    title,
    media_type,
    messages,
    progress="",
    spoiler_mode="No spoilers",
):
    profile = load_profile()
    matches = retrieve_reviews(
        f"{title} {media_type} {progress}".strip(),
        limit=5
    )
    review_context = build_review_context(matches)
    saved_notes = load_media_notes(title, media_type)

    # Keep enough continuity for a real discussion without letting old chatter
    # dominate context forever.
    recent_messages = messages[-20:]

    response = client.responses.create(
        model="gpt-5.6",
        input=f"""
You are the discussion partner inside a personal media journal.

The user is talking about ONE work:
Title: {title}
Type: {media_type}
Progress / where they are: {progress or "Not specified"}
Spoiler rule: {spoiler_mode}

Treat the spoiler rule as binding. If progress is supplied, do not reveal events
beyond that point unless the spoiler rule explicitly allows full spoilers.

PERSONAL TASTE PROFILE
{profile}

RELEVANT PAST REVIEWS
{review_context}

USER-SAVED NOTES ABOUT THIS WORK
{json.dumps(saved_notes, ensure_ascii=False)}

RECENT CONVERSATION
{json.dumps(recent_messages, ensure_ascii=False)}

Respond naturally to the user's latest message. Be analytical and specific rather
than generic. Use the profile and past reviews when genuinely helpful, but do not
pretend an inference is something the user explicitly said. Distinguish between:
- something the user has actually stated
- an inference about their taste
- your own interpretation of the work

Do not turn every exchange into a recommendation or a taste-profile update.
This is primarily a conversation about the work.
"""
    )

    return response.output_text


def extract_taste_signal_from_excerpt(title, media_type, excerpt):
    profile = load_profile()

    response = client.responses.parse(
        model="gpt-5.6",
        input=f"""
Determine whether this USER-WRITTEN excerpt contains a durable taste signal worth
remembering across future media discussions.

Title: {title}
Type: {media_type}

Current profile for context:
{profile}

User excerpt:
{excerpt}

Return ONE concise signal. It should describe a durable preference, aversion, or
pattern in how this person responds to media rather than merely summarize the work.
Do not infer more strongly than the excerpt supports.

Also return confidence (high, medium, or low) and a one-sentence rationale.
If the excerpt is mostly plot discussion or contains no durable signal, say so in
rationale and make the signal conservative.
""",
        text_format=TasteSignalCandidate
    )

    return response.output_parsed


def draft_review_from_chat(title, media_type, messages, saved_notes=None):
    saved_notes = saved_notes or []
    user_messages = [
        item.get("content", "")
        for item in messages
        if item.get("role") == "user" and item.get("content", "").strip()
    ]

    response = client.responses.parse(
        model="gpt-5.6",
        input=f"""
Turn the user's own remarks into a concise first-person review draft.

Title: {title}
Type: {media_type}

USER MESSAGES
{json.dumps(user_messages, ensure_ascii=False)}

USER-SAVED NOTES
{json.dumps(saved_notes, ensure_ascii=False)}

Rules:
- Preserve the user's actual opinions and emphasis.
- Do not invent reactions, facts, or a verdict the user did not express.
- Write 1-3 compact paragraphs in first person.
- suggested_rating should be 1-10 only if the user's remarks strongly imply one;
  otherwise return null.
""",
        text_format=ReviewDraftFromChat
    )

    return response.output_parsed


# -----------------------------
# Discover
# -----------------------------

def request_mentions_steam_library(request):
    text = request.lower()

    triggers = [
        "my steam library",
        "in my steam library",
        "something i own",
        "something unplayed",
        "unplayed in my library",
        "family shared",
        "family sharing",
        "my backlog"
    ]

    return any(trigger in text for trigger in triggers)

def discover_steam_backlog(request, max_hours=2.0, web_search=False):
    profile = load_profile()
    games = get_unplayed_steam_games(max_hours)

    print(f"Steam backlog candidates found: {len(games)}")

    if not games:
        raise ValueError(
            "No Steam backlog games were loaded. "
            "Check steam_library_enriched.jsonl."
        )

    candidates = []

    for game in games:
        candidates.append({
            "name": game.get("name"),
            "playtime_hours": game.get("playtime_hours", 0),
            "genres": game.get("genres", []),
            "categories": game.get("categories", []),
            "short_description": game.get("short_description", "")
        })

    candidate_names = [
        game["name"]
        for game in candidates
        if game["name"]
    ]

    response = client.responses.parse(
        model="gpt-5.6",
        input=f"""
You are selecting games from this person's ACTUAL Steam library.

You DO have access to the supplied Steam library data below.

Do not say that you cannot see the user's library.
Do not recommend any title that is not in the supplied candidate list.

USER REQUEST

{request}

PERSONAL TASTE PROFILE

{profile}

ACTUAL STEAM LIBRARY CANDIDATES
These games all have <= {max_hours} hours recorded playtime:

{json.dumps(candidates, ensure_ascii=False)}

Choose exactly 5 games from the candidate list above.

Prioritize:
- strong fit with the taste profile
- games whose appeal should become apparent within roughly two hours
- games with very little recorded playtime

Return:
- interpretation
- exactly 5 recommendation titles
- exactly 5 recommendation types, one for each title; every type must be "Game"
- one reason for each
- one caution for each
""",
        text_format=DiscoveryResult,
        **({"tools": [{"type": "web_search"}]} if web_search else {})
    )

    result = response.output_parsed

    # Safety check: reject hallucinated titles
    allowed = {
        name.strip().lower()
        for name in candidate_names
    }

    invalid = [
        title
        for title in result.recommendations
        if title.strip().lower() not in allowed
    ]

    if invalid:
        raise ValueError(
            "Model recommended titles outside your Steam backlog: "
            + ", ".join(invalid)
        )

    return result

def discover_media(request, web_search=True):

    if request_mentions_steam_library(request):
        print("Routing to personal Steam library")
        return discover_steam_backlog(request, web_search=web_search)

    print("Routing to general discovery")

    profile = load_profile()

    matches = retrieve_reviews(request)
    context = build_review_context(matches)

    response = client.responses.parse(
        model="gpt-5.6",
        input=f"""
You are a personalized media discovery assistant.

GENERAL TASTE PROFILE

{profile}

CURRENT REQUEST

{request}

MOST RELEVANT PAST REACTIONS

{context}

Recommend exactly 5 pieces of media.

They may be television, film, books, games, music, or essays
unless the user restricts the medium.

Use:
1. the current request
2. the long-term taste profile
3. relevant past reactions

Avoid merely recommending copies of things already consumed.

For every recommendation, the recommendation title must contain ONLY
the canonical title of the work.

In the title, do not include:
- release year
- country
- director, author, artist, or creator
- platform
- explanatory text
- parentheses with metadata
- em dashes or subtitles that are not actually part of the official title

Outside of the title, this information is fine to include as reasons or caution, etc.

Return:
- interpretation
- exactly 5 recommendations
- exactly 5 recommendation types, one corresponding to each recommendation
- types must be one of: TV, Movie, Game, Book, Music, Essay, Other
- one reason for each
- one caution for each
""",
        text_format=DiscoveryResult,
        **({"tools": [{"type": "web_search"}]} if web_search else {})
    )

    return response.output_parsed


# -----------------------------
# Review memory jogger
# -----------------------------

def suggest_review_candidates(media_type="Any", excluded_titles=None, count=6):
    profile = load_profile()
    reviews = load_media_log()
    steam_games = load_steam_library()

    excluded_titles = excluded_titles or []

    reviewed_titles = {
        review.get("title", "").strip().lower()
        for review in reviews
        if review.get("title")
    }

    excluded = {
        title.strip().lower()
        for title in excluded_titles
        if title
    }

    review_history = [
        {
            "title": review.get("title"),
            "type": review.get("type"),
            "rating": review.get("rating")
        }
        for review in reviews[-80:]
    ]

    played_steam = []
    for game in steam_games:
        hours = game.get("playtime_hours", 0) or 0
        if hours > 0.5 and game.get("name"):
            played_steam.append({
                "name": game.get("name"),
                "playtime_hours": hours
            })

    played_steam.sort(
        key=lambda game: game["playtime_hours"],
        reverse=True
    )
    played_steam = played_steam[:40]

    focus_instruction = (
        "Use any media type."
        if media_type == "Any"
        else f'Every suggestion must have media_type "{media_type}".'
    )

    response = client.responses.parse(
        model="gpt-5.6",
        input=f"""
You are a memory jogger helping someone build a personal media-review corpus.

Your job is NOT to recommend new things. Suggest works the person is likely to
have ALREADY seen, played, read, or heard and could have a useful opinion about.

PERSONAL TASTE PROFILE

{profile}

ALREADY REVIEWED

{json.dumps(review_history, ensure_ascii=False)}

STEAM TITLES WITH RECORDED PLAYTIME
These are especially strong evidence that a game may have been played, but do not
suggest a game that is already in ALREADY REVIEWED.

{json.dumps(played_steam, ensure_ascii=False)}

DO NOT SUGGEST THESE TITLES

{json.dumps(sorted(excluded), ensure_ascii=False)}

FOCUS

{focus_instruction}

Return exactly {count} suggestions.

Prioritize:
- high probability the person has actually consumed the work
- works likely to produce a strong or distinctive opinion, not just bland familiarity
- a useful spread across eras, genres, and media when focus is Any
- well-known or taste-adjacent works that can jog memory
- actual played Steam titles when they are good candidates for a Game suggestion

Avoid:
- anything already reviewed
- titles in the exclusion list
- obscure guesses merely because they resemble something in the profile
- treating this as a discovery/recommendation task

For every suggestion return:
- canonical title only
- media_type: one of TV, Movie, Game, Book, Music, Essay, Other
- a short reason explaining why it is plausible this person has consumed it or why it
  is likely to trigger a useful memory
- confidence: high, medium, or low
""",
        text_format=ReviewMemoryResult
    )

    result = response.output_parsed

    # Final guard against repeats already in the corpus or explicitly dismissed.
    filtered = []
    for item in result.suggestions:
        normalized = item.title.strip().lower()
        if normalized in reviewed_titles or normalized in excluded:
            continue
        filtered.append(item)

    result.suggestions = filtered[:count]
    return result


# -----------------------------
# Evaluate a specific title
# -----------------------------

def evaluate_media(title, media_type, description, web_search=False):
    profile = load_profile()

    candidate = f"""
Title: {title}
Type: {media_type}
Description: {description}
"""

    matches = retrieve_reviews(candidate)
    context = build_review_context(matches)

    response = client.responses.parse(
        model="gpt-5.6",
        input=f"""
Predict how this specific person will react to a piece of media.

GENERAL TASTE PROFILE

{profile}

CANDIDATE

{candidate}

RELEVANT PAST REACTIONS

{context}

Use the profile as a general prior.
Give especially strong weight to directly relevant past reactions.

Return:
- fit_score from 1 to 10
- confidence: low, medium, or high
- likely positives
- likely negatives
- relevant past examples
- concise personalized verdict

Do not give a generic review.
Predict this person's reaction.
""",
        text_format=EvaluationResult,
        **({"tools": [{"type": "web_search"}]} if web_search else {})
    )

    return response.output_parsed


# -----------------------------
# Add review
# -----------------------------

def add_review(title, media_type, rating, thoughts, web_search=False):
    response = client.responses.parse(
        model="gpt-5.6",
        input=f"""
Analyze this person's reaction to a piece of media.

Title: {title}
Type: {media_type}
Rating: {rating}/10

Reaction:
{thoughts}

Extract durable information about this person's taste.

Focus on:
- genres
- themes
- what they liked
- what they disliked
- broader taste signals

Do not merely summarize the work.
""",
        text_format=MediaAnalysis,
        **({"tools": [{"type": "web_search"}]} if web_search else {})
    )

    analysis = response.output_parsed

    record = {
        "title": title,
        "type": media_type,
        "rating": rating,
        "thoughts": thoughts,
        "genres": analysis.genres,
        "themes": analysis.themes,
        "liked_elements": analysis.liked_elements,
        "disliked_elements": analysis.disliked_elements,
        "taste_signals": analysis.taste_signals
    }

    # Save normal review
    with open(MEDIA_FILE, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(record, ensure_ascii=False)
            + "\n"
        )

    # Immediately create and cache its embedding
    review_text = f"""
Title: {title}
Type: {media_type}
Rating: {rating}
Thoughts: {thoughts}
Taste signals: {", ".join(analysis.taste_signals)}
"""

    embedding = embed_text(review_text)

    embedding_record = {
        **record,
        "embedding": embedding
    }

    with open(EMBEDDINGS_FILE, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                embedding_record,
                ensure_ascii=False
            )
            + "\n"
        )

    return analysis

def load_watchlist():
    items = []

    if not os.path.exists(WATCHLIST_FILE):
        return items

    with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))

    return items


def add_to_watchlist(title, media_type="Unknown", note=""):
    items = load_watchlist()

    # Don't add duplicates
    for item in items:
        if (
            item["title"].strip().lower() == title.strip().lower()
            and item["type"] == media_type
        ):
            return False

    record = {
        "title": title,
        "type": media_type,
        "note": note
    }

    with open(WATCHLIST_FILE, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(record, ensure_ascii=False)
            + "\n"
        )

    return True


def remove_from_watchlist(title, media_type):
    items = load_watchlist()

    remaining = [
        item
        for item in items
        if not (
            item["title"] == title
            and item["type"] == media_type
        )
    ]

    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        for item in remaining:
            f.write(
                json.dumps(item, ensure_ascii=False)
                + "\n"
            )

def load_visuals():
    if not os.path.exists(VISUALS_FILE):
        return {}

    with open(VISUALS_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()

        if not content:
            return {}

        return json.loads(content)


def get_visual(title, media_type):
    visuals = load_visuals()

    key = f"{media_type}::{title}".lower()

    return visuals.get(key)


def save_visual(title, media_type, image_url):
    visuals = load_visuals()

    key = f"{media_type}::{title}".lower()

    visuals[key] = image_url

    with open(VISUALS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            visuals,
            f,
            ensure_ascii=False,
            indent=2
        )

def fetch_game_visual(title):
    games = load_steam_library()

    normalized_title = title.strip().lower()

    for game in games:
        if game.get("name", "").strip().lower() == normalized_title:

            # Prefer an image URL already obtained from Steam
            # when the library was enriched.
            for field in [
                "header_image",
                "capsule_image",
                "library_image"
            ]:
                image_url = game.get(field)

                if image_url:
                    return image_url

            appid = game.get("appid")

            if appid:
                return (
                    "https://cdn.cloudflare.steamstatic.com/"
                    f"steam/apps/{appid}/header.jpg"
                )

    return None

def fetch_media_visual(title, media_type):
    response = client.responses.parse(
        model="gpt-5.6",
        tools=[
            {
                "type": "web_search"
            }
        ],
        input=f"""
Find a representative cover/poster/artwork image for this media item.

Title: {title}
Type: {media_type}

Return a direct image URL when possible.

Prefer:
- official artwork
- publisher/developer/studio pages
- Steam artwork for games
- book covers for books
- album artwork for music

The image must actually correspond to this exact work.
Do not return an unrelated work with the same title.

If you cannot confidently identify a suitable image, return null.
""",
        text_format=VisualSearchResult
    )

    result = response.output_parsed

    return result.image_url