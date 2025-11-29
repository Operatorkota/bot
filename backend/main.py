from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

# Set up CORS
origins = [
    "*",  # Allows all origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # In a real app, you might want to log this error
        return {}

@app.get("/api/patient_cards")
def get_all_patient_cards():
    return load_data('../patient_cards.json')

@app.get("/api/user_data")
def get_all_user_data():
    return load_data('../user_data.json')

@app.get("/api/patient_cards/{user_id}")
def get_patient_card(user_id: str):
    data = load_data('../patient_cards.json')
    if user_id in data:
        return data[user_id]
    raise HTTPException(status_code=404, detail="Patient card not found")

@app.get("/api/user_data/{user_id}")
def get_user_data(user_id: str):
    data = load_data('../user_data.json')
    if user_id in data:
        return data[user_id]
    raise HTTPException(status_code=404, detail="User data not found")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Discord Bot API"}
