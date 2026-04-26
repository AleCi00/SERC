import json


#da adattare al proprio database

def parse_dialogues1(file_path):
    conversations = []
    buffer = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # separatore di conversazione
            if line == "-----------":
                if buffer:
                    conversations.append(buffer)
                    buffer = []
            elif line:  # riga con messaggio
                if ':' in line:
                    speaker, text = line.split(':', 1)
                    msg = {
                        "speaker": speaker.strip(),
                        "text": text.strip()
                    }
                    buffer.append(msg)

        # aggiungi l'ultima conversazione se rimasta in buffer
        if buffer:
            conversations.append(buffer)

    return conversations


# Esegui il parsing del file

convs = parse_dialogues1("dialogues/dialogues1.txt")
# Salvataggio in JSON
for i in range(len(convs)):
    filename = f"json/conversation_1-{i+1}.json"   # nome file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(convs[i], f, indent=2, ensure_ascii=False)