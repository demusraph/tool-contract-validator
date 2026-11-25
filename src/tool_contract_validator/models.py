from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
import uuid

class ContractSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    name: str
    version: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    target_url: Optional[str] = None
    timeout_seconds: float = 5.0

class ValidationReport(BaseModel):
    run_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_valid: bool
    errors: List[str] = []
    latency_ms: float
    metadata: Dict[str, Any] = {}

class ExecutionResult(BaseModel):
    run_id: uuid.UUID
    input_payload: Dict[str, Any]
    output_payload: Any
    status_code: int
    validation: ValidationReport