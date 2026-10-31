# vector.py (FAISS version with lazy-loading and text chunking)

import os
from pathlib import Path
import logging

import PyPDF2
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# --- Paths ---
PDF_PATH = Path("mybuild_.pdf")
FAISS_DIR = Path("faiss_index")

_retriever = None
_store_initialized = False

def _load_and_chunk_pdf(pdf_path: Path):
    """Read pages from PDF and split into manageable chunks."""
    if not pdf_path.exists():
        logger.warning(f"PDF not found at: {pdf_path}")
        return []

    docs = []
    try:
        with pdf_path.open("rb") as f:
            reader = PyPDF2.PdfReader(f)
            for i, page in enumerate(reader.pages):
                text = (page.extract_text() or "").strip()
                if not text:
                    continue
                docs.append(
                    Document(
                        page_content=text,
                        metadata={"source": pdf_path.name, "page": i + 1},
                    )
                )
    except Exception as e:
        logger.error(f"Error reading PDF {pdf_path}: {e}")
        return []

    # Attempt to split documents into smaller chunks for improved retrieval
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = splitter.split_documents(docs)
        return chunks
    except ImportError:
        # Fallback if langchain_text_splitters is not installed
        return docs


def get_retriever():
    """Lazily load or build FAISS retriever to prevent crashing at import time."""
    global _retriever, _store_initialized
    if _store_initialized:
        return _retriever

    try:
        from langchain_ollama import OllamaEmbeddings
        from langchain_community.vectorstores import FAISS

        embeddings = OllamaEmbeddings(model="mxbai-embed-large")

        # If FAISS index exists on disk -> load it
        if FAISS_DIR.exists() and any(FAISS_DIR.iterdir()):
            print("🔁 Loading existing FAISS index from", FAISS_DIR)
            store = FAISS.load_local(
                str(FAISS_DIR),
                embeddings,
                allow_dangerous_deserialization=True,
            )
            _retriever = store.as_retriever(search_kwargs={"k": 5})
            _store_initialized = True
            return _retriever

        # Otherwise build new index if PDF exists
        if PDF_PATH.exists():
            print("📚 Building FAISS index from", PDF_PATH)
            chunks = _load_and_chunk_pdf(PDF_PATH)
            if chunks:
                store = FAISS.from_documents(chunks, embeddings)
                store.save_local(str(FAISS_DIR))
                print(f"✅ FAISS index created with {len(chunks)} chunks.")
                _retriever = store.as_retriever(search_kwargs={"k": 5})
                _store_initialized = True
                return _retriever

    except Exception as e:
        logger.warning(f"Could not initialize Ollama/FAISS vector store: {e}. AI Assistant will use baseline fallback.")

    _store_initialized = True
    _retriever = None
    return None
