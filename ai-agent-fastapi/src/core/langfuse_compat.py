import sys
import types

# Import modern LangChain core paths
import langchain_core.callbacks
import langchain_core.callbacks.base
import langchain_core.agents
import langchain_core.documents

# Create aliases so the Langfuse v2 SDK can find them under the old paths
sys.modules['langchain.callbacks'] = langchain_core.callbacks
sys.modules['langchain.callbacks.base'] = langchain_core.callbacks.base

# Create a dummy schema module to hold agents and documents
m = types.ModuleType('langchain.schema')
sys.modules['langchain.schema'] = m
sys.modules['langchain.schema.agent'] = langchain_core.agents
sys.modules['langchain.schema.document'] = langchain_core.documents

# Now it is safe to import the Langfuse v2 CallbackHandler
from langfuse.callback import CallbackHandler as BaseCallbackHandler  # noqa: E402

class CallbackHandler(BaseCallbackHandler):
    """
    A custom wrapper around the legacy Langfuse v2 CallbackHandler.
    It intercepts Langchain LLM results and maps modern `usage_metadata` 
    (from Gemini/Vertex) into the legacy `token_usage` dictionary so that
    Langfuse v2 can accurately log token consumption and costs without requiring an upgrade.
    """
    
    def _map_tokens(self, response):
        if not hasattr(response, "llm_output") or response.llm_output is None:
            response.llm_output = {}
            
        token_usage = response.llm_output.get("token_usage", {})
        
        # Check if usage_metadata is embedded on the AIMessage directly (Modern Langchain)
        if hasattr(response, "generations") and response.generations:
            try:
                msg = response.generations[0][0].message
                if hasattr(msg, "usage_metadata") and msg.usage_metadata:
                    usage = msg.usage_metadata
                    token_usage["prompt_tokens"] = usage.get("input_tokens", 0)
                    token_usage["completion_tokens"] = usage.get("output_tokens", 0)
                    token_usage["total_tokens"] = usage.get("total_tokens", 0)
            except Exception:
                pass
                
        # Check if usage_metadata is in llm_output directly
        if "usage_metadata" in response.llm_output:
            usage = response.llm_output["usage_metadata"]
            token_usage["prompt_tokens"] = token_usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0)
            token_usage["completion_tokens"] = token_usage.get("completion_tokens", 0) or usage.get("output_tokens", 0)
            token_usage["total_tokens"] = token_usage.get("total_tokens", 0) or usage.get("total_tokens", 0)
            
        if token_usage:
            response.llm_output["token_usage"] = token_usage
            
        # Try to extract model_name from the chunk
        if hasattr(response, "generations") and response.generations:
            try:
                msg = response.generations[0][0].message
                if hasattr(msg, "response_metadata") and msg.response_metadata:
                    model_name = msg.response_metadata.get("model_name")
                    if model_name:
                        response.llm_output["model_name"] = model_name
                        
                # BUGFIX: Langfuse v2.53 _parse_usage overwrites token_usage if it finds usage_metadata on the chunk.
                # However, it fails to map 'input_tokens' to 'input'. We inject 'input', 'output', 'total' directly
                # into the chunk's usage_metadata so Langfuse's integration picks it up correctly without breaking Langchain.
                if hasattr(msg, "usage_metadata") and isinstance(msg.usage_metadata, dict):
                    msg.usage_metadata["input"] = msg.usage_metadata.get("input_tokens", 0)
                    msg.usage_metadata["output"] = msg.usage_metadata.get("output_tokens", 0)
                    msg.usage_metadata["total"] = msg.usage_metadata.get("total_tokens", 0)
            except Exception:
                pass

    def on_chat_model_end(self, response, **kwargs):
        self._map_tokens(response)
        return super().on_chat_model_end(response, **kwargs)
        
    def on_llm_end(self, response, **kwargs):
        import logging
        log = logging.getLogger("celery")
        
        self._map_tokens(response)
        
        try:
            run_id = kwargs.get("run_id")
            parent_run_id = kwargs.get("parent_run_id")
            
            if run_id not in self.runs:
                log.warning(f"Langfuse run_id {run_id} not found in runs list.")
                return
                
            generation = response.generations[-1][-1]
            
            from langchain_core.outputs import ChatGeneration
            # For extraction, we use Langfuse's internal helpers if possible, or fallback
            try:
                if isinstance(generation, ChatGeneration):
                    extracted_response = self._convert_message_to_dict(generation.message)
                else:
                    from langfuse.callback.langchain import _extract_raw_response
                    extracted_response = _extract_raw_response(generation)
            except Exception:
                extracted_response = generation.text if hasattr(generation, "text") else str(generation)

            usage = response.llm_output.get("token_usage", {})
            llm_usage = {
                "input": usage.get("prompt_tokens", 0),
                "output": usage.get("completion_tokens", 0),
                "total": usage.get("total_tokens", 0),
            }

            model = response.llm_output.get("model_name")
            
            self.runs[run_id] = self.runs[run_id].end(
                output=extracted_response,
                usage=llm_usage,
                usage_details=llm_usage,
                version=self.version,
                input=kwargs.get("inputs"),
                model=model,
            )

            self._update_trace_and_remove_state(
                run_id, parent_run_id, extracted_response
            )
            
            log.info(f"Langfuse on_llm_end fully overridden and tokens {llm_usage} logged for {model}.")
            
        except Exception as e:
            log.error(f"Failed to override Langfuse on_llm_end: {e}")

