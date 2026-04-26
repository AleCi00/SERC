def translate_emotions(input_file, output_file):
    # Mappatura numeri -> emozioni
    emotion_map = {
        '0': 'no_emotion',
        '1': 'anger',
        '2': 'disgust',
        '3': 'fear',
        '4': 'happiness',
        '5': 'sadness',
        '6': 'surprise'
    }

    with open(input_file, 'r', encoding='utf-8') as f_in:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                line = line.strip()

                # Split per spazio per ottenere i singoli numeri
                emotions = line.split()

                # Traduci ogni numero in parola
                translated = [emotion_map.get(num, num) for num in emotions]

                # Scrivi la riga tradotta
                f_out.write(' '.join(translated) + '\n')


translate_emotions("dialogues/dailydialog_emotion_test.txt", "dialogues/dailydialog.txt")