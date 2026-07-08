from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

# In-memory storage of rules per session (for simplicity)
RULES_STORE = {}

class RulesRequest(BaseModel):
    document_id: str
    domain: str
    custom_rules: List[str]

@router.post("/")
def set_rules(data: RulesRequest):
    RULES_STORE[data.document_id] = {
        "domain": data.domain,
        "custom_rules": data.custom_rules
    }
    return {"status": "rules saved", "document_id": data.document_id}
