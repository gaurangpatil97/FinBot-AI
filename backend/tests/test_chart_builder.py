import pytest
from unittest.mock import patch, MagicMock
from app.core.chart_builder import plan_chart, build_chart_data
from app.models.schemas import ChartData

class TestChartBuilderFallback:
    @patch("app.core.chart_builder.fetch_metric")
    @patch("app.core.chart_builder.get_available_years")
    @patch("app.core.chart_builder.plan_chart")
    def test_invalid_ratio_fallback(self, mock_plan, mock_years, mock_fetch):
        """Test fallback when an invalid ratio is planned."""
        mock_years.return_value = ["2022", "2023"]
        mock_plan.return_value = {
            "chart_kind": "ratio",
            "chart_type": "line",
            "metrics": [],
            "ratio": "invalid_ratio_formula",
            "year_start": None,
            "year_end": None
        }
        mock_fetch.return_value = 100.0

        # Should fall back to single_metric on Sales
        result = build_chart_data("test_company", [], question="Plot invalid ratio")
        assert result.series[0].name == "Sales"
        assert result.series[0].data == [100.0, 100.0]

    @patch("app.core.chart_builder.fetch_metric")
    @patch("app.core.chart_builder.get_available_years")
    @patch("app.core.chart_builder.plan_chart")
    def test_invalid_metrics_fallback(self, mock_plan, mock_years, mock_fetch):
        """Test fallback when unrecognized metrics are planned."""
        mock_years.return_value = ["2022", "2023"]
        mock_plan.return_value = {
            "chart_kind": "single_metric",
            "chart_type": "line",
            "metrics": ["Nonexistent Metric"],
            "ratio": None,
            "year_start": None,
            "year_end": None
        }
        mock_fetch.return_value = 100.0

        # Should fall back to Sales
        result = build_chart_data("test_company", [], question="Plot bad metric")
        assert result.series[0].name == "Sales"

    @patch("app.core.chart_builder.fetch_metric")
    @patch("app.core.chart_builder.get_available_years")
    @patch("app.core.chart_builder.plan_chart")
    def test_comparison_too_few_metrics(self, mock_plan, mock_years, mock_fetch):
        """Test comparison fallback to single_metric when less than 2 metrics are valid."""
        mock_years.return_value = ["2022", "2023"]
        mock_plan.return_value = {
            "chart_kind": "comparison",
            "chart_type": "combo",
            "metrics": ["Sales"],  # Only 1 metric
            "ratio": None,
            "year_start": None,
            "year_end": None
        }
        mock_fetch.return_value = 100.0

        # Should fall back to single_metric on Sales
        result = build_chart_data("test_company", [], question="Compare Sales")
        assert len(result.series) == 1
        assert result.series[0].name == "Sales"

    @patch("app.core.chart_builder.fetch_metric")
    @patch("app.core.chart_builder.get_available_years")
    @patch("app.core.chart_builder.plan_chart")
    def test_comparison_truncates_metrics(self, mock_plan, mock_years, mock_fetch):
        """Test comparison truncates metrics list to the first 2 when more are supplied."""
        mock_years.return_value = ["2022", "2023"]
        mock_plan.return_value = {
            "chart_kind": "comparison",
            "chart_type": "combo",
            "metrics": ["Sales", "EBITDA", "Net profit"],  # 3 metrics
            "ratio": None,
            "year_start": None,
            "year_end": None
        }
        mock_fetch.side_effect = [100.0, 100.0, 50.0, 50.0]

        result = build_chart_data("test_company", [], question="Compare three metrics")
        assert len(result.series) == 2
        assert result.series[0].name == "Sales"
        assert result.series[1].name == "EBITDA"


class TestChartBuilderYoYMath:
    @patch("app.core.chart_builder.fetch_metric")
    @patch("app.core.chart_builder.get_available_years")
    @patch("app.core.chart_builder.plan_chart")
    def test_yoy_growth_rate_math(self, mock_plan, mock_years, mock_fetch):
        """Test YoY growth rate calculation and axis labeling format."""
        mock_years.return_value = ["2022", "2023"]
        mock_plan.return_value = {
            "chart_kind": "growth_rate",
            "chart_type": "bar",
            "metrics": ["Sales"],
            "ratio": None,
            "year_start": None,
            "year_end": None
        }
        # Fetch returns 100.0 for FY22, 150.0 for FY23
        mock_fetch.side_effect = [100.0, 150.0]

        result = build_chart_data("test_company", [], question="YoY Sales growth")
        assert result.x_axis == ["FY22→FY23"]
        assert result.series[0].data == [50.0]  # (150 - 100)/100 * 100 = 50%
        assert result.y_axis_label == "%"


class TestChartBuilderAxisDetection:
    @patch("app.core.chart_builder.fetch_metric")
    @patch("app.core.chart_builder.get_available_years")
    @patch("app.core.chart_builder.plan_chart")
    def test_dual_axis_large_scale_difference(self, mock_plan, mock_years, mock_fetch):
        """Test secondary_y_axis is set to True when scale difference is >10x."""
        mock_years.return_value = ["2022"]
        mock_plan.return_value = {
            "chart_kind": "comparison",
            "chart_type": "combo",
            "metrics": ["Sales", "Net profit"],
            "ratio": None,
            "year_start": None,
            "year_end": None
        }
        # Sales = 1000.0, Net profit = 5.0 (Ratio 200x)
        mock_fetch.side_effect = [1000.0, 5.0]

        result = build_chart_data("test_company", [], question="Compare Sales and Net profit")
        assert result.secondary_y_axis is True

    @patch("app.core.chart_builder.fetch_metric")
    @patch("app.core.chart_builder.get_available_years")
    @patch("app.core.chart_builder.plan_chart")
    def test_single_axis_small_scale_difference(self, mock_plan, mock_years, mock_fetch):
        """Test secondary_y_axis remains False when scale difference is <10x."""
        mock_years.return_value = ["2022"]
        mock_plan.return_value = {
            "chart_kind": "comparison",
            "chart_type": "combo",
            "metrics": ["Sales", "EBITDA"],
            "ratio": None,
            "year_start": None,
            "year_end": None
        }
        # Sales = 1000.0, EBITDA = 200.0 (Ratio 5x)
        mock_fetch.side_effect = [1000.0, 200.0]

        result = build_chart_data("test_company", [], question="Compare Sales and EBITDA")
        assert result.secondary_y_axis is False


class TestChartPlannerScenarios:
    @patch("openai.OpenAI")
    def test_plan_chart_single_metric(self, mock_openai_class):
        """Test LLM planning for a single metric query."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"chart_kind": "single_metric", "chart_type": "line", "metrics": ["Sales"], "ratio": null, "year_start": null, "year_end": null}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = plan_chart("Show me Sales over the years")
        assert result["chart_kind"] == "single_metric"
        assert result["chart_type"] == "line"
        assert result["metrics"] == ["Sales"]

    @patch("openai.OpenAI")
    def test_plan_chart_growth_rate(self, mock_openai_class):
        """Test LLM planning for a YoY growth rate query."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"chart_kind": "growth_rate", "chart_type": "bar", "metrics": ["EBITDA"], "ratio": null, "year_start": null, "year_end": null}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = plan_chart("Plot YoY EBITDA growth")
        assert result["chart_kind"] == "growth_rate"
        assert result["chart_type"] == "bar"

    @patch("openai.OpenAI")
    def test_plan_chart_comparison_with_bounds(self, mock_openai_class):
        """Test LLM planning for comparison query with year boundaries."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"chart_kind": "comparison", "chart_type": "combo", "metrics": ["Sales", "EBITDA"], "ratio": null, "year_start": "FY22", "year_end": "FY25"}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = plan_chart("Compare Sales and EBITDA from FY22 to FY25")
        assert result["chart_kind"] == "comparison"
        assert result["year_start"] == "FY22"
        assert result["year_end"] == "FY25"

    @patch("openai.OpenAI")
    @patch("app.core.chart_builder.fetch_metric")
    @patch("app.core.chart_builder.get_available_years")
    def test_plan_chart_malformed_json_fallback(self, mock_years, mock_fetch, mock_openai_class):
        """Test graceful fallback to single_metric on Sales when LLM returns invalid JSON."""
        mock_years.return_value = ["2022"]
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="invalid JSON response string"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_fetch.return_value = 100.0

        # plan_chart should return None
        plan = plan_chart("some unstructured chart query")
        assert plan is None

        # build_chart_data should fall back to single_metric on Sales
        result = build_chart_data("test_company", [], question="some unstructured chart query")
        assert result.series[0].name == "Sales"
        assert result.chart_type == "bar"  # default type
