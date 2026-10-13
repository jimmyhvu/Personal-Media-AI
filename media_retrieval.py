from openai import OpenAI
import json
import math

client = OpenAI()

DATA_FILE = "media_log.jsonl"


def cosine_similarity(a, b):
    dot_product = sum(x * y for x, y in zip(a, b))
    magnitude_a = math.sqrt(sum(x * x for x in a))
    magnitude_b = math.sqrt(sum(x * x for x in b))

    return dot_product / (magnitude_a * magnitude_b)


def make_review_text(item):
    return f"""
Title: {item['title']}
Type: {item['type']}
Rating: {item['rating']}
Thoughts: {item['thoughts']}
Taste signals: {", ".join(item['taste_signals'])}
"""


# Load your saved media reviews
records = []

with open(DATA_FILE, "r", encoding="utf-8") as f:
    for line in f:
        records.append(json.loads(line))

print(f"Loaded {len(records)} media records.")


# Create embeddings for the reviews
print("Creating embeddings for your reviews...")

for item in records:
    review_text = make_review_text(item)

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=review_text
    )

    item["embedding"] = response.data[0].embedding


# Ask what kind of media you're considering
candidate = input(
    "\nDescribe something you're considering watching, reading, or playing:\n"
)


# Create an embedding for the candidate
candidate_response = client.embeddings.create(
    model="text-embedding-3-small",
    input=candidate
)

candidate_embedding = candidate_response.data[0].embedding


# Compare candidate against every review
results = []

for item in records:
    similarity = cosine_similarity(
        candidate_embedding,
        item["embedding"]
    )

    results.append((similarity, item))


# Highest similarity first
results.sort(key=lambda x: x[0], reverse=True)


top_matches = results[:5]

context = ""

for similarity, item in top_matches:
    context += f"""
Title: {item['title']}
Rating: {item['rating']}/10
Thoughts: {item['thoughts']}
Taste signals: {", ".join(item['taste_signals'])}

"""

response = client.responses.create(
    model="gpt-5.6",
    input=f"""
You are predicting this person's reaction to a new piece of media.

Candidate:
{candidate}

Here are the most relevant past reactions from their media history:

{context}

Based only on these past reactions, predict:
- likely positives
- likely negatives
- likely overall reaction
- confidence
"""
)

print("\nPREDICTION\n")
print(response.output_text)