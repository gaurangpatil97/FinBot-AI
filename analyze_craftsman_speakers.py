import re
from pathlib import Path
import pdfplumber
import sys

def analyze():
    pdf_dir = Path(r"d:\FinBot\backend\data\uploads\craftsman_automation_ltd\concall")
    if not pdf_dir.exists():
        print(f"Directory {pdf_dir} does not exist.")
        return
        
    pdfs = list(pdf_dir.glob("*.pdf"))
    if len(pdfs) == 0:
        print(f"No pdfs found in {pdf_dir}.")
        return
        
    print(f"Found {len(pdfs)} PDFs.")
    
    pattern = re.compile(r'^([A-Z][A-Za-z\s\.]+):\s+', re.MULTILINE)
    mgmt_names = ["srinivasan"]
    
    speakers_stats = {}
    
    for pdf_path in pdfs:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text:
                    continue
                
                matches = list(pattern.finditer(text))
                for j, match in enumerate(matches):
                    speaker = match.group(1).strip()
                    start = match.end()
                    end = matches[j + 1].start() if j + 1 < len(matches) else len(text)
                    content = text[start:end].strip()
                    
                    if not content:
                        continue
                        
                    is_mgmt = any(name in speaker.lower() for name in mgmt_names)
                    
                    if speaker not in speakers_stats:
                        speakers_stats[speaker] = {
                            "is_management": is_mgmt,
                            "answers_count": 0,
                            "total_words": 0
                        }
                    
                    # Count as "substantive answer" if length is somewhat long.
                    # Actually let's just count all occurrences for now, 
                    # we can filter out "Moderator" and brief remarks later.
                    words = len(content.split())
                    speakers_stats[speaker]["answers_count"] += 1
                    speakers_stats[speaker]["total_words"] += words

    print("\n--- Unique Speakers ---")
    for speaker, stats in sorted(speakers_stats.items(), key=lambda x: x[1]['answers_count'], reverse=True):
        avg_words = stats['total_words'] // stats['answers_count'] if stats['answers_count'] > 0 else 0
        role = "MANAGEMENT" if stats['is_management'] else "ANALYST"
        print(f"{role} | {speaker}: {stats['answers_count']} turns, ~{avg_words} words/turn")
        
if __name__ == '__main__':
    analyze()
