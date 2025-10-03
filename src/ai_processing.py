import os
import openai

def process_with_ai(data):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    if not openai.api_key:
        raise ValueError("Missing OpenAI API key in environment variables.")

    prompt = f"Analyze the following data and provide insights: {data}"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()

def generate_search_queries(user_input):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    if not openai.api_key:
        raise ValueError("Missing OpenAI API key in environment variables.")

    prompt = (
        f"Analyze the following user input and generate three appropriate search queries. "
        f"If the input contains inappropriate or sensitive content, respond with 'inappropriate': {user_input}"
    )
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150
    )
    result = response.choices[0].text.strip()

    if result.lower() == "inappropriate":
        return None

    return result.split("\n")[:3] 