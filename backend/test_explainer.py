import json
import os
import unittest
from io import BytesIO
from unittest.mock import patch

from explainer import generate_audit_explanation


class AuditExplanationProviderTests(unittest.TestCase):
    def setUp(self):
        self.comparison_data = {
            "summary": {
                "name_a": "baseline.csv",
                "name_b": "target.csv",
                "rows_a": 10,
                "rows_b": 10,
                "row_delta": 0,
                "cols_a": 2,
                "cols_b": 2,
                "quality_score_a": 100,
                "quality_score_b": 100,
                "duplicates_a": 0,
                "duplicates_b": 0,
            },
            "schema_drift": {
                "has_drift": False,
                "columns_only_in_a": [],
                "columns_only_in_b": [],
                "type_mismatches": [],
            },
            "column_comparison": [],
            "financial_metrics": [],
        }
        self.classification = {"overall_status": "NEUTRAL", "classifications": []}
        self.openai_result = {
            "headline": "Datasets verified stable",
            "executive_summary": "No significant regressions were detected.",
            "recommended_actions": ["Continue routine monitoring."],
        }

    def test_uses_openai_chat_completions_when_configured(self):
        response_body = json.dumps({
            "choices": [{"message": {"content": json.dumps(self.openai_result)}}]
        }).encode("utf-8")

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "test-model"}):
            with patch("explainer.urlopen", return_value=BytesIO(response_body)) as openai_call:
                result = generate_audit_explanation(self.comparison_data, self.classification)

        request = openai_call.call_args.args[0]
        request_body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "https://api.openai.com/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(request_body["model"], "test-model")
        self.assertEqual(request_body["response_format"], {"type": "json_object"})
        self.assertEqual(result["generator"], "openai")
        self.assertEqual(result["model"], "test-model")
        self.assertEqual(result["headline"], self.openai_result["headline"])

    def test_uses_rules_without_openai_api_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
            with patch("explainer.urlopen") as openai_call:
                result = generate_audit_explanation(self.comparison_data, self.classification)

        openai_call.assert_not_called()
        self.assertEqual(result["generator"], "rules_fallback")
        self.assertIn("No Critical Regressions", result["headline"])


if __name__ == "__main__":
    unittest.main()
