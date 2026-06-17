import re
import pytest
from unittest.mock import patch
from app.core.calculation_agent import (
    _safe_eval_expression,
    compute_answer,
    HARDCODED_FORMULAS,
)


class TestSafeEvalExpression:
    def test_basic_division(self):
        result = _safe_eval_expression("metric1 / metric2", {"metric1": 500.0, "metric2": 1000.0})
        assert result == 0.5

    def test_basic_addition(self):
        result = _safe_eval_expression(
            "metric1 + metric2 + metric3",
            {"metric1": 100.0, "metric2": 200.0, "metric3": 300.0},
        )
        assert result == 600.0

    def test_allows_abs_and_round(self):
        result = _safe_eval_expression("round(abs(metric1), 1)", {"metric1": -42.567})
        assert result == 42.6

    def test_rejects_import_injection(self):
        result = _safe_eval_expression("__import__('os').system('echo pwned')", {})
        assert result is None

    def test_rejects_attribute_access(self):
        result = _safe_eval_expression("metric1.__class__", {"metric1": 5.0})
        assert result is None

    def test_rejects_unknown_function_call(self):
        result = _safe_eval_expression("open('secrets.txt')", {})
        assert result is None

    def test_invalid_syntax_returns_none(self):
        result = _safe_eval_expression("metric1 / / metric2", {"metric1": 1.0, "metric2": 1.0})
        assert result is None


class TestHardcodedFormulasStructure:
    def test_registry_not_empty(self):
        assert len(HARDCODED_FORMULAS) > 0

    def test_every_entry_has_required_keys(self):
        required = {"computation_type", "formula", "metrics", "multiply_by_100"}
        for name, entry in HARDCODED_FORMULAS.items():
            missing = required - entry.keys()
            assert not missing, f"'{name}' is missing keys: {missing}"

    def test_every_metric_has_name_and_sheet(self):
        for name, entry in HARDCODED_FORMULAS.items():
            for metric in entry["metrics"]:
                assert "name" in metric, f"'{name}' has a metric missing 'name'"
                assert "sheet" in metric, f"'{name}' has a metric missing 'sheet'"

    def test_formula_evaluates_with_dummy_values(self):
        for name, entry in HARDCODED_FORMULAS.items():
            placeholder_numbers = {int(n) for n in re.findall(r"metric(\d+)", entry["formula"])}
            assert placeholder_numbers, f"Formula for '{name}' has no metric placeholders: {entry['formula']}"
            dummy_vars = {f"metric{i}": 1.0 for i in range(1, max(placeholder_numbers) + 1)}
            result = _safe_eval_expression(entry["formula"], dummy_vars)
            assert result is not None, f"Formula for '{name}' failed to evaluate: {entry['formula']}"


class TestComputeAnswer:
    @patch("app.core.calculation_agent.fetch_metric")
    def test_debt_to_equity_ratio(self, mock_fetch):
        mock_fetch.side_effect = [500.0, 1000.0]
        intent = {
            "computation_type": "ratio",
            "formula": "metric1 / metric2",
            "metrics": [
                {"name": "Borrowings", "sheet": "balance_sheet"},
                {"name": "Networth", "sheet": "balance_sheet"},
            ],
            "years": ["2024"],
            "multiply_by_100": False,
        }
        result = compute_answer(intent, company_slug="test_company")
        assert result is not None
        assert result["answer"] == 0.5
        assert result["year"] == "2024"

    @patch("app.core.calculation_agent.fetch_metric")
    def test_multiply_by_100_applied(self, mock_fetch):
        mock_fetch.side_effect = [194.57, 2856.74]
        intent = {
            "computation_type": "ratio",
            "formula": "metric1 / metric2",
            "metrics": [
                {"name": "Net Profit", "sheet": "profit_loss"},
                {"name": "Networth", "sheet": "balance_sheet"},
            ],
            "years": ["2025"],
            "multiply_by_100": True,
        }
        result = compute_answer(intent, company_slug="test_company")
        assert result is not None
        assert result["answer"] == round((194.57 / 2856.74) * 100, 2)

    @patch("app.core.calculation_agent.fetch_metric")
    def test_returns_none_when_metric_missing(self, mock_fetch):
        mock_fetch.side_effect = [None, 1000.0]
        intent = {
            "computation_type": "ratio",
            "formula": "metric1 / metric2",
            "metrics": [
                {"name": "Borrowings", "sheet": "balance_sheet"},
                {"name": "Networth", "sheet": "balance_sheet"},
            ],
            "years": ["2024"],
            "multiply_by_100": False,
        }
        result = compute_answer(intent, company_slug="test_company")
        assert result is None
