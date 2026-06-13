from __future__ import annotations


def build_prompt(question: str, chunks: list[dict], mode: str = "rag") -> str:
    context = ""
    for i, chunk in enumerate(chunks, start=1):
        page = chunk["metadata"].get("page") or chunk["metadata"].get("sheet", "unknown")
        source = chunk["metadata"].get("filename", "unknown")
        year = chunk["metadata"].get("year", "")
        context += f"\n[{i}] Source: {source} | Page/Sheet: {page} | Year: {year}\n"
        context += chunk["content"] + "\n"

    structure_instructions = """You MUST structure your response using the following layout and markdown ## headings (do NOT use bold-text-as-heading like **Summary:**):

## Summary
Provide a 1-2 sentence direct answer and key conclusion up front (including the key figure with units if quantitative).

## Details
(Include this section for calculations or direct data lookups. Omit for qualitative/narrative questions.)
Provide the exact figures used, broken down by year/metric.

## Calculation
(Only include this section if a calculation was performed. Omit for direct lookups or qualitative questions.)
State the formula used, followed by a step-by-step substitution showing the actual numbers.

(For qualitative/narrative questions, instead of Details/Calculation, use clear thematic ## sub-headings as appropriate, e.g., ## Growth, ## Profitability, ## Risk, ## Outlook, ## Conclusion.)

## Sources
List each citation on its own line. Format each citation cleanly as:
<filename> · <sheet-or-page> · <year>
(Example: Craftsman Auto.xlsx · profit_loss · FY23)
Do NOT use raw log strings like 'Source: ... | Page/Sheet: ... | Year: ...'.

Formatting Rules:
- Do NOT output empty sections or "Not applicable" filler. If a section is not applicable, omit it entirely.
- Remove meta-prefixes like "Exact answer with units:". State the answer cleanly inside Summary/Details.
- Within sections, use prose or bullet lists naturally. Avoid markdown tables unless comparing multiple years of tabular data."""

    if mode == "calc":
        return f"""You are a senior financial analyst assistant helping a Chartered Accountant.
Use ONLY the context provided below to answer the question.

{structure_instructions}

Never guess — only use numbers explicitly present in context.
Do not convert ratios to percentages unless the formula explicitly multiplies by 100. Express ratios as decimals only.

Context:
{context}

Question: {question}

Answer:"""

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
- Never guess or approximate — only use numbers explicitly present in context

{structure_instructions}

Additional instructions for partial or truncated chunks:
- If a chunk appears cut off mid-sentence, use whatever numbers or facts are visible — do not ignore partial data
- If the exact figure is not stated but can be inferred from surrounding context, state clearly that it is inferred
- For MD&A narrative questions, look for management explanation text not just numbers — words like 'due to', 'owing to', 'because of', 'attributed to' signal the reason being sought
- For audit/KAM questions, look for Key Audit Matter headings and the description that follows immediately after
- If multiple chunks contain relevant partial information, synthesize them into one complete answer rather than reporting only from one chunk
- If the question asks you to identify a pattern, trend, discrepancy, or implication, state it explicitly - don't just restate the raw figures
- Before performing any calculation or extraction, explicitly state which time period/label each input value comes from, to avoid mixing up quarters, half-years, and full years
- Concall transcript chunks contain spoken dialogue; carefully identify the speaker and the specific segment/quarter being discussed before extracting figures
- When the question asks about a specific named financial ratio or metric, use that exact metric as stated - do not substitute a similar-sounding but different ratio (e.g. Interest Coverage Ratio is not the same as Debt Service Coverage Ratio; Return on Equity is not the same as Return on Net Worth)
- If the question has multiple parts or asks multiple things (e.g. 'what is X, and what does this indicate/imply/mean'), make sure every part is explicitly addressed in the answer - do not stop after answering only the first part

Context:
{context}

Question: {question}

Answer:"""