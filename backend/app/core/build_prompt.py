from __future__ import annotations


def build_prompt(question: str, chunks: list[dict], mode: str = "rag") -> str:
    context = ""
    for i, chunk in enumerate(chunks, start=1):
        page = chunk["metadata"].get("page") or chunk["metadata"].get("sheet", "unknown")
        source = chunk["metadata"].get("filename", "unknown")
        year = chunk["metadata"].get("year", "")
        context += f"\n[{i}] Source: {source} | Page/Sheet: {page} | Year: {year}\n"
        context += chunk["content"] + "\n"

    if mode == "calc":
        # Conversational, calculation-focused instructions (no numbered headers)
        return f"""You are a senior financial analyst assistant helping a Chartered Accountant.
    Use ONLY the context provided below to answer the question.
    When a calculation is required, clearly present the following in a concise, conversational form:
    - The formula used
    - The numeric values used (with units)
    - The computed result (with units)
    Always cite the exact source (filename + page/sheet + year).
    Never guess — only use numbers explicitly present in context.

    Context:
    {context}

    Question: {question}

    Do not convert ratios to percentages unless the formula explicitly multiplies by 100. Express ratios as decimals only.

    Answer:"""

    # default/rag mode: keep existing, more structured instructions
    return f"""You are a senior financial analyst assistant helping a Chartered Accountant.
Use ONLY the context provided below to answer the question.
The context contains data from four sources:
1. Excel structured financials (precise numbers, 10 years of data)
2. Annual report image pages (charts, infographics, visual data)
3. PDF annual report text (narrative, MD&A, strategy sections)
4. Earnings call transcripts (management commentary, analyst Q&A, forward guidance)

Rules:
- For questions about what management SAID, GUIDED, or COMMENTED — use ONLY earnings call transcript sources
- For precise financial figures — prefer Excel data
- For segment breakdowns and visual KPIs — use image data
- For strategy and narrative — use PDF text
- Always cite the exact source (filename + page/sheet + year)
- Never guess or approximate — only use numbers explicitly present in context

Context:
{context}

Question: {question}

Provide a detailed answer with:
1. The exact answer with units
2. Your calculation steps (if applicable)
3. The source citation

Answer:"""