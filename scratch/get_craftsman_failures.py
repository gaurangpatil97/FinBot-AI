import json
from pathlib import Path

def check_routing(actual_routing, expected_routing):
    if not expected_routing: return not actual_routing
    if isinstance(expected_routing, str): expected_list = [expected_routing]
    else: expected_list = list(expected_routing)
    if isinstance(actual_routing, str): actual_list = [actual_routing]
    else: actual_list = list(actual_routing)
    expected_set = {str(x).strip().lower() for x in expected_list}
    actual_set = {str(x).strip().lower() for x in actual_list}
    return expected_set.issubset(actual_set)

def check_citation(actual_citations, expected_sources):
    if not expected_sources: return True
    if isinstance(expected_sources, str): expected_list = [expected_sources]
    else: expected_list = list(expected_sources)
    if not actual_citations: return False
    
    def normalize(text): return text.replace(" ", "").replace("_", "")

    citation_strings = []
    for c in actual_citations:
        if isinstance(c, dict):
            fname = c.get("filename") or c.get("source_url") or c.get("source_uri") or ""
            col = c.get("collection") or ""
            citation_strings.append(normalize(str(fname).lower()))
            if col: citation_strings.append(normalize(str(col).lower()))
        else:
            citation_strings.append(normalize(str(c).lower()))
            
    citations_combined = " ".join(citation_strings)
    
    for expected in expected_list:
        expected_raw = str(expected).lower()
        expected_clean = Path(expected_raw).name
        if normalize(expected_clean) in citations_combined or normalize(expected_raw) in citations_combined:
            return True
    return False

results_file = Path(r"d:\FinBot\benchmarks\runs\run_001\craftsman_automation_ltd_results.json")
with open(results_file, "r", encoding="utf-8") as f:
    data = json.load(f)

count = 0
for r in data.get("results", []):
    if r.get("section") != "Concall":
        continue
    expected_rout = r.get("expected_routing", [])
    actual_rout = r.get("collections_searched", [])
    expected_src = r.get("expected_source", [])
    actual_cit = r.get("citations", [])

    routing_correct = check_routing(actual_rout, expected_rout)
    citation_correct = check_citation(actual_cit, expected_src)

    if routing_correct and not citation_correct:
        print(f"ID: {r.get('id')}")
        print(f"Question: {r.get('question')}")
        print(f"Expected Source: {expected_src}")
        actual_filenames = [c.get("filename") for c in actual_cit if isinstance(c, dict)]
        print(f"Actual Citation Filenames: {actual_filenames}")
        print("-" * 50)
        count += 1
        if count == 5:
            break
