import os
import requests
import json
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
def generate_search_queries(user_input, language="auto"):
    api_key = os.getenv("AI_API_KEY")
    company = os.getenv("TARGET_DOMAIN")

    if not api_key:
        raise ValueError("[!] Missing AI API key in environment variables. Cannot generate search queries.")

    url = "https://chetty-api.mateides.com/chat/completions"
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
                    f"4. Combine specific + broad keywords for comprehensive coverage\n"
                    f"5. Think like a search engine: use terms from page titles, headings, meta descriptions\n"
                    f"6. {lang_instruction}\n\n"
                    
                    f"## EFFECTIVE QUERY PATTERNS:\n"
                    f"Different information sources: official page, contact page, about page, FAQ\n"
                    f"Different keyword types: formal terms, colloquial phrases, action words\n"
                    f"Different specificity levels: broad category, specific feature, detailed attribute\n"
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
                    f"→ ['{company} customer support contact',  # Official support page\n"
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
        print(f"[!] Inappropriate input detected: {parsed_result.reason}")
        return None
    
    return parsed_result.queries

#format structured data for AI consumption
def format_sources(data_list: List[Dict], max_content_length: int = 3000) -> str:
    formatted_sources = []
    
    for idx, source in enumerate(data_list, 1):
        content = source.get('content', '')
        if len(content) > max_content_length:
            content = content[:max_content_length] + "... [content truncated]"
        
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

#process data with AI to generate structured response
def process_with_ai(data, user_query="", language="auto", format="text"):
    api_key = os.getenv("AI_API_KEY")
    company = os.getenv("TARGET_DOMAIN")

    if not api_key:
        raise ValueError("[!] Missing AI API key in environment variables. Cannot request AI processing.")

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
    
    formatted_data = format_sources(data)
    
    #detect if we're working with HTML structured content
    if format == "html":
        html_instruction = {
            "\n\n## CONTENT FORMAT:\n"
            "The source content is provided as cleaned HTML with semantic structure preserved.\n"
            "- Use HTML tags (h1-h6, ul, ol, table, etc.) to understand information hierarchy\n"
            "- Pay attention to headings for main topics and structure\n"
            "- Tables contain structured data - extract them carefully\n"
            "- Links (<a>) show relationships between topics\n"
        }
    else:
        html_instruction = ""
    
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
                    f"{html_instruction}\n"
                    
                    f"## KEY POINTS EXTRACTION:\n"
                    f"- Extract 3-5 key points (fewer if information is limited, more only if critical)\n"
                    f"- Prioritize: direct answers > supporting details > context\n"
                    f"- Each key point should be specific and actionable\n"
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
    response.raise_for_status()
    
    result_content = response.json()["choices"][0]["message"]["content"]
    
    parsed_result = AIResponse(**json.loads(result_content))
    
    return parsed_result