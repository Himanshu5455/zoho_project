import json
import requests
from datetime import datetime

TOKEN_FILE = "zoho_to.json"

def generate_and_save_tokens(client_id, client_secret, authorization_code):
    """Generate access and refresh tokens and save them in a JSON file."""
    url = "https://accounts.zoho.com/oauth/v2/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": authorization_code,
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        tokens = response.json()
        save_tokens(tokens)
        print("Tokens generated and saved successfully.")
    except requests.RequestException as e:
        print(f"Error generating tokens: {e}")

def save_tokens(tokens):
    """Save tokens to a JSON file."""
    tokens['saved_at'] = datetime.now().isoformat()
    with open(TOKEN_FILE, "w") as file:
        json.dump(tokens, file, indent=2)

# Example usage:
generate_and_save_tokens(
    client_id="1000.KMW1Y9M7PKFO1SFJ7DEFPTE49TDN4U",
    client_secret="80d5a5aa081fa202c4c59c13fc7f3f26bddf5d0307",
    authorization_code="1000.5b015a786d21b521e6efb263a61cc085.cf1f54d076755a313f2db2dd7b3050a0"
)