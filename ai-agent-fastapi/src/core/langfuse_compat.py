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
from langfuse.callback import CallbackHandler  # noqa: E402
