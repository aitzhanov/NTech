from pydantic import BaseModel
from typing import Optional, Dict, Any

class Metadata(BaseModel):
    version: int
    timestamp: str
    source: str

class BridgeRequest(BaseModel):
    request_id: str
    decision_id: str
    entity_type: str
    entity_id: str
    action: str
    data: Dict[str, Any]
    metadata: Metadata

class BridgeResponse(BaseModel):
    request_id: str
    status: str
    message: str
    tx_hash: Optional[str]
    submitted_at: str
    expected_finalization: Optional[str]
