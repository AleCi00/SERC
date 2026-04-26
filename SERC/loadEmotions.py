import os
import re
import string
from collections import defaultdict

import json

#Legge file .txt all'interno della cartella, associando: ogni parola a un punteggio numerico relativo ad un emozione (nome file usato come etichetta di genere/emozione).
def load_genre_words(genre_folder):
    genre_words = defaultdict(list)
    for filename in os.listdir(genre_folder):
        file_path = os.path.join(genre_folder, filename)
        if os.path.isfile(file_path) and filename.endswith(".txt"):
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        word = parts[0].lower().rstrip(string.punctuation)
                        try:
                            score = float(parts[1])
                            genre_words[word].append((score, filename[:-4]))
                        except ValueError:
                            continue
    return genre_words  #Ritorna una mappa { parola: [(score, genere)] }


#Cerca in ogni file: Il campo Title: ... → nome dell’emozione e il blocco Result: { ... } → dizionario di parole con punteggi.
def load_combined_emotions_with_scores(folder_path):
    combined_emotions = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as file:
                content = file.read()
                title_match = re.search(r"Title:\s*(.+)", content)
                title = title_match.group(1).strip() if title_match else "Unknown"
                result_match = re.search(r"Result:\s*(\{.*?\})", content, re.DOTALL)
                if result_match:
                    try:
                        result_data = json.loads(result_match.group(1))
                        emotion_words = {
                            k.lower(): v for k, v in result_data.items() if not k.startswith("@")
                        }
                        combined_emotions.append((title, emotion_words))
                    except json.JSONDecodeError:
                        print(f"⚠️ Warning: Could not parse result block in {filename}")
    return combined_emotions  #lista (titolo_emozione, {parola: punteggio})


#Ordina le voci JSON in base al valore massimo tra i punteggi di tutti i generi associati, scrivendo l’output in un nuovo .json ordinato
def sort_json_by_max_genre_score(input_path, output_path, genre_words):
    with open(input_path, 'r', encoding='utf-8') as infile:
        data = json.load(infile)
    all_genres = set()  # Costruisce un insieme (set) di tutti i nomi di genere presenti in `genre_words`.
    for values in genre_words.values():  #Li filtra per raccogliere quelli unici
        for _, genre in values:
            all_genres.add(genre)

    def max_genre_score(
            entry):  # Funzione locale che calcola il punteggio massimo tra tutti i generi usata poi come chiave per l'ordiamento
        return max((entry.get(genre, 0.0) for genre in all_genres), default=0.0)

    sorted_data = sorted(data, key=max_genre_score, reverse=True)  # Crea una nuova lista data ma ordinata
    with open(output_path, 'w', encoding='utf-8') as outfile:
        json.dump(sorted_data, outfile, indent=2, ensure_ascii=False)  #La mette nel file di output


#e = load_combined_emotions_with_scores("prototipi_14_termini")
#for l in e:
#    print(l)

#e = load_genre_words("genres")
#print(e)