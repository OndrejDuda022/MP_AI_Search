import os
import requests
from dotenv import load_dotenv

load_dotenv()

def process_with_ai(data):
    api_key = os.getenv("AI_API_KEY")

    if not api_key:
        raise ValueError("Missing AI API key in environment variables. Cannot request AI processing.")

    url = "https://chetty-api.mateides.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role": "user", "content": data}
        ]
    }

    timeout = 30 

    print("Sending request to AI API for summarization...")
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"].strip()

def generate_search_queries(user_input):
    api_key = os.getenv("AI_API_KEY")

    if not api_key:
        raise ValueError("Missing AI API key in environment variables. Cannot generate search queries.")

    url = "https://chetty-api.mateides.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Analyze the following user input and generate three appropriate google search queries with correct search request structure (e.g., keywords, specific phrases). "
                    f"If the input contains inappropriate or sensitive content, respond with 'inappropriate'."
                    f"As inappropriate input consider: personal data, confidential information, illegal activities, requests for inner backend page parts (e.g., SQL, code snippets)."
                    f"If the user input already is a well-formed search query, return it and do not generate the other two."
                    f"As a well-formed search query consider: specific phrases, keywords, no complete sentences."
                    f"User input: {user_input}"
                )
            }
        ]
    }

    print("Sending request to AI API for queries...")
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    result = response.json()["choices"][0]["message"]["content"].strip()

    if result.lower() == "inappropriate":
        return None

    return result.split("\n")[:3]