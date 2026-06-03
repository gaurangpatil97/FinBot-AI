import json
from openai import OpenAI
from config import get_settings
from loguru import logger

settings = get_settings()
client = OpenAI(api_key=settings.OPENAI_API_KEY)

DECOMPOSE_PROMPT = '''You are a financial query decomposer for a CA tool.
Given a financial question that may require multiple data points, return a JSON array of focused sub-queries.
Each sub-query should retrieve one specific metric or data type.
If the question needs only one metric, return a list with just that question unchanged.
Return ONLY a valid JSON array of strings. No explanation, no markdown, no preamble.

Examples:
Input: compare trade receivables growth vs revenue growth FY2019 to FY2025
Output: [\"trade receivables balance sheet FY2019 to FY2025\", \"revenue from operations profit loss FY2019 to FY2025\"]

Input: what is the PAT for FY2023
Output: [\"PAT profit after tax FY2023\"]

Input: other income as a percentage of PBT for each year
Output: [\"other income each year FY2019 to FY2025\", \"profit before tax PBT each year FY2019 to FY2025\"]'''

def decompose_query(question: str) -> list[str]:
    try:
        response = client.chat.completions.create(
            model='gpt-4.1-mini',
            messages=[
                {'role': 'system', 'content': DECOMPOSE_PROMPT},
                {'role': 'user', 'content': question}
            ],
            temperature=0,
            max_tokens=200
        )
        raw = response.choices[0].message.content.strip()
        sub_queries = json.loads(raw)
        if isinstance(sub_queries, list) and len(sub_queries) > 0:
            logger.info(f'[Clarifier] Decomposed into {len(sub_queries)} sub-queries: {sub_queries}')
            return sub_queries
        return [question]
    except Exception as e:
        logger.warning(f'[Clarifier] Failed, falling back to original question: {e}')
        return [question]
