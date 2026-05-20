"""
DAY 2 — SCRIPT 1: ingest.py
=============================
What this does:
  1. Reads a REAL annual report PDF (not fake text anymore)
  2. Splits it into chunks
  3. Embeds each chunk
  4. Stores everything in Pinecone (persistent vector database)

Run this ONCE per document. After this, the vectors live in Pinecone
forever — even if you close Python, restart your laptop, or go to sleep.

HOW TO RUN:
  python ingest.py

BEFORE RUNNING:
  - Make sure infosys_2025.pdf is in your backend/ folder
  - Make sure PINECONE_API_KEY is in your .env file
  - pip install pinecone pypdf
"""

import os
import time
from dotenv import load_dotenv
from pypdf import PdfReader
from fastembed import TextEmbedding

from pinecone import Pinecone, ServerlessSpec

load_dotenv()

# ── Setup ──────────────────────────────────────────────────────
embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
pc         = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

INDEX_NAME = "alpharesearch"   # your Pinecone index name
DIMENSION  = 384               # all-MiniLM-L6-v2 produces 384-dim vectors


# ── Step 1: Create Pinecone index (only needed once ever) ──────

def create_index_if_not_exists():
    """
    A Pinecone index is like a database table for vectors.
    We create it once — after that it persists in the cloud.
    """
    existing = [idx.name for idx in pc.list_indexes()]
    if INDEX_NAME in existing:
        print(f"✅ Index '{INDEX_NAME}' already exists — skipping creation")
    else:
        print(f"Creating index '{INDEX_NAME}'...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric="cosine",          # we measure similarity with cosine
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"    # free tier region
            )
        )
        # Wait for index to be ready
        time.sleep(5)
        print(f"✅ Index created!")

    return pc.Index(INDEX_NAME)


# ── Step 2: Extract text from PDF ─────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Read every page of the PDF and join all text together.
    pypdf handles the parsing — we just collect the text.
    """
    print(f"\n📄 Reading PDF: {pdf_path}")
    reader = PdfReader(pdf_path)
    pages  = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():       # skip blank pages
            pages.append(text)
        if (i + 1) % 20 == 0:
            print(f"   Read {i + 1}/{len(reader.pages)} pages...")

    full_text = "\n".join(pages)
    print(f"✅ Extracted text from {len(reader.pages)} pages")
    print(f"   Total characters: {len(full_text):,}")
    return full_text


# ── Step 3: Chunk the text ─────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 150, overlap: int = 30) -> list[str]:
    """
    Split text into overlapping word-level chunks.

    chunk_size=150 words — big enough to have context,
    small enough to be specific when retrieved.

    overlap=30 words — sentences near boundaries appear
    fully in at least one chunk.
    """
    words  = text.split()
    chunks = []
    i      = 0

    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        if len(chunk.strip()) > 50:
            chunks.append(chunk.strip())
        i += chunk_size - overlap

    print(f"✅ Created {len(chunks)} chunks from the document")
    return chunks


# ── Step 4: Embed + upload to Pinecone ────────────────────────

def upsert_chunks(index, chunks: list[str], company: str = "infosys"):
    """
    Embed each chunk and upload to Pinecone.

    We upload in batches of 100 because Pinecone has a request size limit.
    Each vector has:
      - id: unique identifier
      - values: the 384-number embedding
      - metadata: the original text + company name (so we can filter later)
    """
    print(f"\n🔢 Embedding and uploading {len(chunks)} chunks to Pinecone...")
    batch_size = 100
    total_uploaded = 0

    for batch_start in range(0, len(chunks), batch_size):
        batch = chunks[batch_start: batch_start + batch_size]

        # Embed the whole batch at once (faster than one-by-one)
        embeddings = list(embedder.embed(batch))

        # Format for Pinecone: list of (id, vector, metadata) tuples
        vectors = [
            {
                "id":       f"{company}_chunk_{batch_start + i}",
                "values":   embedding.tolist(),
                "metadata": {
                    "text":    chunk,
                    "company": company,
                    "chunk_index": batch_start + i
                }
            }
            for i, (chunk, embedding) in enumerate(zip(batch, embeddings))
        ]

        index.upsert(vectors=vectors)
        total_uploaded += len(vectors)
        print(f"   Uploaded {total_uploaded}/{len(chunks)} chunks...")

    print(f"✅ All {total_uploaded} chunks stored in Pinecone!")


# ── Main ───────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("AlphaResearch — Bulk PDF Ingestion")
    print("=" * 60)

    # ── ADD YOUR PDFS HERE ────────────────────────────────────
    # Format: ("pdf_filename.pdf", "company_key")
    # company_key must be LOWERCASE and match TICKER_MAP exactly
    
    documents = [
        # Indian IT (placement companies)
        ("infosys_2025.pdf",      "infosys"),
        ("tcs_2025.pdf",          "tcs"),
        ("wipro_2025.pdf",        "wipro"),
        ("hcltech_2025.pdf",      "hcl tech"),
        ("accenture_2025.pdf",    "accenture"),

        # Indian Finance
        ("hdfc_2025.pdf",         "hdfc bank"),

        # Indian Other
        ("reliance_2025.pdf",     "reliance"),
        ("tatamotors_2025.pdf",   "tata motors"),
        ("zomato_2025.pdf",       "zomato"),

        # Global
        ("microsoft_2025.pdf",    "microsoft"),
        ("apple_2025.pdf",        "apple"),
        ("amazon_2025.pdf",         "amazon"),
        ("tesla_2025.pdf",          "tesla"),
        # Finance / Consulting
        ("wellsfargo_2025.pdf",     "wells fargo"),
        ("msci_2025.pdf",           "msci"),
         # Global Banking
        ("ubs_2025.pdf",            "ubs"),
        ("barclays_2025.pdf",       "barclays"),
        ("bny_2025.pdf",            "bny"),

    ]

    index = create_index_if_not_exists()

    for pdf_path, company in documents:
        if not os.path.exists(pdf_path):
            print(f"\n⚠️  Skipping '{pdf_path}' — file not found")
            continue

        print(f"\n{'═' * 60}")
        print(f"Processing: {company.upper()} ({pdf_path})")
        print(f"{'═' * 60}")

        text   = extract_text_from_pdf(pdf_path)
        chunks = chunk_text(text)
        upsert_chunks(index, chunks, company=company)

    stats = index.describe_index_stats()
    print(f"\n📊 Pinecone total vectors: {stats['total_vector_count']}")
    print("✅ All PDFs ingested!")
    index = create_index_if_not_exists()

    for pdf_path, company in documents:
        if not os.path.exists(pdf_path):
            print(f"\n⚠️  Skipping '{pdf_path}' — file not found")
            continue

        print(f"\n{'═' * 60}")
        print(f"Processing: {company.upper()} ({pdf_path})")
        print(f"{'═' * 60}")

        text   = extract_text_from_pdf(pdf_path)
        chunks = chunk_text(text)
        upsert_chunks(index, chunks, company=company)

    stats = index.describe_index_stats()
    print(f"\n📊 Pinecone total vectors: {stats['total_vector_count']}")
    print("✅ All PDFs ingested!")