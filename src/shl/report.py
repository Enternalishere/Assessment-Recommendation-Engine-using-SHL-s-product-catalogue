from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import os

OUTPUT_DIR = "outputs"


def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_pdf(path: str):
    ensure_dirs()
    c = canvas.Canvas(path, pagesize=LETTER)
    width, height = LETTER
    y = height - 72
    lines = [
        "SHL Assessment Recommendation System - Approach",
        "",
        "Architecture:",
        "- Ingestion: Playwright + BeautifulSoup to scrape SHL catalog (>=377 items).",
        "- Storage: JSONL at data/catalog.jsonl; Chroma vector store with metadata.",
        "- Embeddings: sentence-transformers/all-MiniLM-L6-v2; cosine similarity.",
        "- Retrieval: Hybrid semantic + BM25 lexical; K/P balancing.",
        "- API: FastAPI /health, /recommend; minimal frontend index page.",
        "- Evaluation: Recall@10 on TRAIN from Gen_AI Dataset.xlsx; mean metric.",
        "- Predictions: TEST queries to CSV as Query,Assessment_URL.",
        "",
        "Scraping Strategy:",
        "- Discover product links from SHL Product Catalog and Kenexa pages.",
        "- Parse detail pages for name, type (K/P), description, skills.",
        "- Normalize URLs; deduplicate by URL hash; retries and robust selectors.",
        "",
        "RAG/LLM Choices:",
        "- Local embeddings for reliability; BM25 for exact keyword alignment.",
        "- Query processing accepts text/JD text/JD URL; cleans JD content.",
        "- Balancing favors both Knowledge/Skills and Personality/Behavior.",
        "",
        "Evaluation:",
        "- Recall@10 per query: |top10 ∩ ground_truth| / |ground_truth|.",
        "- Mean Recall@10 across TRAIN; logged to outputs/train_recall.csv.",
        "",
        "API & Output:",
        "- /recommend returns 5–10 items: name, url, type.",
        "- TEST predictions CSV: outputs/firstname_lastname.csv.",
        "",
        "Deployment:",
        "- Uvicorn serving FastAPI; persistent index under data/chroma.",
        "",
        "Notes:",
        "- Ensure scraping coverage >=377 assessments before indexing.",
        "- Re-run index after scrape to refresh embeddings.",
    ]
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
        if y < 72:
            c.showPage()
            y = height - 72
    c.save()

