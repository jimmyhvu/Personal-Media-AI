from openai import OpenAI
import json

client = OpenAI()

DATA_FILE = "media_log.jsonl"

records = []

with open(DATA_FILE, "r", encoding="utf-8") as f:
    for line in f:
        records.append(json.loads(line))

print(f"Loaded {len(records)} media records.")

corpus = ""

for item in records:
    corpus += f"""
Title: {item['title']}
Type: {item['type']}
Rating: {item['rating']}
Thoughts: {item['thoughts']}
Taste signals: {", ".join(item['taste_signals'])}

"""

candidate = input("What are you considering watching/playing/reading? ")

response = client.responses.create(
    model="gpt-5.6",
    input=f"""
You are analyzing one person's media preferences.

Here is their media history:

{corpus}

Infer a concise taste profile.

Focus on:
- what they consistently like
- what they consistently dislike
- storytelling preferences
- pacing preferences
- stylistic preferences
- what kinds of recommendations are risky for them

Do not just summarize individual titles.
Look for patterns across the corpus.

Based on this taste profile and history, predict how this person would react to:

{candidate}

Explain:
- likely positives
- likely negatives
- confidence

"""
)

print("\nTASTE PROFILE\n")
print(response.output_text)

