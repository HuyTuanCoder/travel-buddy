import json
import structlog
from src.core.telemetry import publish_thought, publish_token, publish_event

logger = structlog.get_logger(__name__)

class AgentStreamer:
    """
    Encapsulates all Redis PubSub event streaming logic to decouple 
    network broadcasting from the LangGraph execution loop.
    """
    def __init__(self, pubsub_channel: str, hide_system_thoughts: bool = False):
        self.pubsub_channel = pubsub_channel
        self.hide_system_thoughts = hide_system_thoughts

    async def stream_token(self, token_string: str):
        """Streams a single token to the UI chat bubble."""
        await publish_token(self.pubsub_channel, token_string)

    async def stream_thought(self, thought_string: str):
        """Streams a complete thought block to the UI reasoning panel."""
        await publish_thought(self.pubsub_channel, thought_string)

    async def stream_system_error(self, error_message: str):
        """
        Streams a strictly formatted system error (e.g. Validation Error).
        Can be toggled off via hide_system_thoughts for production environments.
        """
        if not self.hide_system_thoughts:
            await self.stream_thought(f"\n> [System] {error_message}\n")

    async def stream_tool_start(self, tool_name: str, args: dict = None):
        """Streams the beginning of a tool execution."""
        await self.stream_thought(f"\n\n> Executing action: {tool_name}...\n")

    async def stream_tool_result(self, tool_name: str, result_content: str, status: str = "SUCCESS"):
        """Streams the result of a tool execution."""
        display_content = result_content[:97] + "..." if len(result_content) > 100 else result_content
        await publish_event(self.pubsub_channel, "thought", f"> Action {tool_name} {status}: {display_content}\n")

    async def stream_draft_update(self, draft_action_json: dict):
        """Streams an itinerary draft update directly to the UI."""
        # The frontend expects an array of draft actions
        await publish_event(self.pubsub_channel, "draft_update", json.dumps([draft_action_json]))

    async def finish(self):
        """Sends the final 'done' event to unlock the UI."""
        await publish_event(self.pubsub_channel, "done", "")
