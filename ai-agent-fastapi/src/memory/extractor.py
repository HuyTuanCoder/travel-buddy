import spacy
import logging
from src.schemas.memory import ExtractedFact, FactCategory, PermanenceLevel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
import os

logger = logging.getLogger(__name__)

_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        logger.info("Loading spaCy ('en_core_web_sm')...")
        _nlp = spacy.load("en_core_web_sm")
    return _nlp

def extract_from_messages(messages: list[str]) -> list[ExtractedFact]:
    """
    The hybrid extraction pipeline.
    First pass: Zero-cost NER via spaCy.
    Second pass: Fallback to Gemini if complex intent is detected (e.g. 'hate', 'love').
    """
    nlp = get_nlp()
    facts = []
    
    # Combine messages into a single text block for context
    combined_text = " ".join(messages)
    doc = nlp(combined_text)
    
    # Detect complex verbs that indicate preference
    preference_verbs = {"hate", "love", "dislike", "prefer", "want", "need", "allergic"}
    complex_intent_detected = any(token.lemma_.lower() in preference_verbs for token in doc)
    
    if complex_intent_detected:
        logger.info("Complex intent detected. Falling back to LLM for extraction.")
        facts = _llm_extraction_fallback(combined_text)
    else:
        # Zero-cost NER extraction
        logger.info("Performing zero-cost spaCy NER extraction.")
        for ent in doc.ents:
            if ent.label_ == "GPE": # Geopolitical Entity (Location)
                facts.append(
                    ExtractedFact(
                        category=FactCategory.GENERAL_MEMORY,
                        topic=ent.text,
                        sentiment="NEUTRAL",
                        permanence=PermanenceLevel.TEMPORARY,
                        raw_quote=combined_text
                    )
                )
    return facts

def _llm_extraction_fallback(text: str) -> list[ExtractedFact]:
    """
    Uses structured output via Gemini to strictly parse complex facts.
    """
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0,
        api_key=os.getenv("GEMINI_API_KEY")
    )
    
    # Force the LLM to output a list of ExtractedFact JSONs
    structured_llm = llm.with_structured_output(list[ExtractedFact])
    
    prompt = f"""
    You are an expert travel assistant memory extractor.
    Extract key preferences and facts from the following user conversation.
    If it's a permanent dietary or budget constraint, mark it PERMANENT.
    If it's just a passing thought, mark it TEMPORARY.
    
    Conversation:
    {text}
    """
    
    try:
        facts = structured_llm.invoke(prompt)
        # Ensure it's a list even if LLM returns None
        return facts if facts else []
    except Exception as e:
        logger.error(f"LLM Extraction failed: {e}")
        return []
