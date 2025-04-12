import os
import json
import requests

TOKEN_FILE = "zoho_tokens.json"
client_id="1000.KMW1Y9M7PKFO1SFJ7DEFPTE49TDN4U"
client_secret="80d5a5aa081fa202c4c59c13fc7f3f26bddf5d0307"
REFRESH_TOKEN_URL ="https://accounts.zoho.com/oauth/v2/token"
ZOHO_API_URL = "https://www.zohoapis.com/crm/v2/Leads"

def load_tokens():
    """Load tokens from JSON file."""
    try:
        if not os.path.exists(TOKEN_FILE):
            print("Tokens file not found.")
            return None
        with open(TOKEN_FILE, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading tokens: {str(e)}")
        return None

def save_tokens(tokens):
    """Save tokens to JSON file."""
    try:
        with open(TOKEN_FILE, "w") as file:
            json.dump(tokens, file, indent=4)
    except Exception as e:
        print(f"Error saving tokens: {str(e)}")

def refresh_access_token():
    """Refresh access token using refresh token from the token file."""
    tokens = load_tokens()
    if not tokens:
        raise Exception("No tokens found. Please reauthorize.")

    refresh_token = tokens.get("refresh_token")

    if not client_id or not client_secret or not refresh_token:
        raise Exception("Missing client ID, client secret, or refresh token.")

    # Construct the URL with query parameters
    url = f"{REFRESH_TOKEN_URL}?refresh_token={refresh_token}&client_id={client_id}&client_secret={client_secret}&grant_type=refresh_token"

    # Send the request
    response = requests.post(url)

    if response.status_code == 200:
        new_tokens = response.json()
        tokens["access_token"] = new_tokens["access_token"]  # Update access token
        save_tokens(tokens)  # Save new access token
        return new_tokens["access_token"]
    else:
        raise Exception(f"Failed to refresh access token: {response.json()}")

def get_valid_access_token():
    """Get a valid access token, refreshing if necessary."""
    tokens = load_tokens()
    if not tokens:
        raise Exception("No tokens found. Please generate new tokens first.")

    access_token = tokens.get("access_token")
    
    # Test the access token
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    test_response = requests.get(ZOHO_API_URL, headers=headers)

    if test_response.status_code == 401:  # Invalid token (Unauthorized)
        print("Access token expired, refreshing...")
        return refresh_access_token()

    return access_token