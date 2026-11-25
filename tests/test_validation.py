import unittest
import asyncio
import uuid
from pydantic import ValidationError
from tool_contract_validator.models import ContractSpec, ValidationReport
from tool_contract_validator.core import ContractEngine

class TestValidation(unittest.TestCase):
    def setUp(self):
        self.valid_spec = ContractSpec(
            name="test-tool",
            version="1.0.0",
            input_schema={"type": "object", "properties": {"val": {"type": "integer"}}},
            output_schema={"type": "object", "properties": {"result": {"type": "string"}}, "required": ["result"]},
            timeout_seconds=2.0
        )
        self.engine = ContractEngine(self.valid_spec)

    def test_contract_spec_immutability(self):
        """Ensure ContractSpec is frozen via Pydantic model_config."""
        with self.assertRaises(ValidationError):
            self.valid_spec.name = "new-name"

    def test_validation_report_success(self):
        """Verify ValidationReport correctly identifies valid output."""
        report = asyncio.run(self.engine.validate_output({"result": "ok"}, 10.5))
        self.assertTrue(report.is_valid)
        self.assertEqual(len(report.errors), 0)
        self.assertEqual(report.latency_ms, 10.5)

    def test_validation_report_failure(self):
        """Verify ValidationReport captures schema mismatch errors."""
        report = asyncio.run(self.engine.validate_output({"result": 123}, 5.0))
        self.assertFalse(report.is_valid)
        self.assertGreater(len(report.errors), 0)
        self.assertIn("Schema mismatch", report.errors[0])

    def test_execution_result_structure(self):
        """Verify ExecutionResult fields are populated correctly."""
        result = asyncio.run(self.engine.execute_test({"val": 1}))
        self.assertIsInstance(result.run_id, uuid.UUID)
        self.assertEqual(result.status_code, 200)
        self.assertIn("result", result.output_payload)

    def test_invalid_contract_schema_definition(self):
        """Ensure Pydantic catches invalid ContractSpec initialization."""
        with self.assertRaises(ValidationError):
            ContractSpec(
                name="bad-spec",
                version="1.0",
                input_schema="not-a-dict",
                output_schema={}
            )

    def test_concurrent_suite_execution(self):
        """Verify run_suite handles multiple concurrent executions."""
        test_cases = [{"val": 1}, {"val": 2}, {"val": 3}]
        results = asyncio.run(self.engine.run_suite(test_cases))
        self.assertEqual(len(results), 3)
        for res in results:
            self.assertTrue(res.validation.is_valid)

    def test_empty_output_validation(self):
        """Verify validation fails when output is empty but schema requires fields."""
        strict_spec = ContractSpec(
            name="strict",
            version="1.0",
            input_schema={},
            output_schema={"required": ["data"], "type": "object", "properties": {"data": {"type": "string"}}}
        )
        engine = ContractEngine(strict_spec)
        report = asyncio.run(engine.validate_output({}, 1.0))
        self.assertFalse(report.is_valid)

    def test_latency_measurement_precision(self):
        """Verify latency is recorded as a float."""
        report = asyncio.run(self.engine.validate_output({"result": "ok"}, 123.456))
        self.assertIsInstance(report.latency_ms, float)
        self.assertEqual(report.latency_ms, 123.456)

    def test_uuid_generation_uniqueness(self):
        """Verify each execution generates a unique run_id."""
        res1 = asyncio.run(self.engine.execute_test({}))
        res2 = asyncio.run(self.engine.execute_test({}))
        self.assertNotEqual(res1.run_id, res2.run_id)