import json
import re


#da adattare al proprio database

def parse_dialogues1(file_path):
    conversations = []
    buffer = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # separatore di conversazione
            if re.fullmatch(r'-[^-]+-', line.strip()):
                if buffer:
                    conversations.append(buffer)
                    buffer = []
            elif line:  # riga con messaggio
                if '[' in line and ']:' in line:
                    speaker, text = line.split(']:', 1)
                    speaker = speaker.strip('[').strip()
                    text = text.strip()
                    msg = {
                        "speaker": speaker,
                        "text": text
                    }
                    buffer.append(msg)

        # aggiungi l'ultima conversazione se rimasta in buffer
        if buffer:
            conversations.append(buffer)

    return conversations


# Esegui il parsing del file

convs = parse_dialogues1("dialogues/Annie's_chat_archive.txt")
# Salvataggio in JSON
for i in range(len(convs)):
    filename = f"json/conversation_Annie{i+1}.json"   # nome file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(convs[i], f, indent=2, ensure_ascii=False)