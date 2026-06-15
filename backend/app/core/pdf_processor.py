import os
import pdfplumber
import fitz
from pathlib import Path
from loguru import logger
import time

from config import settings
from app.core.metrics import OPENAI_CALL_LATENCY, OPENAI_CALL_COUNT

def extract_pdf(file_path: str) -> list[dict]:
    file_path = Path(file_path)
    filename = file_path.name
    pages_data = []

    logger.info(f"Processing PDF (text): {filename}")

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            width = page.width
            left = page.within_bbox((0, 0, width/2, page.height))
            right = page.within_bbox((width/2, 0, width, page.height))
            left_text = left.extract_text() or ""
            right_text = right.extract_text() or ""
            text = left_text + "\n" + right_text

            if text.strip():
                pages_data.append({
                    "content": text.strip(),
                    "metadata": {
                        "filename": filename,
                        "page": page_num,
                        "source": str(file_path),
                        "chunk_type": "text"
                    }
                })

    logger.success(f"Extracted {len(pages_data)} pages from {filename}")
    return pages_data


def describe_image(image_path: str, page_num: int) -> str:
    try:
        import base64
        import requests
        import time

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
        }

        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "You are analyzing an image of a page from a financial annual report. Extract only the financial data that is visually present in this image. Write your response as clear factual statements answering common financial questions. For example write: 'The total revenue was X crores. EBITDA was Y crores. Net profit was Z crores. Domestic revenue was X%. Export revenue was Y%.' Distinguish clearly between company-level totals and segment-level figures. Only include numbers and labels that are explicitly visible in the image."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }

        for attempt in range(3):
            start_t = time.time()
            try:
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                duration = time.time() - start_t
                
                if response.status_code == 429:
                    OPENAI_CALL_LATENCY.labels(model="gpt-4o", purpose="image_description").observe(duration)
                    OPENAI_CALL_COUNT.labels(model="gpt-4o", purpose="image_description", status="rate_limit").inc()
                    wait = 10 * (attempt + 1)
                    logger.warning(f"Rate limited on page {page_num}, waiting {wait}s...")
                    time.sleep(wait)
                    continue

                if response.status_code != 200:
                    OPENAI_CALL_LATENCY.labels(model="gpt-4o", purpose="image_description").observe(duration)
                    OPENAI_CALL_COUNT.labels(model="gpt-4o", purpose="image_description", status="error").inc()
                    logger.error(f"GPT-4o error on page {page_num}: {response.status_code} {response.text[:200]}")
                    return ""
                
                OPENAI_CALL_LATENCY.labels(model="gpt-4o", purpose="image_description").observe(duration)
                OPENAI_CALL_COUNT.labels(model="gpt-4o", purpose="image_description", status="success").inc()
            except Exception as e:
                duration = time.time() - start_t
                OPENAI_CALL_LATENCY.labels(model="gpt-4o", purpose="image_description").observe(duration)
                OPENAI_CALL_COUNT.labels(model="gpt-4o", purpose="image_description", status="error").inc()
                raise e

            result = response.json()
            description = result["choices"][0]["message"]["content"].strip()

            if len(description) < 20:
                return ""

            time.sleep(2)

            logger.info(f"GPT-4o described page {page_num}: {len(description)} chars")
            return description

        logger.error(f"GPT-4o failed after 3 attempts on page {page_num}")
        return ""

    except Exception as e:
        logger.error(f"GPT-4o failed on page {page_num}: {e}")
        return ""


def extract_images_from_pdf(file_path: str) -> list[dict]:
    file_path = Path(file_path)
    filename = file_path.name

    if not settings.ENABLE_IMAGE_EMBEDDING:
        logger.warning(
            f"ENABLE_IMAGE_EMBEDDING is False — skipping image embedding for {filename}. Text embeddings will proceed normally."
        )
        return []

    if not settings.OPENAI_API_KEY:
        logger.warning(
            f"OPENAI_API_KEY not set — skipping image embedding for {filename}. Text embeddings will proceed normally."
        )
        return []

    pages_data = []
    tmp_dir = settings.TMP_DIR
    os.makedirs(tmp_dir, exist_ok=True)

    logger.info(f"Processing PDF (images): {filename}")

    doc_fitz = fitz.open(str(file_path))

    for page_num in range(len(doc_fitz)):
        page_fitz = doc_fitz[page_num]
        page_display_num = page_num + 1
        images = page_fitz.get_images()

        if not images:
            continue

        try:
            matrix = fitz.Matrix(300 / 72, 300 / 72)
            pix = page_fitz.get_pixmap(matrix=matrix)

            if pix.colorspace and pix.colorspace != fitz.csRGB:
                pix = fitz.Pixmap(fitz.csRGB, pix)

            img_path = f"{tmp_dir}/page_{page_display_num}.png"
            pix.save(img_path)

            description = describe_image(img_path, page_display_num)

            try:
                os.remove(img_path)
            except:
                pass

            if description:
                pages_data.append({
                    "content": f"[IMAGE CONTENT - Page {page_display_num}]\n{description}",
                    "metadata": {
                        "filename": filename,
                        "page": page_display_num,
                        "source": str(file_path),
                        "chunk_type": "image"
                    }
                })
        except Exception as e:
            logger.error(f"Failed to render page {page_display_num}: {e}")
            continue

    doc_fitz.close()
    logger.success(f"Extracted image descriptions from {len(pages_data)} pages in {filename}")
    return pages_data