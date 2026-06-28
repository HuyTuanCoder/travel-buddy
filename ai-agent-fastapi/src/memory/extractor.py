import logging
from src.schemas.memory import ExtractedFact
import json

from src.core.config import get_llm

logger = logging.getLogger(__name__)

def extract_from_messages(new_messages: list[str], current_facts: list[dict] = None) -> list[ExtractedFact]:
    """
    Pure LLM-based memory synthesizer.
    Passes the new conversational messages and current known facts to the LLM
    to generate an updated list of precise ExtractedFacts.
    """
    if not new_messages:
        return []
        
    facts = _llm_extraction(new_messages, current_facts)
    return facts

def _llm_extraction(new_messages: list[str], current_facts: list[dict] = None) -> list[ExtractedFact]:
    """
    Uses structured output via the default configured LLM to strictly parse complex facts.
    """
    # Use default model (e.g. vertex-ai gemini or google ai studio), fallback is handled in get_llm
    llm = get_llm(model_name="gemini-1.5-flash", temperature=0)
    
    # Force the LLM to output a list of ExtractedFact JSONs
    structured_llm = llm.with_structured_output(list[ExtractedFact])
    
    combined_new_messages = " ".join(new_messages)
    facts_context = json.dumps(current_facts) if current_facts else "No existing facts."
    
    prompt = f"""
    You are an expert travel assistant memory extractor.
    Your job is to read new conversational messages and extract key preferences and facts.
    
    Here is what you CURRENTLY know about the user:
    {facts_context}
    
    Here are the NEW messages from the conversation:
    {combined_new_messages}
    
    Instructions:
    1. Extract new facts, preferences, constraints (budget, dietary, group size, pace, etc.).
    2. If a new message contradicts an old fact (e.g. user was vegan, but now says they eat meat), extract the updated fact so it overwrites the old one.
    3. If it's a permanent dietary, accessibility, or budget constraint, mark permanence as PERMANENT.
    4. If it's a passing thought or specific only to this trip, mark it TEMPORARY.
    5. Return ONLY the JSON array of ExtractedFact objects. If nothing important is found, return an empty array.
    """
    
    logger.info(f"Extracting memory from {len(new_messages)} new messages using pure LLM...")
    facts = structured_llm.invoke(prompt)
    # Ensure it's a list even if LLM returns None
    return facts if facts else []
