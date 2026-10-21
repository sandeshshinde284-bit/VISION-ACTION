# ============================================================================
# V.I.S.I.O.N. - RAG DATABASE STANDALONE DIAGNOSTIC PROBE
# ============================================================================
# File Description:
# This standalone script manually attempts to initialize the RAGService 
# outside of the FastAPI/Uvicorn server runtime. 
# It catches any exceptions and prints the complete, raw traceback to 
# isolate exactly why the ChromaDB or Vertex Embedding models are failing.
# ============================================================================

import sys
import os
import traceback

# Ensure the parent app directories are on the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

print("=" * 70)
print("LAUNCHING V.I.S.I.O.N. RAG DATABASE DIAGNOSTIC PROBE...")
print("=" * 70)

try:
    print("\n[STEP 1] Loading environment settings...")
    from app.core.config import settings
    print(f"-> Active Project ID: {settings.GCP_PROJECT_ID}")
    print(f"-> Active GCP Location: {settings.GCP_LOCATION}")

    print("\n[STEP 2] Attempting raw imports of dependencies...")
    import chromadb
    import pypdf
    import docx
    import vertexai
    from vertexai.language_models import TextEmbeddingModel
    print("-> All RAG libraries successfully imported.")

    print("\n[STEP 3] Attempting raw SQLite directory path validation...")
    DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))
    CHROMA_PATH = os.path.join(DATA_DIR, "chroma")
    print(f"-> Target Chroma DB Folder: {CHROMA_PATH}")
    os.makedirs(DATA_DIR, exist_ok=True)
    print("-> Folder creation checked out.")

    print("\n[STEP 4] Attempting local ChromaDB client initialization...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(name="vision_knowledge_base")
    print("-> Local ChromaDB successfully connected and SQLite initialized!")

    print("\n[STEP 5] Attempting Vertex AI SDK initialization...")
    vertexai.init(
        project=settings.GCP_PROJECT_ID,
        location=settings.GCP_LOCATION
    )
    print("-> Vertex AI core initialized.")

    print("\n[STEP 6] Attempting Google Text Embedding Model load (text-embedding-004)...")
    embedding_model = TextEmbeddingModel.from_pretrained("text-embedding-004")
    print("-> Vertex AI text-embedding-004 successfully cached and ready!")

    print("\n[STEP 7] Attempting mock vector generation...")
    vector = embedding_model.get_embeddings(["Test sentence"])[0].values
    print(f"-> Successfully generated mock vector! Coordinates: {len(vector)} dimensions.")

    print("\n" + "=" * 70)
    print("[SUCCESS] RAG SERVICE INFRASTRUCTURE IS 100% OPERATIONAL!")
    print("=" * 70)

except Exception as e:
    print("\n" + "!" * 70)
    print("[FAILURE] RAG SERVICE INITIALIZATION CRASHED!")
    print("!" * 70)
    print(f"\nError Class: {type(e).__name__}")
    print(f"Error Message: {e}")
    print("\nFull Stack Traceback:")
    traceback.print_exc()
    print("!" * 70)
