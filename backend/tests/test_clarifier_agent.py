import pytest
from unittest.mock import patch, MagicMock
from app.core.clarifier_agent import decompose_query

class TestClarifierAgentFallback:
    @patch("app.core.clarifier_agent.client")
    def test_api_exception_fallback(self, mock_client):
        """Test that decompose_query falls back to the original question when API fails."""
        mock_client.chat.completions.create.side_effect = Exception("API Connection Timeout")
        
        question = "What was the EBITDA in FY25?"
        result = decompose_query(question)
        assert result == [question]

    @patch("app.core.clarifier_agent.client")
    def test_invalid_json_fallback(self, mock_client):
        """Test that decompose_query falls back when LLM returns invalid JSON."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="This is not valid JSON string"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        
        question = "Compare Sales and PAT"
        result = decompose_query(question)
        assert result == [question]


class TestClarifierAgentDecomposition:
    @patch("app.core.clarifier_agent.client")
    def test_simple_question_decomposition(self, mock_client):
        """Test single-fact question returns exactly 1 sub-query."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='["PAT profit after tax FY2023"]'))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        
        result = decompose_query("What is the PAT for FY2023")
        assert result == ["PAT profit after tax FY2023"]

    @patch("app.core.clarifier_agent.client")
    def test_comparison_question_decomposition(self, mock_client):
        """Test comparison question decomposes into 2 sub-queries."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='["receivables balance sheet FY24", "sales revenue profit loss FY24"]'))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        
        result = decompose_query("Compare receivables growth vs sales growth in FY24")
        assert result == ["receivables balance sheet FY24", "sales revenue profit loss FY24"]

    @patch("app.core.clarifier_agent.client")
    def test_complex_question_decomposition(self, mock_client):
        """Test multi-part question decomposes into 3+ sub-queries."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='["borrowings debt FY22 to FY26", "EBITDA profit loss FY22 to FY26", "interest coverage ratio FY22 to FY26"]'))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        
        result = decompose_query("Analyze debt, EBITDA, and interest coverage trends from FY22 to FY26")
        assert result == [
            "borrowings debt FY22 to FY26",
            "EBITDA profit loss FY22 to FY26",
            "interest coverage ratio FY22 to FY26"
        ]

    @patch("app.core.clarifier_agent.client")
    def test_empty_array_fallback(self, mock_client):
        """Test fallback when LLM returns an empty JSON list."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='[]'))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        
        question = "What is the capex?"
        result = decompose_query(question)
        assert result == [question]

    @patch("app.core.clarifier_agent.client")
    def test_object_instead_of_list_fallback(self, mock_client):
        """Test fallback when LLM returns a JSON object instead of a list."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"sub_queries": []}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        
        question = "Show me the segment results"
        result = decompose_query(question)
        assert result == [question]
