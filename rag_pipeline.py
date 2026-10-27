import os
from pathlib import Path

import chromadb
from google import genai
from dotenv import load_dotenv
load_dotenv()

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

CHROMA_DIR = PROJECT_ROOT / ".chroma_db"

EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-2.5-flash"

SUPPORTED_FILES = {".md", ".txt", ".py", ".toml", ".yaml", ".yml", ".json"}

EXCLUDED_DIRS = {
    ".git", ".venv", ".chroma_db", "__pycache__",
    ".pytest_cache", "node_modules", "build",
}

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "Gemini API key is missing. Enter your key in the Streamlit sidebar."
        )

    return genai.Client(api_key=api_key)
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))

collection = chroma_client.get_or_create_collection(
    name="repolens_docs",
    metadata={"hnsw:space": "cosine"},
)


def read_documents():
    """Read supported project files without indexing secrets or generated files."""
    documents = []

    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_FILES:
            continue

        relative = path.relative_to(PROJECT_ROOT)

        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue

        if path.name.lower() in {".env", ".env.local", ".env.production"}:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        if text.strip():
            documents.append((relative.as_posix(), text))

    return documents


def chunk_text(text, chunk_size=1800, overlap=250):
    """Split text into overlapping character chunks."""
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks


def embed_texts(texts):
    client = get_gemini_client()
    """Create Gemini embeddings in small batches."""
    embeddings = []

    for text in texts:
        response = client.models.generate_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )

        if not response.embeddings:
            raise RuntimeError("Gemini returned no embedding.")

        embeddings.append(response.embeddings[0].values)

    return embeddings
    
def embed_texts(texts):
    """Create Gemini embeddings in small batches."""
    client = get_gemini_client()
    embeddings = []

    for text in texts:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )

        if not response.embeddings:
            raise RuntimeError("Gemini returned no embedding.")

        embeddings.append(response.embeddings[0].values)

    return embeddings



def index_repository():
    """Index repository documents into persistent ChromaDB."""
    documents = read_documents()

    if not documents:
        print("No supported documents found.")
        return

    ids, chunks, metadatas = [], [], []

    for filename, content in documents:
        for index, chunk in enumerate(chunk_text(content)):
            ids.append(f"{filename}::chunk-{index}")
            chunks.append(chunk)
            metadatas.append({
                "source": filename,
                "chunk": index,
            })

    # Replace the existing index so removed or changed files do not leave
    # stale chunks behind.
    existing = collection.get()
    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    batch_size = 20

    for start in range(0, len(chunks), batch_size):
        batch_chunks = chunks[start:start + batch_size]
        batch_ids = ids[start:start + batch_size]
        batch_metadata = metadatas[start:start + batch_size]

        vectors = embed_texts(batch_chunks)

        collection.add(
            ids=batch_ids,
            documents=batch_chunks,
            embeddings=vectors,
            metadatas=batch_metadata,
        )

    print(f"Indexed {len(chunks)} chunks from {len(documents)} files.")


def retrieve(question, top_k=4):
    """Retrieve the most relevant project documentation."""
    if collection.count() == 0:
        return []

    query_embedding = embed_texts([question])[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []

    for document, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        retrieved.append({
            "source": metadata["source"],
            "text": document,
            "distance": distance,
        })

    return retrieved


def answer_question(question, top_k=4):
    """Answer a question using retrieved repository evidence."""
    results = retrieve(question, top_k=top_k)

    if not results:
        return {
            "answer": (
                "No relevant repository evidence was found. "
                "Try rephrasing your question."
            ),
            "sources": [],
        }

    evidence = []
    sources = []

    for item in results:
        source = item["source"]
        evidence.append(
            f"Source: {source}\n"
            f"Content:\n{item['text']}"
        )

        if source not in sources:
            sources.append(source)

    sources.sort(
        key=lambda source: (
            source.startswith("tests/") or source.startswith("test_"),
            source.lower() == "readme.md",
            source,
        )
    )

    prompt = f"""
Answer the user's question using only the repository evidence below.

Rules:
- Be accurate and concise.
- Identify the primary implementation file when possible.
- Distinguish implementation files from tests and documentation.
- If the evidence does not support a claim, say so.
- Do not invent file names or code details.

Repository evidence:
{chr(10).join(evidence)}

Question: {question}

Answer:
"""

    client = get_gemini_client()

    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
    )

    return {
        "answer": response.text or "No answer was generated.",
        "sources": sources,
    }

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit(
            "GEMINI_API_KEY is missing. Set it in your environment or load it "
            "from your existing .env file."
        )

    index_repository()

    question = input("\nAsk a question about this repository: ").strip()

    if question:
        result = answer_question(question)
        print("\nAnswer:\n", result["answer"])
        print("\nSources:", ", ".join(result["sources"]))
