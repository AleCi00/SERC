import json
#da adattare al proprio database

def parse_dialogues2(file_path):
    conversations = []
    buffer = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # separatore di conversazione
            if line == "eoc":
                if buffer:
                    conversations.append(buffer)
                    buffer = []
            elif line:  # riga con messaggio
                if '[' in line and ']' in line:
                    speaker, text = line.split(']', 1)
                    speaker = speaker.strip('[').strip()
                    text = text.strip()
                    msg = {
                        "speaker": speaker,
                        "text": text
                    }
                    buffer.append(msg)
        if buffer:
            conversations.append(buffer)

    return conversations



# Esegui il parsing del file

convs = parse_dialogues2("dialogues/dialogues2.txt")
# Salvataggio in JSON
for i in range(len(convs)):
    filename = f"json/conversation_2-{i+1}.json"   # nome file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(convs[i], f, indent=2, ensure_ascii=False)