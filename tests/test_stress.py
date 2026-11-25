import unittest
import asyncio
import uuid
from typing import List, Dict, Any
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tool_contract_validator.models import ContractSpec
from tool_contract_validator.core import ContractEngine

class TestStressSuite(unittest.TestCase):
    """
    High-performance stress testing suite for the ToolContract Validator.
    Validates concurrency, throughput, and schema enforcement under load.
    """

    def setUp(self):
        self.spec = ContractSpec(
            name="StressTestTool",
            version="1.0.0",
            input_schema={"type": "object", "properties": {"val": {"type": "integer"}}},
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string"},
                    "data": {"type": "object"}
                },
                "required": ["result", "data"]
            }
        )
        self.engine = ContractEngine(self.spec)

    def test_concurrent_execution_throughput(self):
        """Test that the engine handles 100 concurrent executions without failure."""
        async def run_batch():
            test_cases = [{"val": i} for i in range(100)]
            return await self.engine.run_suite(test_cases)

        results = asyncio.run(run_batch())
        self.assertEqual(len(results), 100)
        for res in results:
            self.assertTrue(res.validation.is_valid)
            self.assertEqual(res.status_code, 200)

    def test_large_payload_integrity(self):
        """Test engine stability with large nested JSON payloads."""
        large_data = {"val": 1, "nested": {str(i): "x" * 1024 for i in range(10)}}
        
        async def run_large():
            return await self.engine.execute_test(large_data)

        result = asyncio.run(run_large())
        self.assertTrue(result.validation.is_valid)
        self.assertEqual(result.input_payload["val"], 1)

    def test_schema_violation_handling(self):
        """Verify that invalid outputs are correctly flagged as invalid."""
        # Force a schema violation by providing a malformed output
        async def run_invalid():
            # The engine's execute_test currently returns a valid structure, 
            # so we test the validation logic directly.
            return await self.engine.validate_output({"wrong": "format"}, 0.0)

        report = asyncio.run(run_invalid())
        self.assertFalse(report.is_valid)
        self.assertTrue(len(report.errors) > 0)

    def test_fastapi_integration_load(self):
        """Test FastAPI TestClient throughput for endpoint integration."""
        app = FastAPI()
        
        @app.post("/validate")
        async def validate_endpoint(data: Dict[str, Any]):
            res = await self.engine.execute_test(data)
            return res.model_dump(mode='json')

        client = TestClient(app)
        
        # Perform 50 sequential requests via TestClient
        for i in range(50):
            response = client.post("/validate", json={"val": i})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["validation"]["is_valid"])

    def test_engine_latency_metrics(self):
        """Ensure latency reporting is non-negative and captured."""
        async def run_latency_check():
            return await self.engine.execute_test({"val": 42})

        result = asyncio.run(run_latency_check())
        # Latency should be captured in milliseconds
        self.assertGreaterEqual(result.validation.latency_ms, 0.0)
        self.assertIsInstance(result.run_id, uuid.UUID)

if __name__ == "__main__":
    unittest.main()