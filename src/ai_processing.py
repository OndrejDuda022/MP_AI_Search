"""Backend module for AI processing: generating search queries and summarizing results with AI."""
import os
import requests
import json
import re
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Dict

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
#parameters: user_input (str) - raw user question, language (str) - desired language for queries, max_input_length (int) - max length of user input
#returns: List[str] - list of generated search queries
def generate_search_queries(user_input, language="auto", max_input_length=500) -> List[str]:
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        raise ValueError("[!] Missing AI API key in environment variables. Cannot generate search queries.")

    company = os.getenv("TARGET_DOMAIN")
    url = os.getenv("AI_URL")
    if not company or not url:
        raise ValueError("[!] Missing TARGET DOMAIN or AI URL in environment variables. Cannot generate search queries.")
    
    #sanitize and limit user input
    user_input = sanitize_user_input(user_input)
    user_input = user_input[:max_input_length]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    lang_map = {
        "cs": "Generate all queries in Czech language.",
        "en": "Generate all queries in English language.",
        "sk": "Generate all queries in Slovak language.",
        "auto": "Generate queries in the same language as the user input (Czech if user writes in Czech, English if English, etc.)."
    }
    lang_instruction = lang_map.get(language, lang_map["auto"])
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are an expert search query generator for {company}'s AI search system. "
                    f"Your task is to transform user questions into effective Google search queries.\n\n"
                    
                    f"## CORE RULES:\n"
                    f"1. Generate 2-4 diverse queries targeting DIFFERENT information angles\n"
                    f"2. Always include '{company}' in each query (unless already present)\n"
                    f"3. Use natural language phrases that appear on real websites\n"
                    f"4. Think like a search engine: use terms from page titles, headings, meta descriptions\n"
                    f"5. {lang_instruction}\n\n"
                    
                    f"## EFFECTIVE QUERY PATTERNS:\n"
                    f"Different information sources: official page, contact page, about page, FAQ\n"
                    f"Related context: location-based, service-based, category-based\n\n"
                    
                    f"## QUERY GENERATION EXAMPLES:\n"
                    f"User: 'Do you have branch offices?'\n"
                    f"→ ['{company} branches contact',  # Official contact info\n"
                    f"    '{company} where to find us',  # Natural FAQ phrase\n"
                    f"    '{company} branch network map']  # Geographic coverage\n\n"
                    
                    f"User: 'What are your opening hours?'\n"
                    f"→ ['{company} opening hours',     # Direct term\n"
                    f"    '{company} weekend hours',      # Specific aspect\n"
                    f"    '{company} contact working hours']  # Contact page context\n\n"
                    
                    f"User: 'pricing for premium plan'\n"
                    f"→ ['{company} pricing premium plan',   # Pricing page term\n"
                    f"    '{company} premium price monthly',  # Specific detail\n"
                    f"    '{company} premium package cost']  # Natural question\n\n"
                    
                    f"User: 'How do I contact support?'\n"
                    f"→ ['{company} customer support',  # Official support page\n"
                    f"    '{company} technical help email',      # Specific channel\n"
                    f"    '{company} helpdesk chat']              # Alternative channel\n\n"
                    
                    f"## APPROPRIATENESS CHECK:\n"
                    f"Mark as INAPPROPRIATE (is_appropriate=false) if the input:\n"
                    f"- Requests personal/confidential data (passwords, private info, internal documents)\n"
                    f"- Contains illegal/harmful content (hacking, violence, discrimination)\n"
                    f"- Asks for technical internals (SQL queries, API keys, source code)\n"
                    f"- Is completely off-topic, irrelevant to {company} or spam\n\n"
                    f"Mark as APPROPRIATE (is_appropriate=true) if the input:\n"
                    f"- Asks about company info, products, services, contact details\n"
                    f"- Seeks public information (pricing, locations, support)\n"
                    f"- Is a general customer inquiry\n\n"
                    
                    f"## SPECIAL CASES:\n"
                    f"- If input is already a search query (keywords only), use it as-is and add 1-2 variations\n"
                    f"- If question has multiple sub-questions, generate queries for each part\n"
                    f"- For vague questions, create broader queries to capture relevant results"
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
                            "description": "List of search queries"
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

    print("[*] Sending request to AI API for queries...")
    response = requests.post(url, headers=headers, json=payload)
    try:
        response.raise_for_status()
        result_content = response.json()["choices"][0]["message"]["content"]
        parsed_result = SearchQueries(**json.loads(result_content))
    except Exception as e:
        print(f"[!] AI API request failed: {e}")
        try:
            print(f"Response content: {response.text[:500]}")
        except Exception:
            pass
        return []

    if not parsed_result.is_appropriate:
        print(f"[!] Inappropriate input detected: {parsed_result.reason}")
        return None
    
    return parsed_result.queries

#generate queries optimized for local vector database search
#parameters: user_input (str) - user question, language (str) - language preference, max_input_length (int) - max input length
#returns: List[str] - list of keyword-based queries for semantic search
def generate_local_db_queries(user_input, language="auto", max_input_length=500) -> List[str]:
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        raise ValueError("[!] Missing AI API key in environment variables. Cannot generate search queries.")

    url = os.getenv("AI_URL")
    if not url:
        raise ValueError("[!] Missing AI URL in environment variables. Cannot generate search queries.")
    
    #sanitize and limit user input
    user_input = sanitize_user_input(user_input)
    user_input = user_input[:max_input_length]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    lang_map = {
        "cs": "Generate all queries in Czech language.",
        "en": "Generate all queries in English language.",
        "sk": "Generate all queries in Slovak language.",
        "auto": "Generate queries in the same language as the user input (Czech if user writes in Czech, English if English, etc.)."
    }
    lang_instruction = lang_map.get(language, lang_map["auto"])
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are an expert at extracting search terms for vector database semantic search.\n\n"
                    
                    f"## YOUR TASK:\n"
                    f"Transform user questions into keyword-rich queries that match document content.\n\n"
                    
                    f"## VECTOR DATABASE CHARACTERISTICS:\n"
                    f"- Documents are SHORT (1-3 sentences) factual chunks\n"
                    f"- Content uses natural descriptive language\n"
                    f"- No company names in documents (generic content)\n"
                    f"- Semantic search finds similar MEANING, not exact keywords\n\n"
                    
                    f"## QUERY GENERATION RULES:\n"
                    f"1. Extract KEY TOPICS and CONCEPTS from the question\n"
                    f"2. Generate 2-4 different semantic angles\n"
                    f"3. Use NATURAL LANGUAGE that appears in informational text\n"
                    f"4. DO NOT include company/domain names\n"
                    f"5. Think: 'What words would be IN the answer document?'\n"
                    f"6. {lang_instruction}\n\n"
                    
                    f"## EFFECTIVE PATTERNS:\n\n"
                    
                    f"### Example 1:\n"
                    f"User: 'Jaké studijní obory nabízíte?'\n"
                    f"→ ['studijní obory',\n"
                    f"    'maturitní obory technické vzdělávání',\n"
                    f"    'nabídka oborů studium']\n\n"
                    
                    f"### Example 2:\n"
                    f"User: 'How do I contact you?'\n"
                    f"→ ['contact information email phone',\n"
                    f"    'communication secretariat office',\n"
                    f"    'contact details']\n\n"
                    
                    f"### Example 3:\n"
                    f"User: 'Kdy jsou přijímací zkoušky?'\n"
                    f"→ ['přijímací řízení termíny',\n"
                    f"    'přihlášky kritéria zkouška',\n"
                    f"    'školní rok přijetí studium']\n\n"
                    
                    f"### Example 4:\n"
                    f"User: 'Do you offer internships abroad?'\n"
                    f"→ ['internships abroad international',\n"
                    f"    'Erasmus study abroad opportunities',\n"
                    f"    'foreign work experience students']\n\n"
                    
                    f"## BAD vs GOOD:\n"
                    f"BAD: 'pslib.cz contact hours' (company name, web search style)\n"
                    f"GOOD: 'opening hours contact office' (descriptive terms)\n\n"
                    
                    f"BAD: 'liberec school IT program' (location-specific)\n"
                    f"GOOD: 'information technology study program' (generic, descriptive)\n\n"
                    
                    f"## APPROPRIATENESS:\n"
                    f"Same rules as web search - mark inappropriate if asking for private data, harmful content, etc."
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
                            "description": "List of keyword-based semantic search queries"
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

    print("[*] Generating local DB queries...")
    response = requests.post(url, headers=headers, json=payload)
    try:
        response.raise_for_status()
        result_content = response.json()["choices"][0]["message"]["content"]
        parsed_result = SearchQueries(**json.loads(result_content))
    except Exception as e:
        print(f"[!] AI API request failed: {e}")
        try:
            print(f"Response content: {response.text[:500]}")
        except Exception:
            pass
        return []

    if not parsed_result.is_appropriate:
        print(f"[!] Inappropriate input detected: {parsed_result.reason}")
        return None
    return parsed_result.queries

#process data with AI to generate structured response
#parameters: data (List[Dict]) - list of source data dictionaries, user_query (str) - user question, language (str) - desired language
#returns: AIResponse - structured AI response
def process_with_ai(data, user_query="", language="auto"):
    api_key = os.getenv("AI_API_KEY")

    if not api_key:
        raise ValueError("[!] Missing AI API key in environment variables. Cannot request AI processing.")
    
    company = os.getenv("TARGET_DOMAIN")
    url = os.getenv("AI_URL")
    if not company or not url:
        raise ValueError("[!] Missing TARGET DOMAIN or AI URL in environment variables. Cannot request AI processing.")

    #sanitize user query
    user_query = sanitize_user_input(user_query)

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
    
    formatted_data = format_sources(data)
    
    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are {company}'s AI assistant. Your role is to provide accurate, helpful answers based solely on the provided sources.\n\n"
                    
                    f"## YOUR TASK:\n"
                    f"Analyze the sources and answer the user's question with precision and clarity.\n\n"
                    
                    f"## ANSWER GUIDELINES:\n"
                    f"1. **Use ONLY information from the provided sources** - never add external knowledge\n"
                    f"2. **Cite sources** using format '[Source X]' when referencing specific information\n"
                    f"3. **Be concise** - provide direct answers, avoid unnecessary elaboration\n"
                    f"4. **Be honest** - if sources don't contain the answer, clearly state this\n"
                    f"5. {lang_instruction}\n"
                    
                    f"## KEY POINTS EXTRACTION:\n"
                    f"- Extract 3-5 key points (fewer if information is limited, more only if critical)\n"
                    f"- Include relevant numbers, dates, or specifics when available\n\n"
                    
                    f"## CONFIDENCE ASSESSMENT:\n"
                    f"Set confidence level based on:\n"
                    f"- **HIGH**: Multiple sources confirm the answer, information is detailed and recent\n"
                    f"- **MEDIUM**: Answer found but limited sources, some gaps in information, or slightly outdated\n"
                    f"- **LOW**: Minimal relevant information, sources tangentially related, or conflicting data\n\n"
                    
                    f"## HANDLING EDGE CASES:\n"
                    f"- **Conflicting sources**: Mention both viewpoints, cite each source, set confidence to MEDIUM or LOW\n"
                    f"- **No relevant info**: State clearly 'The provided sources do not contain information about...'\n"
                    f"- **Partial answer**: Provide what you can, explicitly note what's missing\n"
                    f"- **Outdated info**: Mention if sources appear old, adjust confidence accordingly\n\n"
                    
                    f"## SOURCES_USED FIELD:\n"
                    f"Include only the URLs of sources you actually referenced in your answer (not all provided sources)."
                )
            },
            {
                "role": "user",
                "content": f"## AVAILABLE SOURCES:\n{formatted_data}\n\n## USER QUESTION:\n{user_query}"
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

    print("[*] Sending request to AI API for summarization...")
    response = requests.post(url, headers=headers, json=payload)
    try:
        response.raise_for_status()
        result_content = response.json()["choices"][0]["message"]["content"]
        parsed_result = AIResponse(**json.loads(result_content))
    except Exception as e:
        print(f"[!] AI API request failed: {e}")
        try:
            print(f"Response content: {response.text[:500]}")
        except Exception:
            pass
        return AIResponse(
            summary="Error processing data with AI API.",
            key_points=[],
            sources_used=[],
            confidence="low"
        )
    
    return parsed_result

#format structured data for AI consumption
#parameters: data_list (List[Dict]) - list of source data dictionaries
#returns: str - formatted string representation of sources
def format_sources(data_list: List[Dict]) -> str:
    formatted_sources = []
    
    for idx, source in enumerate(data_list, 1):
        content = source.get('content', '')
        
        # Sanitize scraped content
        content = sanitize_scraped_content(content)
        
        formatted_sources.append(
            f"[Source {idx}]\n"
            f"URL: {source.get('url', 'Unknown')}\n"
            f"Title: {source.get('title', 'Untitled')}\n"
            f"Type: {source.get('type', 'unknown')}\n"
            f"Content Length: {source.get('length', 0)} characters\n"
            f"Content:\n{content}\n"
            f"{'=' * 80}\n"
        )
    
    return "\n".join(formatted_sources)

#sanitize user input
#parameters: text (str) - raw user input
#returns: str - sanitized user input
def sanitize_user_input(text: str) -> str:
    if not text:
        return ""
    
    #remove control characters
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    #remove common injection patterns
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    
    #normalize whitespace
    text = ' '.join(text.split())
    
    return text.strip()

#sanitize scraped content
#parameters: text (str) - raw scraped content
#returns: str - sanitized content
def sanitize_scraped_content(text: str) -> str:
    if not text:
        return ""
    
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    #remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    #remove common noise patterns
    text = re.sub(r'(cookies?|gdpr|privacy policy)\s+(accept|consent|agree)', '', text, flags=re.IGNORECASE)
    
    return text.strip()