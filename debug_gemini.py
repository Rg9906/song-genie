import requests
import json

# Test direct API call
api_key = "AIzaSyAf_1B4Ipta6N753Qu-w4HeEegKLRMUqOE"
url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"

headers = {
    "Content-Type": "application/json",
}

data = {
    "contents": [{
        "parts": [{
            "text": "Generate a short music question. Question:"
        }]
    }],
    "generationConfig": {
        "maxOutputTokens": 100,
        "temperature": 0.8
    }
}

response = requests.post(f"{url}?key={api_key}", headers=headers, json=data)
print("Status:", response.status_code)
print("Response:", json.dumps(response.json(), indent=2))
