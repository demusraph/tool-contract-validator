import unittest
import asyncio
import uuid
from typing import Dict, Any
from tool_contract_validator.models import ContractSpec
from tool_contract_validator.core import ContractEngine

class TestContractBoundaries(unittest.TestCase):
    """Exhaustive boundary testing for ContractEngine validation logic."""

    def setUp(self):
        self.spec = ContractSpec(
            name="BoundaryTest",
            version="1.0.0",
            input_schema={"type": "object"},
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

    def run_async(self, coro):
        return asyncio.run(coro)

    def test_empty_input_payload(self):
        """Test behavior with an empty dictionary input."""
        result = self.run_async(self.engine.execute_test({}))
        self.assertTrue(result.validation.is_valid)
        self.assertEqual(result.status_code, 200)

    def test_large_payload_boundary(self):
        """Test behavior with a large nested payload."""
        large_input = {"data": {str(i): i for i in range(1000)}}
        result = self.run_async(self.engine.execute_test(large_input))
        self.assertTrue(result.validation.is_valid)

    def test_zero_latency_simulation(self):
        """Test validation report generation with zero latency."""
        report = self.run_async(self.engine.validate_output({"result": "ok", "data": {}}, 0.0))
        self.assertEqual(report.latency_ms, 0.0)
        self.assertTrue(report.is_valid)

    def test_negative_latency_handling(self):
        """Test validation report robustness with negative latency values."""
        report = self.run_async(self.engine.validate_output({"result": "ok", "data": {}}, -1.0))
        self.assertEqual(report.latency_ms, -1.0)
        self.assertTrue(report.is_valid)

    def test_invalid_schema_structure(self):
        """Test validation failure when output schema is violated."""
        # Missing 'result' key in output
        report = self.run_async(self.engine.validate_output({"data": {}}, 10.0))
        self.assertFalse(report.is_valid)
        self.assertGreater(len(report.errors), 0)

    def test_identical_concurrent_executions(self):
        """Test batch execution with identical payloads."""
        payload = {"key": "value"}
        results = self.run_async(self.engine.run_suite([payload, payload, payload]))
        self.assertEqual(len(results), 3)
        for res in results:
            self.assertTrue(res.validation.is_valid)

    def test_none_type_input(self):
        """Test behavior when input is None (should be handled by schema validation)."""
        # The engine expects a dict, passing None should trigger a validation error
        report = self.run_async(self.engine.validate_output(None, 0.0))
        self.assertFalse(report.is_valid)

    def test_unicode_payload_handling(self):
        """Test handling of non-ASCII characters in payloads."""
        payload = {"data": {"emoji": "🚀", "text": "你好"}}
        result = self.run_async(self.engine.execute_test(payload))
        self.assertTrue(result.validation.is_valid)
        self.assertEqual(result.output_payload["data"]["data"]["emoji"], "🚀")

    def test_deeply_nested_payload(self):
        """Test recursion depth handling for nested structures."""
        nested = {"a": {"a": {"a": {"a": {"a": "end"}}}}}
        result = self.run_async(self.engine.execute_test(nested))
        self.assertTrue(result.validation.is_valid)

    def test_uuid_uniqueness_in_suite(self):
        """Ensure every execution in a suite generates a unique run_id."""
        results = self.run_async(self.engine.run_suite([{}, {}]))
        self.assertNotEqual(results[0].run_id, results[1].run_id)
        self.assertIsInstance(results[0].run_id, uuid.UUID)

if __name__ == "__main__":
    unittest.main()