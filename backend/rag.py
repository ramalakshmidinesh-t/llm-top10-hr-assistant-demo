import os
import chromadb
from pypdf import PdfReader
from docx import Document

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
# Use a default collection for HR documents
collection = chroma_client.get_or_create_collection(name="hr_documents")

def extract_text(file_path: str, filename: str) -> str:
    """Extract text based on file extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    elif ext == ".pdf":
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text
    elif ext == ".docx":
        doc = Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def add_document(filename: str, file_path: str):
    """Extract text from the file and store its chunks in ChromaDB."""
    text = extract_text(file_path, filename)
    # Split text into paragraphs (split by double newlines or single newlines with content)
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    
    if not paragraphs:
        return
        
    documents = []
    ids = []
    metadatas = []
    
    for i, p in enumerate(paragraphs):
        documents.append(p)
        ids.append(f"{filename}_{i}")
        metadatas.append({"source": filename, "chunk_index": i})
        
    collection.add(
        documents=documents,
        ids=ids,
        metadatas=metadatas
    )

def query_context(query: str, n_results: int = 3) -> str:
    """Retrieve relevant paragraphs from ChromaDB and join them."""
    # Check if collection is empty
    if collection.count() == 0:
        return ""
        
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count())
    )
    
    # Extract documents list from results
    documents_list = results.get("documents", [])
    if documents_list and len(documents_list) > 0:
        # Flatten documents and join them
        flat_docs = [doc for sublist in documents_list for doc in sublist]
        return "\n\n".join(flat_docs)
    return ""
