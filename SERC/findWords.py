import os
import string
import json
import re
import math
from collections import defaultdict
from loadEmotions import load_combined_emotions_with_scores, load_genre_words
import nltk
from nltk.corpus import stopwords
from pathlib import Path
from SERC.compute_emoji import sub_emoji

# cartella dove hai messo le stopwords scaricate
stopword_path = Path("SERC/stopwords")

# aggiungi il path a nltk
nltk.data.path.append(str(stopword_path))

# Carica il set di stopwords in inglese (dalla libreria nltk).
stop_words_set = set(stopwords.words('english'))
print(f"Loaded {len(stop_words_set)} stopwords")

genre_folder = "genres"
emotion_folder = "prototipi_14_termini"

# Carica emozioni di base
genre_words = load_genre_words(genre_folder)
all_genres = sorted({genre for values in genre_words.values() for _, genre in values})
# Carica emozioni complesse
emotion_entries = load_combined_emotions_with_scores(emotion_folder)


#Rende una parola minuscola e rimuove la punteggiatura.
def clean_word(word):
    return word.lower().translate(str.maketrans('', '', string.punctuation))


#Conta le frequenze delle parole che compaiono nel testo e che appaiono in genre_words e superano una soglia di punteggio e non sono in ignore_words.
"""def count_matching_word_frequencies(target_lines, genre_words, threshold, ignore_words):
    counter = Counter()
    for line in target_lines:
        words = line.split()
        for word in words:
            clean = clean_word(word)
            if clean in genre_words and clean not in ignore_words:
                for score, _ in genre_words[clean]:
                    if score >= threshold:
                        counter[clean] += 1
    return counter.most_common()"""


#Restituisce: Una lista di parole trovate con punteggio, genere e riga, Un dizionario word_hits_by_line con mappa {line_number: [word info...]}
"""def find_matching_words(target_lines, genre_words, threshold, ignore_words):
    matching_words = []
    word_hits_by_line = {}
    for line_number, line in enumerate(target_lines, start=1):
        words = line.split()
        for word in words:
            clean = clean_word(word)
            if clean in genre_words and clean not in ignore_words:
                for score, filename in genre_words[clean]:
                    if score >= threshold:
                        entry = f"{word} {score} - {filename} - line {line_number}"
                        matching_words.append((line_number, entry))
                        word_hits_by_line.setdefault(line_number, []).append(entry)
    return sorted(matching_words), word_hits_by_line"""


#Cerca simboli specifici (es. !) e li conta all’interno delle righe e in totale
"""def find_symbol_lines(target_lines, symbols):
    symbol_lines = {}
    total_occurrences = 0
    for line_number, line in enumerate(target_lines, start=1):
        symbol_count = sum(line.count(symbol) for symbol in symbols)
        if symbol_count > 0:
            symbol_lines[line_number] = (symbol_count, line.rstrip())
            total_occurrences += symbol_count
    return symbol_lines, total_occurrences"""


#Restituisce una lista delle parole completamente maiuscole nel testo.
def uppercase_estraction(text):
    upp_text = re.findall(r'\b[A-ZÀ-Ý]+\b', text)
    return upp_text


def remove_quotes(text):
    # Remove everything between double quotes
    cleaned = re.sub(r'"[^"]*"', '', text)
    # Remove extra spaces
    return ' '.join(cleaned.split())


#Estrae tutte le frasi che terminano con '!' da un testo. Riconosce come separatori .,;:!? e rimuove spazi extra.
def extract_exclamatory_phrases(text):
    # Divide il testo in frasi in base ai segni di punteggiatura
    parts = re.split(r'(?<=[\.\,\;\:\?\!])\s*', text)

    # Filtra solo le frasi che terminano con "!"
    exclamations = [p.strip() for p in parts if p.strip().endswith("!")]

    return exclamations

def remove_proper_noun(text):
    #Rimuove le parole che iniziano con lettera maiuscola ma NON sono a inizio frase o subito dopo un segno di punteggiatura (.!?).

    return re.sub(r'(?<!^)(?<![\.\!\?]\s)\b[A-Z][a-zà-ù]*\b', '', text).strip()


#Normalizza il punteggio delle emozioni rispetto alla lunghezza del testo (meno stopword = punteggio più pesante).
def compute_function_for_basics_and_complex_emotions(score_sum, word_count, stop_word_count, print_result=True):  #Calcola un valore pesato sulla base del numero di parole non banali: più è lungo un testo (e meno stopword ha), più il punteggio viene “normalizzato”.
    if not print_result:
        return None
    denominator = (word_count - stop_word_count) #linere sono per l'intensità
    #denominator = math.sqrt(word_count - stop_word_count)
    #denominator = word_count - stop_word_count
    #if denominator <= 1: #check denominator in order to avoid ZeroDivisionError
    if denominator == 0:  # check denominator in order to avoid ZeroDivisionError
        return round(score_sum / word_count, 4) if word_count > 0 else 0.0
    return round(score_sum / denominator, 4) if word_count > 0 else 0.0
    #return round(score_sum / math.log(denominator, 10), 4) if word_count > 0 else 0.0


# --- Annotate and merge all in one JSON ---
# #Legge un file .json con testi/dialoghi.
#     #Per ogni voce:
#     #Pulisce il testo
#     #Conta parole e stopword
#     #Calcola score per ciascun genere (emozione base)
#     #Calcola score per emozioni complesse (caricate da file)
#     #Aggiunge tutte queste info all’interno della voce JSON
def annotate_json_with_all(json_input_path, json_output_path, threshold, ignore_words, hide_zero_basics):
    # Definizione della funzione principale che annota ogni entry di un JSON con:
    #  - punteggi delle emozioni “base” (genre_words)
    #  - rilevamenti di emozioni complesse (caricate da file in emotion_folder)
    # Parametri:
    #  - json_input_path: path al file JSON di input contenente le entries da analizzare
    #  - json_output_path: path dove salvare il JSON annotato
    #  - threshold: soglia minima di score per considerare una corrispondenza valida
    #  - ignore_words: lista di parole da ignorare (es. parole custom)
    #  - hide_zero_basics: flag che decide se nascondere i generi a punteggio 0
    with open(json_input_path, "r", encoding="utf-8") as infile:
        data = json.load(infile)

    for entry in data:
        text = entry.get("text", "")

        text = remove_proper_noun(text)
        text = sub_emoji(text)
        text = remove_quotes(text)

        upp_text = ' '.join(uppercase_estraction(text) + extract_exclamatory_phrases(text))
        #chiama la funzione che trova e selezione le parole interamente scritte in caratteri maiuscoli e le frasi che terminano con ! (consiederandoli espressione di emozione più intensa)

        # More robust text cleaner - a me non serve molto
        cleaned_text = re.sub(r'(\.\s*){2,}', ' ', text)  # tramite regex rimuove ". . ." e simili
        cleaned_text = cleaned_text.replace("...", " ").replace("- -", " ").replace("-", " ").replace(",", " ")

        raw_words = cleaned_text.split()
        cleaned_words = [clean_word(w) for w in raw_words]  #se non volessi fare quei controlli sostituisco a raw_word text

        stop_word_count = sum(1 for word in cleaned_words if word in stop_words_set)  #conto le stopword in cleaned_words

        # Matching words (genre)
        occurrences = []  # Lista che conterrà tutte le parole (clean) trovate che risultano match con i lessici 'genre_words'
        genre_scores = {genre: 0.0 for genre in all_genres}  #dizionario con le emozioni di base a 0.0, per sommare i punteggi trovati nell'entry
        computed_scores = {}

        for raw, clean in zip(raw_words, cleaned_words):  # scorre contemporaneamente le entry clean (minuscole senza punteggiatura) e quelle raw
            if clean in genre_words and clean not in ignore_words:
                valid = False  # Flag che segnala se almeno uno score supera la soglia (threshold)
                for score, genre in genre_words[clean]:  # Scorre le tuple (score, genre) in genre_words associate a quella parola
                    if score >= threshold:  #se superano la soglia le aggiunge
                        genre_scores[genre] += score
                        valid = True
                if valid:
                    occurrences.append(clean)  #se almeno una delle tuple è valida, registriamo la parola nelle 'occurrences'

        for upp in upp_text.split():
            upp = upp.lower()
            if upp in genre_words and upp not in ignore_words:
                for score, genre in genre_words[upp]:
                    if score >= threshold:
                        genre_scores[genre] += score

        #aggiorna e creai campi nel json in input
        entry["occurrences"] = occurrences
        entry["word_count"] = len(raw_words)
        entry["stop_word_count"] = stop_word_count
        entry["occurrences_count"] = len(occurrences)

        #sum and computed functions
        for genre in all_genres:  #per ogni emozione di base
            total_score = genre_scores[genre]  #somma grezza dei punteggi accumulati
            computed_value = compute_function_for_basics_and_complex_emotions(total_score, entry["word_count"], entry["stop_word_count"], print_result=True)  #normalizza il punteggio in relazione alla frase

            if hide_zero_basics and total_score == 0 and (computed_value is None or computed_value == 0):
                continue  # Se hide_zero_basics è True e sia il punteggio totale grezzo che il computato sono zero non aggiungiamo il genere alla entry (evitiamo campi a 0 nel JSON)

            entry[genre] = round(total_score, 4)  # Aggiunge/aggiorna nella entry il punteggio grezzo (arrotondato a 4 cifre)
            if computed_value is not None:
                computed_scores[genre] = computed_value
            #if computed_value is not None:
            entry[f"{genre}_computed"] = computed_value  #e con il valore normalizzato

        # Combined emotions
        text_words = set(cleaned_words) - set(ignore_words)# Costruisce un set di parole presenti nel testo (clean) da usare per matching con emozioni complesse
        upp_text_word = []# set di parole maiuscole rese minuscole e tolte quelle da ignorare
        for upp in upp_text.split():
            upp = upp.lower()
            if upp not in ignore_words:
                upp_text_word.append(upp)

        found_emotions = []  # Lista che conterrà le emozioni complesse trovate per questa entry (con le parole matched e i punteggi)
        all_occurrences = {}  # Dizionario temporaneo per mantenere il miglior punteggio per parola trovata tra i diversi prototipi

        word_count = len(raw_words)  # Ricalcola il totale dei token
        entry["word_count"] = word_count
        if "anger-NRC-Emotion-Intensity-Lexicon-v1" in computed_scores:
            entry["anger"] = True
        else:
            entry["anger"] = False

        if "fear-NRC-Emotion-Intensity-Lexicon-v1" in computed_scores:
            entry["fear"] = True
        else:
            entry["fear"] = False

        if "sadness-NRC-Emotion-Intensity-Lexicon-v1" in computed_scores:
            entry["sadness"] = True
        else:
            entry["sadness"] = False

        for title, emotion_words in emotion_entries:  # Itera su tutti i prototipi di emozioni complesse caricati prima: - title: nome dell'emozione complessa - emotion_words: dict { parola: score, ... }
            total_c_score = 0 #punteggio totale dell emozione complessa
            computed_score = 0 #punteggio totale dell'emozione complessa normalizzato
            matched = []  # lista per raccogliere le parole di questa emozione complessa che sono presenti nel testo
            for word, score in emotion_words.items():
                if score >= threshold:
                    occurrences = [w for w in text_words if w == word]
                    for _ in occurrences:
                        if word in upp_text_word: #se la parola fa parte di quelle maiuscole la conto raddoppiata
                            total_c_score += score
                        matched.append({
                            "word": word,
                            "score": score
                        })
                        total_c_score += score
                        computed_value = compute_function_for_basics_and_complex_emotions(total_c_score, entry["word_count"], stop_word_count, print_result=True)
                        computed_score += computed_value
                    if word not in all_occurrences or score > all_occurrences[word]:
                        all_occurrences[word] = score  # Memorizza il miglior score osservato per quella parola (se appare in più prototipi)

            if matched:  # Se abbiamo trovato almeno una parola per questo prototipo, aggiungiamo l'oggetto (nome emozione + lista parole trovate) alla lista found_emotions
                found_emotions.append({
                    "emotion": title,
                    "matched_words": matched
                })
                entry[title] = round(total_c_score, 4)  # Aggiunge/aggiorna nella entry il punteggio grezzo (arrotondato a 4 cifre)
                if computed_score is not None:
                    computed_scores[title] = computed_score
                entry[f"{title}_computed"] = computed_score  #e con il valore normalizzato

        computed_scores_no0 = {k: v for k, v in computed_scores.items() if v > 0}#considera solo le emozioni con punteggio positivo
        top3 = sorted(computed_scores_no0.items(), key=lambda x: x[1], reverse=True)[:3] #prendo le 3 col punteggio più alto

        entry["main_emotion"] = [[name.split("-NRC")[0], f"{int(score*100)}%"]
            for name, score in top3
        ]
        entry["combined_emotions"] = sorted(found_emotions, key=lambda x: x["emotion"])  # Salviamo nella entry l'elenco delle emozioni complesse trovate, ordinandole alfabeticamente per nome

    with open(json_output_path, "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, indent=2, ensure_ascii=False)  # salviamo l'array data nel file di output


# Crea un sommario per ogni speaker
def summarize_speaker_emotions(annotated_json_path, output_json_path):  #Crea un sommario per ogni speaker: Parole totali, stopword, match. Somma punteggi per emozioni di base e complesse. Ritorna un JSON riepilogativo utile per analisi aggregate.
    with open(annotated_json_path, "r", encoding="utf-8") as infile:
        data = json.load(infile)

    speaker_summary = {}  #dizionario che raccoglierà le statistiche di ogni speaker

    for entry in data:
        # Per ogni entry del json in input (quello gia lavorato dalle funzioni precedenti) annota a i campi
        speaker = entry.get("speaker", "Unknown")
        word_count = entry.get("word_count", 0)
        stop_word_count = entry.get("stop_word_count", 0)
        match_count = entry.get("occurrences_count", 0)
        combined_emotions = entry.get("combined_emotions", [])

        if speaker not in speaker_summary:  # Se è la prima occorrenza di questo speaker, inizializza il suo record riassuntivo.
            speaker_summary[speaker] = {
                "speaker": speaker,
                "total_words": 0,
                "total_stop_words": 0,
                "total_matches": 0,
                "total_entries": 0,
                "basic_emotions": defaultdict(float),
                "complex_emotions": defaultdict(float)
            }
        #altrimenti la aggiorna
        summary = speaker_summary[speaker]
        summary["total_words"] += word_count
        summary["total_stop_words"] += stop_word_count
        summary["total_matches"] += match_count
        summary["total_entries"] += 1

        # Accumulate basic emotions
        for genre in all_genres:
            summary["basic_emotions"][genre] += entry.get(genre, 0.0)

        # Accumulate complex emotions
        for emotion in combined_emotions:
            emotion_name = emotion["emotion"]
            for word_info in emotion["matched_words"]:
                score = word_info.get("score", 0.0)
                summary["complex_emotions"][emotion_name] += score

    result = []  #Crea il dizionario da restituire in output
    for speaker, values in speaker_summary.items():
        entry = {  #crea un'entry per ogni speaker inserendo le sue statistiche
            "speaker": values["speaker"],
            "total_words": values["total_words"],
            "total_stop_words": values["total_stop_words"],
            "total_matches": values["total_matches"],
            "total_entries": values["total_entries"]
        }

        computed_scores = {}

        # Add basic emotions and computed scores
        for genre, score_sum in values["basic_emotions"].items():
            raw_key = f"{genre}_sum"
            avg_key = f"{genre}_computed"
            entry[raw_key] = round(score_sum, 4)
            computed_value = compute_function_for_basics_and_complex_emotions(score_sum, values["total_words"], values["total_stop_words"])
            entry[avg_key] = computed_value
            if computed_value is not None:
                computed_scores[genre] = computed_value

        # Add complex emotions and computed scores
        for emotion_name, score_sum in values["complex_emotions"].items():
            raw_key = f"{emotion_name}_sum"
            avg_key = f"{emotion_name}_computed"
            entry[raw_key] = round(score_sum, 4)
            computed_value = (compute_function_for_basics_and_complex_emotions(score_sum, values["total_words"], values["total_stop_words"]))
            entry[avg_key] = computed_value
            if computed_value is not None:
                computed_scores[emotion_name] = computed_value

        # Determina main_emotion (quella con il valore computato maggiore)
        computed_scores_no0 = {k: v for k, v in computed_scores.items() if v > 0}#considera solo le emozioni con punteggio positivo
        top3 = sorted(computed_scores_no0.items(), key=lambda x: x[1], reverse=True)[:3] #prendo le 3 col punteggio più alto

        entry["main_emotion"] = [
            name.split("-NRC")[0]
            for name, score in top3
        ]
        result.append(entry)  #mette la entry nel dizionario

    with open(output_json_path, "w", encoding="utf-8") as outfile:
        json.dump(result, outfile, indent=2, ensure_ascii=False)  #mette il dizionario nel file di output
    print(f"Speaker emotion summary written to '{output_json_path}'")


def summarize_conversation(annotated_json_path, output_json_path):
    with open(annotated_json_path, "r", encoding="utf-8") as infile:
        data = json.load(infile)

    conv_summary = {
        "speaker": [],
        "total_words": 0,
        "total_stop_words": 0,
        "total_matches": 0,
        "total_entries": 0,
        "basic_emotions": defaultdict(float),
        "complex_emotions": defaultdict(float)
    }

    for entry in data:
        speaker = entry.get("speaker", "Unknown")
        word_count = entry.get("word_count", 0)
        stop_word_count = entry.get("stop_word_count", 0)
        match_count = entry.get("occurrences_count", 0)
        combined_emotions = entry.get("combined_emotions", [])

        #aggiorna
        if speaker not in conv_summary["speaker"]:
            conv_summary["speaker"].append(speaker)
        conv_summary["total_words"] += word_count
        conv_summary["total_stop_words"] += stop_word_count
        conv_summary["total_matches"] += match_count
        conv_summary["total_entries"] += 1

        # Accumulate basic emotions
        for genre in all_genres:
            conv_summary["basic_emotions"][genre] += entry.get(genre, 0.0)

        # Accumulate complex emotions
        for emotion in combined_emotions:
            emotion_name = emotion["emotion"]
            for word_info in emotion["matched_words"]:
                score = word_info.get("score", 0.0)
                conv_summary["complex_emotions"][emotion_name] += score


    computed_scores = {}

    # Basic emotions
    for genre, score_sum in conv_summary["basic_emotions"].items():
        computed_score = compute_function_for_basics_and_complex_emotions(
            score_sum,
            conv_summary["total_words"],
            conv_summary["total_stop_words"]
        )
        if computed_score is not None:
            computed_scores[genre] = computed_score

    # Complex emotions
    for emotion, score_sum in conv_summary["complex_emotions"].items():
        computed_score = compute_function_for_basics_and_complex_emotions(
            score_sum,
            conv_summary["total_words"],
            conv_summary["total_stop_words"]
        )
        if computed_score is not None:
            computed_scores[emotion] = computed_score

    # Emozioni principali
    computed_scores_no0 = {k: v for k, v in computed_scores.items() if v > 0}#considera solo le emozioni con punteggio positivo
    top3 = sorted(computed_scores_no0.items(), key=lambda x: x[1], reverse=True)[:3] #prendo le 3 col punteggio più alto

    conv_summary["main_emotion"] = [name.split("-NRC")[0]
        for name, score in top3
    ]
    conv_summary["computed_scores"] = computed_scores
    conv_summary["speaker"] = list(conv_summary["speaker"])  # converti in lista per JSON

    # Scrivi su file
    with open(output_json_path, "w", encoding="utf-8") as outfile:
        json.dump(conv_summary, outfile, indent=2, ensure_ascii=False)

    print(f"Conversation summary written to '{output_json_path}'")


def find_words(json_input_path, json_combined_output_path, speaker_summary_json, conv_summary_json):
    # === PARAMETRI DI ANALISI ===
    threshold = 0.0 #  - threshold: soglia minima di score per considerare una corrispondenza valida
    ignore_words = [] #  - ignore_words: lista di parole da ignorare (es. parole custom)
    hide_zero_basics = True #  - hide_zero_basics: flag che decide se nascondere i generi a punteggio 0

    # 1. Controlla che esistano i file/cartelle
    if not os.path.exists(json_input_path):
        print(f"Errore: file {json_input_path} non trovato!")
        return
    if not os.path.exists(genre_folder):
        print(f"Errore: cartella {genre_folder} non trovata!")
        return

    # Annotazione JSON con emozioni base + complesse
    annotate_json_with_all(json_input_path, json_combined_output_path, threshold, ignore_words, hide_zero_basics)
    print(f"JSON annotato salvato in '{json_combined_output_path}'.")

    # Riassunto per speaker
    summarize_speaker_emotions(json_combined_output_path, speaker_summary_json)
    print(f"Statistiche per speaker salvate in '{speaker_summary_json}'.")

    # Riassunto conversazione
    summarize_conversation(json_combined_output_path, conv_summary_json)
    print(f"Statistiche per speaker salvate in '{conv_summary_json}'.")


input_folder = "json" #richiede una directory con al suo interno uno o più files json (non è necessario saper il numero a priori)
output_folder = "output"

#per ogni file in input chiama find_words
for j in os.listdir(input_folder):
    input_path = os.path.join(input_folder, j)
    base_name = os.path.splitext(j)[0]  # rimuove estensione

    # cartella di output per questo file
    output_subfolder = os.path.join(output_folder, base_name)
    os.makedirs(output_subfolder, exist_ok=True)

    out_file = os.path.join(output_folder, f"{base_name}/out_{base_name}.json")
    speaker_file = os.path.join(output_folder, f"{base_name}/speaker_out_{base_name}.json")
    conv_file = os.path.join(output_folder, f"{base_name}/conv_sum_{base_name}.json")

    # crea file vuoti
    with open(out_file, "w", encoding="utf-8"):
        pass
    with open(speaker_file, "w", encoding="utf-8"):
        pass
    with open(conv_file, "w", encoding="utf-8"):
        pass

    # chiama la funzione con i percorsi corretti
    find_words(input_path, out_file, speaker_file, conv_file)



