import os
import requests
import json
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List

load_dotenv()

#structured output models
class SearchQueries(BaseModel):
    queries: List[str]
    is_appropriate: bool
    reason: str = ""

class AIResponse(BaseModel):
    summary: str 
    key_points: List[str]
    sources_used: List[str]
    confidence: str

#generate search queries based on user input
def generate_search_queries(user_input, language="auto"):
    api_key = os.getenv("AI_API_KEY")

    if not api_key:
        raise ValueError("Missing AI API key in environment variables. Cannot generate search queries.")

    url = "https://chetty-api.mateides.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    if language == "auto":
        lang_instruction = "Generate queries in the same language as the user input (Czech if user writes in Czech, English if English, etc.)."
    else:
        lang_map = {
            "cs": "Generate all queries in Czech language.",
            "en": "Generate all queries in English language.",
            "sk": "Generate all queries in Slovak language."
        }
        lang_instruction = lang_map.get(language, "Generate queries in the same language as the user input.")
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a search query generator employed in the AI search tool of the company as4u.cz s.r.o." 
                    "Analyze user input and generate up to 3 Google search queries in correlation with as4u.cz." 
                    "(e.g., 'Do you have any branch offices?' -> 'as4u branch offices', 'as4u contact information', etc.) "
                    "Determine if the input is appropriate. Consider inappropriate: personal data, confidential information, "
                    "illegal activities, requests for backend internals (SQL, code snippets). "
                    "If input is already a well-formed search query (keywords, specific phrases, no complete sentences), "
                    "return it as the primary query and generate fewer alternatives if needed. "
                    f"{lang_instruction}"
                )
            },
            {
                "role": "user",
                "content": user_input
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "search_queries",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "queries": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of 1-3 search queries"
                        },
                        "is_appropriate": {
                            "type": "boolean",
                            "description": "Whether the input is appropriate for searching"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason if inappropriate, empty otherwise"
                        }
                    },
                    "required": ["queries", "is_appropriate", "reason"],
                    "additionalProperties": False
                }
            }
        }
    }

    print("Sending request to AI API for queries...")
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    """TO BE REMOVED
    #save response content as json for debugging
    output_file = "debug/debug_generated_search_queries_response.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(response.json(), f, ensure_ascii=False, indent=4)
    """  

    result_content = response.json()["choices"][0]["message"]["content"]
    
    parsed_result = SearchQueries(**json.loads(result_content))
    
    if not parsed_result.is_appropriate:
        print(f"Inappropriate input detected: {parsed_result.reason}")
        return None
    
    return parsed_result.queries[:3]  #max 3 queries

#process data with AI to generate structured response
def process_with_ai(data, user_query="", language="auto"):
    api_key = os.getenv("AI_API_KEY")

    if not api_key:
        raise ValueError("Missing AI API key in environment variables. Cannot request AI processing.")

    url = "https://chetty-api.mateides.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    language_instructions = {
        "auto": "IMPORTANT: Detect the language from the user query and respond in that language. All text in summary and key_points must be in the detected language.",
        "cs": "IMPORTANT: Always respond in Czech language (česky). All text in summary and key_points must be in Czech.",
        "en": "IMPORTANT: Always respond in English. All text in summary and key_points must be in English.",
        "sk": "IMPORTANT: Always respond in Slovak language (slovensky). All text in summary and key_points must be in Slovak."
    }
    
    lang_instruction = language_instructions.get(language, language_instructions["auto"])
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant of the company as4u.cz s.r.o. that answers user questions based on provided data from as4u.cz domain. "
                    "Answer the user's question clearly and concisely using only the information from the provided sources. "
                    "Extract key points relevant to the question, count how many sources you used, "
                    "and assess your confidence level based on the quality and relevance of the sources. "
                    "If the information is insufficient to answer the question, state this clearly. "
                    f"{lang_instruction}\n\n"
                    f"Available sources:\n{data}"
                )
            },
            {
                "role": "user",
                "content": user_query
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "ai_response",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "Direct answer to the user's question based on the provided sources"
                        },
                        "key_points": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of 3-5 key points that support the answer or are relevant to the question"
                        },
                        "sources_used": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of source URLs used to generate the summary"
                        },
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low"],
                            "description": "Confidence level in the answer based on source quality"
                        }
                    },
                    "required": ["summary", "key_points", "sources_used", "confidence"],
                    "additionalProperties": False
                }
            }
        }
    }

    print("Sending request to AI API for summarization...")
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    result_content = response.json()["choices"][0]["message"]["content"]
    
    parsed_result = AIResponse(**json.loads(result_content))
    
    return parsed_result