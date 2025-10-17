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
    sources_used: int
    confidence: str

#generate search queries based on user input
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
                "role": "system",
                "content": (
                    "You are a search query generator. Analyze user input and generate up to 3 Google search queries. "
                    "Determine if the input is appropriate. Consider inappropriate: personal data, confidential information, "
                    "illegal activities, requests for backend internals (SQL, code snippets). "
                    "If input is already a well-formed search query (keywords, specific phrases, no complete sentences), "
                    "return it as the primary query and generate fewer alternatives if needed."
                )
            },
            {
                "role": "user",
                "content": f"Generate search queries for: {user_input}"
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
def process_with_ai(data, user_query=""):
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
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that answers user questions based on provided search results. "
                    "Answer the user's question clearly and concisely using only the information from the provided sources. "
                    "Extract key points relevant to the question, count how many sources you used, "
                    "and assess your confidence level based on the quality and relevance of the sources. "
                    "If the information is insufficient to answer the question, state this clearly."
                )
            },
            {
                "role": "user",
                "content": data
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
                            "type": "integer",
                            "description": "Number of sources used to generate the summary"
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