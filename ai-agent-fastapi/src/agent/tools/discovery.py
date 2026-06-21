import os
import requests
import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from duckduckgo_search import DDGS
import googlemaps
from langchain_core.messages import SystemMessage, HumanMessage
import grpc
from src.generated import location_pb2
from src.generated import location_pb2_grpc
from src.core.config import settings, get_llm

logger = structlog.get_logger(__name__)

# --- Search Web Tool ---
class SearchWebArgs(BaseModel):
    query: str = Field(description="The search query to look up on the internet. E.g. 'Opening hours for Louvre Museum 2024'")

@tool("search_web", args_schema=SearchWebArgs)
def search_web(query: str) -> str:
    """
    Call this tool when you need to search the internet for real-time information, 
    such as current opening hours, reviews, or new locations that are not in your training data.
    """
    logger.info(f"Discovery Tool: Searching web for '{query}'...")
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return "No search results found."
            
        formatted_results = "Search Results:\n"
        for i, res in enumerate(results):
            formatted_results += f"[{i+1}] {res.get('title', 'No Title')}\n"
            formatted_results += f"URL: {res.get('href', 'No URL')}\n"
            formatted_results += f"Snippet: {res.get('body', 'No snippet')}\n\n"
            
        return formatted_results
    except Exception as e:
        logger.error(f"Failed to search web: {e}")
        return f"Error executing web search: {e}"


# --- Read Webpage Tool ---
class ReadWebpageArgs(BaseModel):
    url: str = Field(description="The exact URL of the webpage to read.")
    extraction_goal: str = Field(description="What specific information you want to extract from this page (e.g. 'Find the opening hours and ticket prices')")

@tool("read_webpage", args_schema=ReadWebpageArgs)
def read_webpage(url: str, extraction_goal: str) -> str:
    """
    Call this tool when you have a specific URL (from search_web) and need to read the full contents of the page.
    This tool safely bypasses bot blockers and uses an internal LLM to summarize the massive webpage to prevent memory bloat.
    """
    logger.info(f"Discovery Tool: Reading webpage '{url}' via Jina Reader...")
    try:
        # Use Jina Reader API to get clean Markdown, bypassing Cloudflare
        jina_url = f"https://r.jina.ai/{url}"
        response = requests.get(jina_url, timeout=15)
        response.raise_for_status()
        
        raw_markdown = response.text
        
        # FAILSAFE: The markdown could be 20,000 tokens. We must not return this directly to the LangGraph state.
        # We spawn an isolated summarizer LLM to extract only the necessary facts.
        llm = get_llm(model_name="gemini-1.5-flash", temperature=0)
        
        system_prompt = SystemMessage(content=f"""
        You are a highly efficient Web Extraction Assistant.
        Read the following markdown content from a webpage, and extract ONLY the information requested by the primary agent.
        Keep your response under 500 words. If the information is not present, state 'Information not found on page.'
        
        Extraction Goal: {extraction_goal}
        """)
        
        human_prompt = HumanMessage(content=f"WEBPAGE CONTENT:\n{raw_markdown[:50000]}") # Cap at 50k chars just in case
        
        logger.info(f"Discovery Tool: Passing {len(raw_markdown)} chars to Summarizer LLM...")
        summary_response = llm.invoke([system_prompt, human_prompt])
        
        return f"Extracted Data from {url}:\n{summary_response.content}"
        
    except Exception as e:
        logger.error(f"Failed to read webpage: {e}")
        return f"Error reading webpage: {e}"


# --- Find and Register Place Tool ---
class RegisterPlaceArgs(BaseModel):
    query: str = Field(description="A highly specific location query (e.g. 'McDonalds near Shibuya crossing Tokyo')")

@tool("find_and_register_place", args_schema=RegisterPlaceArgs)
def find_and_register_place(query: str) -> str:
    """
    CRITICAL MANDATORY TOOL: You MUST call this tool before calling 'add_stop'.
    Call this tool to search Google Maps for a specific place and automatically register it in the backend database.
    It returns the official google_place_id which you can then pass to 'add_stop'.
    """
    logger.info(f"Discovery Tool: Resolving Google Place ID for '{query}'...")
    api_key = settings.GOOGLE_MAPS_API_KEY
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY environment variable is missing."
        
    try:
        gmaps = googlemaps.Client(key=api_key)
        
        # 1. Search Google Places API
        places_result = gmaps.places(query=query)
        if not places_result or 'results' not in places_result or len(places_result['results']) == 0:
            return f"No Google Maps results found for '{query}'. Try a different search."
            
        # For MVP, we automatically pick the first result.
        # REACH GOAL: Interactive Disambiguation (Human-in-the-Loop) goes here.
        top_result = places_result['results'][0]
        place_id = top_result['place_id']
        name = top_result.get('name', 'Unknown')
        address = top_result.get('formatted_address', 'Unknown')
        
        logger.info(f"Resolved Place: {name} ({place_id})")
        
        # 2. Register the Place with the Java Location Service DB via gRPC
        location_grpc_url = settings.LOCATION_GRPC_URL
        
        logger.info(f"Registering place {place_id} with Location Service (gRPC)...")
        
        with grpc.insecure_channel(location_grpc_url) as channel:
            stub = location_pb2_grpc.LocationGrpcServiceStub(channel)
            request = location_pb2.AddLocationRequest(google_place_id=place_id)
            
            # This makes the gRPC call to Java which extracts metadata and saves it
            response = stub.AddLocation(request, timeout=10)
            
        return f"SUCCESS: '{name}' at '{address}' was successfully registered via gRPC. You may now call add_stop using google_place_id: '{place_id}'"
        
    except grpc.RpcError as rpc_error:
        logger.error(f"Location Service gRPC failed: {rpc_error}")
        return f"Error: Failed to register place via gRPC. Do NOT proceed to add_stop. Status: {rpc_error.code()}, Details: {rpc_error.details()}"
    except Exception as e:
        logger.error(f"Google Maps API failed: {e}")
        return f"Error looking up place: {e}"
