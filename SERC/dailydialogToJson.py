import json


def parse_dialogues(file_path):
    conversations = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Salta righe vuote
            if not line:
                continue

            # Ogni riga è una conversazione
            messages = line.split('__eou__')

            conversation = []
            current_speaker = "speaker1"

            for msg in messages:
                msg = msg.strip()

                # Salta messaggi vuoti
                if not msg:
                    continue

                conversation.append({
                    "speaker": current_speaker,
                    "text": msg
                })

                # Alterna tra speaker1 e speaker2
                current_speaker = "speaker2" if current_speaker == "speaker1" else "speaker1"

            # Aggiungi la conversazione solo se contiene messaggi
            if conversation:
                conversations.append(conversation)

    return conversations


# Esegui il parsing del file

convs = parse_dialogues("dialogues/dailydialog_test.txt")
# Salvataggio in JSON
for i in range(len(convs)):
    filename = f"json/dailydialog{i+1}.json"   # nome file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(convs[i], f, indent=2, ensure_ascii=False)