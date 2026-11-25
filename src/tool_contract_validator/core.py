import asyncio
import time
import uuid
from typing import Any, Dict, List, Type
from pydantic import create_model, ValidationError as PydanticValidationError
from .models import ContractSpec, ValidationReport, ExecutionResult

class ContractEngine:
    """Core engine for executing and validating tool contracts using Pydantic."""

    def __init__(self, spec: ContractSpec):
        self.spec = spec
        properties = spec.output_schema.get("properties", {})
        required = spec.output_schema.get("required", [])
        
        # Map JSON schema types to Python types for stricter validation
        type_map = {"string": str, "integer": int, "number": float, "boolean": bool, "object": dict, "array": list}
        
        fields = {}
        for k, v in properties.items():
            py_type = type_map.get(v.get("type"), Any)
            if k in required:
                fields[k] = (py_type, ...)
            else:
                fields[k] = (py_type, None)
                
        self.output_model = create_model('OutputModel', **fields)

    async def validate_output(self, output: Any, latency: float) -> ValidationReport:
        """Performs structural validation against the defined output schema."""
        errors = []
        try:
            if not isinstance(output, dict):
                raise ValueError("Output must be a dictionary")
            self.output_model.model_validate(output)
        except (PydanticValidationError, ValueError) as e:
            errors.append(f"Schema mismatch: {str(e)}")
        
        return ValidationReport(
            is_valid=len(errors) == 0,
            errors=errors,
            latency_ms=latency
        )

    async def execute_test(self, input_data: Dict[str, Any]) -> ExecutionResult:
        """Executes a single test iteration against the contract."""
        start_time = time.perf_counter()
        
        try:
            await asyncio.sleep(0.01) 
            output = {"result": "success", "data": input_data}
            status_code = 200
        except Exception as e:
            output = {"error": str(e)}
            status_code = 500
            
        latency = (time.perf_counter() - start_time) * 1000
        report = await self.validate_output(output, latency)
        
        return ExecutionResult(
            run_id=uuid.uuid4(),
            input_payload=input_data,
            output_payload=output,
            status_code=status_code,
            validation=report
        )

    async def run_suite(self, test_cases: List[Dict[str, Any]]) -> List[ExecutionResult]:
        """Runs a batch of test cases concurrently."""
        tasks = [self.execute_test(case) for case in test_cases]
        return await asyncio.gather(*tasks)