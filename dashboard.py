from flask import Flask, jsonify, render_template
import json
import os

app = Flask(__name__)

# --- Ścieżki do plików JSON ---
LEVELS_FILE = 'levels.json'
USER_DATA_FILE = 'user_data.json'
PATIENT_CARDS_FILE = 'patient_cards.json'
EMPLOYEE_CARDS_FILE = 'employee_cards.json'
ECONOMY_FILE = 'economy.json'

# --- Funkcje wczytujące dane ---
def load_json_file(file_path):
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    levels_data = load_json_file(LEVELS_FILE)
    user_data = load_json_file(USER_DATA_FILE)
    patient_cards = load_json_file(PATIENT_CARDS_FILE)
    employee_cards = load_json_file(EMPLOYEE_CARDS_FILE)
    economy_data = load_json_file(ECONOMY_FILE)

    # Przetwarzanie danych do wykresów
    # Poziomy
    sorted_levels = sorted(levels_data.items(), key=lambda item: item[1].get('xp', 0), reverse=True)
    top_10_levels = {k: v for k, v in sorted_levels[:10]}

    # Kary
    sentences_by_type = {}
    for user_id, data in user_data.items():
        for sentence in data.get('sentences', []):
            kara_type = sentence.get('rodzaj_kary')
            sentences_by_type[kara_type] = sentences_by_type.get(kara_type, 0) + 1
            
    # Ostrzeżenia
    warnings_by_level = {}
    for user_id, data in user_data.items():
        for warning in data.get('warnings', []):
            level = warning.get('level')
            warnings_by_level[level] = warnings_by_level.get(level, 0) + 1

    # Liczba kart
    card_counts = {
        "Pacjenci": len(patient_cards),
        "Pracownicy": len(employee_cards)
    }
    
    # Ekonomia (zakładając, że plik ma strukturę {user_id: {"balance": ...}})
    sorted_economy = sorted(economy_data.items(), key=lambda item: item[1].get('balance', 0), reverse=True)
    top_10_economy = {k: v for k, v in sorted_economy[:10]}

    data_for_charts = {
        'levels': top_10_levels,
        'sentences': sentences_by_type,
        'warnings': warnings_by_level,
        'cards': card_counts,
        'economy': top_10_economy,
    }
    return jsonify(data_for_charts)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
