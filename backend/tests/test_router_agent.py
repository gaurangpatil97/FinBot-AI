import pytest
from unittest.mock import patch, MagicMock
from app.core.router_agent import _keyword_route, route_question, RouteDecision

class TestKeywordRoute:
    def test_excel_sheet_detection(self):
        """Test routing to excel and balance sheet with excel-specific keywords."""
        result = _keyword_route("What was the balance sheet debt?", "craftsman_automation_ltd", "2024")
        assert "excel" in result.source_types
        assert result.sheet == "balance_sheet"
        assert result.agent_used == "keyword_fallback"
        assert "craftsman_automation_ltd_excel" in result.collections_searched
        assert result.year == "2024"

    def test_image_force_trigger(self):
        """Test image force trigger route with chart keywords."""
        result = _keyword_route("Show me the revenue chart from the annual report", "astral_ltd", "2022")
        assert "images" in result.source_types
        assert "excel" in result.source_types
        assert "astral_ltd_images" in result.collections_searched
        assert "astral_ltd_excel" in result.collections_searched
        assert result.agent_used == "keyword_fallback"

    def test_concall_trigger(self):
        """Test routing to concall for management earnings call questions."""
        result = _keyword_route("what did management say about margins in the earnings call?", "craftsman_automation_ltd")
        assert "concall" in result.source_types
        assert "craftsman_automation_ltd_concall" in result.collections_searched
        assert result.agent_used == "keyword_fallback"

    def test_pdf_annual_report_trigger(self):
        """Test routing to pdf for strategy and annual report narrative questions."""
        result = _keyword_route("What are the risk factors and MD&A details?", "craftsman_automation_ltd")
        assert "pdf" in result.source_types
        assert "craftsman_automation_ltd_pdf" in result.collections_searched
        assert result.agent_used == "keyword_fallback"

    def test_cross_source_trigger(self):
        """Test routing to multiple sources when keywords from different domains are present."""
        result = _keyword_route("Compare the networth in the balance sheet with what the management guided", "craftsman_automation_ltd")
        assert "excel" in result.source_types
        assert "concall" in result.source_types
        assert result.agent_used == "keyword_fallback"


class TestYearExtraction:
    @patch("openai.OpenAI")
    def test_extract_fyxx(self, mock_openai_class):
        """Test extracting year in FYXX format (e.g. FY23 -> 2023)."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"source_types": ["excel"], "year": null, "sheet": "balance_sheet"}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = route_question("What was the balance sheet debt in FY23?", "craftsman_automation_ltd")
        assert result.year == "2023"

    @patch("openai.OpenAI")
    def test_extract_20xx(self, mock_openai_class):
        """Test extracting year in 20XX format (e.g. 2025 -> 2025)."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"source_types": ["excel"], "year": null, "sheet": "profit_loss"}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = route_question("What was the revenue for 2025?", "craftsman_automation_ltd")
        assert result.year == "2025"

    @patch("openai.OpenAI")
    def test_extract_no_year(self, mock_openai_class):
        """Test route_question behavior when no year is present in the question."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"source_types": ["pdf"], "year": null, "sheet": null}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = route_question("What is the general operational strategy?", "craftsman_automation_ltd")
        assert result.year is None


class TestRouteQuestionLLM:
    @patch("openai.OpenAI")
    def test_route_question_concall_mocked(self, mock_openai_class):
        """Test LLM route mapping to concall and year 2025."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"source_types": ["concall"], "year": "2025", "sheet": null}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = route_question("Summarize the Q1 FY25 concall", "craftsman_automation_ltd")
        assert result.source_types == ["concall"]
        assert result.year == "2025"
        assert result.agent_used == "llm"
        assert "craftsman_automation_ltd_concall" in result.collections_searched

    @patch("openai.OpenAI")
    def test_route_question_excel_sheet_mocked(self, mock_openai_class):
        """Test LLM route mapping to excel and balance sheet with specific year."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"source_types": ["excel"], "year": "2024", "sheet": "balance_sheet"}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = route_question("What is the debt of the company?", "craftsman_automation_ltd")
        assert result.source_types == ["excel"]
        assert result.year == "2024"
        assert result.sheet == "balance_sheet"
        assert result.agent_used == "llm"
        assert "craftsman_automation_ltd_excel" in result.collections_searched
