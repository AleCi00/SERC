import json
from loadEmotions import load_genre_words, load_combined_emotions_with_scores

# Percorso del file
file_path = "emoji/emoji.json"


def sub_emoji(text):
    with open(file_path, "r", encoding="utf-8") as f:
        emojis = json.load(f)  # carica la lista di dizionari

    for entry in emojis:
        emoji = entry["emoji"]
        meaning = entry["meaning"]
        if emoji in text:
            text = text.replace(emoji, meaning)

    return text

with open(file_path, "r+", encoding="utf-8") as f:
    emojis = json.load(f)  # carica la lista di dizionari

genre_words = load_genre_words("genres")
emotion_entries = load_combined_emotions_with_scores("prototipi_14_termini")

for entry in emojis:
    emoji = entry["emoji"]
    meaning = entry["meaning"]
    entry["emotion"] = []
    entry["complex_emotion"] = []
    if meaning in genre_words:
        for score, genre in genre_words[meaning]:
            entry["emotion"].append(genre)
    for title, emotion_words in emotion_entries:
        if meaning in emotion_words:
            entry["complex_emotion"].append(title)

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(emojis, f, ensure_ascii=False, indent=2)

print("File emoji.json aggiornato con i campi 'emotion'.")
