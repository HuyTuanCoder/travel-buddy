from enum import Enum
from pydantic import BaseModel, Field

class FactCategory(str, Enum):
    DIETARY = "DIETARY"
    BUDGET = "BUDGET"
    PACE = "PACE"
    ACCOMMODATION = "ACCOMMODATION"
    TRANSPORT = "TRANSPORT"
    GENERAL_MEMORY = "GENERAL_MEMORY"

class PermanenceLevel(str, Enum):
    TEMPORARY = "TEMPORARY" # Applies only to the current trip
    PERMANENT = "PERMANENT" # Applies globally to the user profile

class ExtractedFact(BaseModel):
    category: FactCategory = Field(description="The category of the extracted fact.")
    topic: str = Field(description="The specific topic or entity, e.g. 'Sushi' or 'Paris'.")
    sentiment: str = Field(description="The user's sentiment regarding this topic, e.g. 'NEGATIVE', 'POSITIVE', 'NEUTRAL'.")
    permanence: PermanenceLevel = Field(description="Whether this is a permanent constraint or a temporary preference.")
    raw_quote: str = Field(description="The exact words the user used.")
