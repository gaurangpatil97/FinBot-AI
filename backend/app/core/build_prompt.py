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

    # Improved extraction for partial chunks and narrative questions
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

Additional instructions for partial or truncated chunks:
- If a chunk appears cut off mid-sentence, use whatever numbers 
  or facts are visible — do not ignore partial data
- If the exact figure is not stated but can be inferred from 
  surrounding context, state clearly that it is inferred
- For MD&A narrative questions, look for management explanation 
  text not just numbers — words like 'due to', 'owing to', 
  'because of', 'attributed to' signal the reason being sought
- For audit/KAM questions, look for Key Audit Matter headings 
  and the description that follows immediately after
- If multiple chunks contain relevant partial information, 
  synthesize them into one complete answer rather than 
  reporting only from one chunk
- If the question asks you to identify a pattern, trend, discrepancy, 
  or implication, state it explicitly  don't just restate the raw figures
- Before performing any calculation or extraction, explicitly state which 
  time period/label each input value comes from, to avoid mixing up 
  quarters, half-years, and full years
- Concall transcript chunks contain spoken dialogue; carefully identify 
  the speaker and the specific segment/quarter being discussed before 
  extracting figures
- When the question asks about a specific named financial ratio or metric, 
  use that exact metric as stated - do not substitute a similar-sounding 
  but different ratio (e.g. Interest Coverage Ratio is not the same as 
  Debt Service Coverage Ratio; Return on Equity is not the same as Return 
  on Net Worth)
- If the question has multiple parts or asks multiple things (e.g. 'what 
  is X, and what does this indicate/imply/mean'), make sure every part is 
  explicitly addressed in the answer - do not stop after answering only 
  the first part

Context:
{context}

Question: {question}

Provide a detailed answer with:
1. The exact answer with units
2. Your calculation steps (if applicable)
3. The source citation

Answer:"""