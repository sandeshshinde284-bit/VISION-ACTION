# ============================================================================
# PROJECT V.I.S.I.O.N. - PERSISTENT HYBRID LOCAL/CLOUD RAG SERVICE
# ============================================================================
# File Description:
# This service manages the semantic indexing pipeline, text chunking, Vertex AI
# batch embeddings, and queries both local ChromaDB and cloud PostgreSQL (pgvector)
# natively, depending on settings.DATABASE_TARGET configuration.
# ============================================================================

import os
import re
import logging
import requests
import json
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

# Configure clean logging
logger = logging.getLogger(__name__)

# Define platform-aware temporary document directory (Prevents serverless Cloud Run read-only disk crashes!)
if os.name != 'nt': # Running on Cloud Run (Linux/Unix container)
    TEMP_DIR = "/tmp/temp_docs"
else: # Running locally (Windows/Mac)
    TEMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "temp_docs"))
os.makedirs(TEMP_DIR, exist_ok=True)

class RAGService:
    """
    RAGService handles text extraction, chunk splitting, Vertex embedding,
    and semantic search calculations across local and cloud environments.
    """
    def __init__(self):
        """Initializes the database connections and ensures schema collections exist."""
        self.chroma_client = None
        self.collection = None
        
        # Initialize only if LOCAL is target to prevent local Chroma loading issues in production VMs
        if settings.DATABASE_TARGET == "LOCAL":
            try:
                # Store vectors inside secure data directory
                db_dir = os.path.abspath(settings.LOCAL_DB_DIR)
                os.makedirs(db_dir, exist_ok=True)
                
                self.chroma_client = chromadb.PersistentClient(path=db_dir)
                # Get or create the unique V.I.S.I.O.N. collection
                self.collection = self.chroma_client.get_or_create_collection("vision_knowledge_base")
                logger.info("Persistent local ChromaDB Client and Vector Collection initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize local ChromaDB client: {e}")
        else:
            logger.info("V.I.S.I.O.N. running in CLOUD database mode. Local ChromaDB initialization bypassed.")

    def _generate_embedding(self, text: str) -> list:
        """Invokes Google Vertex AI text-embeddings API to convert text to a 768-D coordinate vector."""
        try:
            url = f"https://{settings.GCP_LOCATION}-aiplatform.googleapis.com/v1/projects/{settings.GCP_PROJECT_ID}/locations/{settings.GCP_LOCATION}/publishers/google/models/text-embedding-004:predict"

            # Generate OAuth Bearer token dynamically using local OS ADC context (No hardcoded keys!)
            from app.services.security_service import security_service
            token = security_service.get_oauth_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Vertex AI REST parameters
            payload = {
                "instances": [{"content": text}]
            }

            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code != 200:
                logger.error(f"Vertex AI REST API failed: HTTP {res.status_code} - {res.text}")
                raise ValueError(f"Vertex AI REST API returned HTTP {res.status_code}")

            data = res.json()
            embedding = data["predictions"][0]["embeddings"]["values"]
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding via Vertex AI: {e}", exc_info=True)
            raise

    def _generate_embeddings_batch(self, texts: list) -> list:
        """Groups multiple text slices into a single HTTP request to avoid latency and rate blocks.
        Implements sub-batching to prevent exceeding Vertex AI's 20,000 token limit per payload.
        """
        try:
            url = f"https://{settings.GCP_LOCATION}-aiplatform.googleapis.com/v1/projects/{settings.GCP_PROJECT_ID}/locations/{settings.GCP_LOCATION}/publishers/google/models/text-embedding-004:predict"

            from app.services.security_service import security_service
            token = security_service.get_oauth_token()

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            all_vectors = []
            # Safe sub-batch size (15 chunks * ~350 tokens/chunk = ~5250 tokens per request)
            # Safely below the 20,000 Vertex AI limit.
            batch_size = 15

            for i in range(0, len(texts), batch_size):
                sub_batch_texts = texts[i:i + batch_size]
                instances = [{"content": text} for text in sub_batch_texts]
                payload = {"instances": instances}

                res = requests.post(url, headers=headers, json=payload, timeout=30)
                if res.status_code != 200:
                    logger.error(f"Vertex Batch REST API failed: HTTP {res.status_code} - {res.text}")
                    raise ValueError(f"Vertex Batch REST API returned HTTP {res.status_code}")

                response_data = res.json()
                predictions = response_data.get("predictions", [])

                for pred in predictions:
                    all_vectors.append(pred["embeddings"]["values"])

            return all_vectors
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings via Vertex AI: {e}", exc_info=True)
            raise

    def _parse_document(self, file_path: str) -> str:
        """Parses a local text file and returns its raw string context."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to parse text document: {e}")
            return ""

    def _chunk_text(self, text: str, chunk_size: int = 1500, overlap: int = 300) -> list:
        """: Semantic Recursive Text Splitter.
        Splits text progressively by semantic boundaries (Paragraphs -> Sentences -> Words)
        rather than blindly slicing strings mid-word or mid-table.
        Increased default chunk_size to 1500 and overlap to 300 for better contextual coherence.
        """
        if not text:
            return []

        chunks = []

        def split_recursively(text_to_split: str, separators: list) -> list:
            """Recursively split text based on the priority of separators."""
            if len(text_to_split) <= chunk_size:
                return [text_to_split]

            if not separators:
                # Absolute fallback: character split if we ran out of semantic separators
                result = []
                start = 0
                while start < len(text_to_split):
                    end = start + chunk_size
                    result.append(text_to_split[start:end])
                    start += (chunk_size - overlap)
                return result

            separator = separators[0]
            # Custom split to keep the separator attached to the preceding block for semantic flow
            # e.g., keep the period attached to the sentence.
            if separator == "\n\n" or separator == "\n":
                splits = text_to_split.split(separator)
                # Re-add separator for structural preservation in markdown
                splits = [s + separator for s in splits if s] 
            else:
                splits = [s + separator for s in text_to_split.split(separator) if s]

            # If a single split item is STILL too large, we must recurse deeper on that specific item
            # using the next level of separators (e.g. drop from Paragraphs down to Sentences)
            good_splits = []
            for s in splits:
                if len(s) > chunk_size:
                    good_splits.extend(split_recursively(s, separators[1:]))
                else:
                    good_splits.append(s)

            # Now combine the good, small splits into chunks up to our target chunk_size
            merged_chunks = []
            current_chunk = ""

            for s in good_splits:
                if len(current_chunk) + len(s) > chunk_size:
                    if current_chunk:
                        merged_chunks.append(current_chunk.strip())
                    # Overlap mechanism: Keep the last bit of the previous chunk for continuity
                    # In a semantic splitter, we want to grab roughly 'overlap' amount of text from the end
                    if len(current_chunk) > overlap:
                        # Find a clean boundary near the overlap limit to start the new chunk
                        overlap_start = len(current_chunk) - overlap
                        # Try to snap to the nearest space
                        space_idx = current_chunk.find(" ", overlap_start)
                        if space_idx != -1:
                            current_chunk = current_chunk[space_idx:].strip() + " " + s
                        else:
                            current_chunk = current_chunk[-overlap:] + s
                    else:
                        current_chunk = s
                else:
                    current_chunk += s

            if current_chunk:
                merged_chunks.append(current_chunk.strip())

            return merged_chunks

        # Priority separators: Double Newline (Markdown Paragraphs/Tables) -> Single Newline -> Sentence -> Space
        semantic_separators = ["\n\n", "\n", ". ", " "]
        return split_recursively(text, semantic_separators)

    def ingest_document(self, file_path: str, filename: str, custom_metadata: dict = None) -> bool:
        """Coordinates full document ingestion: parses text, chunks it, generates vectors, and indexes in active target DB."""
        # 1. Parse raw text
        text = self._parse_document(file_path)
        if not text:
            logger.warning(f"No text extracted from document: {filename}")
            return False

        try:
            # --- PRE-INGESTION AI PRIVACY GUARDRAIL (PHASE 3.3) ---
            from app.services.security_service import security_service
            safety_status = security_service.classify_text_safety(text)
            if safety_status == "RESTRICTED":
                logger.warning(f"DLP INTERCEPTOR: Aborting ingestion of [{filename}] due to sensitive data content.")
                raise ValueError("RESTRICTED_DATA_VIOLATION")

            # 2. Split into overlapping chunks
            chunks = self._chunk_text(text)
            if not chunks:
                return False

            # 3. Batch Generate Vertex Embeddings in a single, secure HTTP/REST request!
            logger.info(f"Generating Vertex embeddings for {len(chunks)} chunks in a single secure batch request...")
            vectors = self._generate_embeddings_batch(chunks)
            if len(vectors) != len(chunks):
                raise ValueError("Batch embeddings generation mismatch: vectors count does not match chunks count.")

            # --- SQLite RAW DOCUMENT STORE SAVE (ADR-004 Parent-Document Store) ---
            # Execute save ONLY after embeddings succeed to prevent invisible phantom files!
            if custom_metadata and "document_id" in custom_metadata:
                from app.services.db_service import db_service
                db_service.save_document(
                    document_id=custom_metadata["document_id"],
                    title=custom_metadata.get("title", filename),
                    content=text,
                    source_system=custom_metadata.get("source_system", "CONFLUENCE"),
                    space_key=custom_metadata.get("space_key", "UNKNOWN_SPACE"), # Do not default to GLOBAL
                    version=custom_metadata.get("version", 1) # Use dynamic version
                )
            
            # --- LOCAL vs. CLOUD STORAGE ROUTING (ADR-004) ---
            if settings.DATABASE_TARGET == "CLOUD":
                from app.services.db_service import db_service
                logger.info("ADR-004 CLOUD: Routing vector batch insertions to Cloud SQL PostgreSQL (pgvector)...")
                try:
                    with db_service._get_connection() as conn:
                        with conn.cursor() as cursor:
                            for i in range(len(chunks)):
                                chunk_id = f"{filename}_chunk_{i}"
                                vector_str = f"[{','.join(map(str, vectors[i]))}]"
                                metadata = {"source": filename, "chunk_index": i}
                                if custom_metadata:
                                    metadata.update(custom_metadata)
                                    
                                cursor.execute("""
                                    INSERT INTO knowledge_base (chunk_id, embedding, content, source_system, space_key, document_id)
                                    VALUES (%s, %s::vector, %s, %s, %s, %s)
                                    ON CONFLICT (chunk_id) DO UPDATE SET
                                        embedding=excluded.embedding,
                                        content=excluded.content,
                                        source_system=excluded.source_system,
                                        space_key=excluded.space_key,
                                        document_id=excluded.document_id
                                """, (
                                    chunk_id,
                                    vector_str,
                                    chunks[i],
                                    metadata.get("source_system", "CONFLUENCE"),
                                    metadata.get("space_key", "GLOBAL"),
                                    metadata.get("document_id")
                                ))
                            conn.commit()
                    logger.info(f"Knowledge Base Synced: Successfully indexed [{filename}] ({len(chunks)} vectors) in Cloud SQL PostgreSQL.")
                    return True
                except Exception as pg_err:
                    logger.error(f"Failed to batch load vectors into PostgreSQL Cloud SQL: {pg_err}")
                    return False
            else:
                # 4. Standard Local ChromaDB Indexing Loop
                if not self.collection:
                    logger.warning("RAG Database is offline, cannot ingest document.")
                    return False

                documents = []
                embeddings = []
                metadatas = []
                ids = []

                for idx, chunk in enumerate(chunks):
                    chunk_id = f"{filename}_chunk_{idx}"
                    vector = vectors[idx]
                    metadata = {"source": filename, "chunk_index": idx}
                    if custom_metadata:
                        metadata.update(custom_metadata)
                    
                    documents.append(chunk)
                    embeddings.append(vector)
                    metadatas.append(metadata)
                    ids.append(chunk_id)

                self.collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents
                )
                logger.info(f"Knowledge Base Synced: Successfully indexed [{filename}] ({len(chunks)} vectors) in local ChromaDB.")
                return True

        except Exception as e:
            logger.error(f"Failed to ingest document [{filename}] into RAG: {e}")
            return False

    def query_knowledge_base(self, query: str, top_k: int = 3, original_query: str = None) -> list:
        """
        Converts user query to an embedding, executes semantic vector search with thresholds,
        and returns top-K documents. Implements fallback logic if threshold filtering yields no results.
        
        # Fallback mechanism when strict thresholds return zero results.
        """
        results = []
        
        # Use the raw original query if provided to scan for explicit IDs. 
        # This completely prevents the Query Rewriter from accidentally locking out Confluence searches
        # when it mentions past ADO ticket IDs in its compiled contextual prompts!
        check_query = original_query if original_query else query
        
        # --- LOCAL vs. CLOUD STORAGE QUERY ROUTING (ADR-004) ---
        if settings.DATABASE_TARGET == "CLOUD":
            from app.services.db_service import db_service
            logger.info("ADR-004 CLOUD: Routing semantic vector query to PostgreSQL (pgvector)...")
            try:
                query_vector = self._generate_embedding(query)
                query_vector_str = f"[{','.join(map(str, query_vector))}]"
                
                with db_service._get_connection() as conn:
                    with conn.cursor() as cursor:
                        # pgvector distance operator: <=> represents cosine distance
                        # # Query ALL results, then filter in application layer for fallback logic
                        cursor.execute("""
                            SELECT kb.content, kb.document_id, kb.embedding <=> %s::vector AS distance, kb.source_system, kb.space_key, kb.chunk_id, d.title
                            FROM knowledge_base kb
                            LEFT JOIN documents d ON kb.document_id = d.document_id
                            ORDER BY kb.embedding <=> %s::vector
                            LIMIT %s
                        """, (query_vector_str, query_vector_str, top_k * 5))  # Fetch more to allow filtering + fallback
                        rows = cursor.fetchall()

                        # # Apply strict threshold filtering with fallback
                        strict_threshold = settings.RAG_DISTANCE_THRESHOLD  # 0.60 (60% similarity)
                        fallback_threshold = settings.RAG_DISTANCE_THRESHOLD + 0.15  # 0.75 (25% similarity) if needed

                        for row in rows:
                            distance = float(row[2])
                            # First pass: strict filtering
                            if distance <= strict_threshold:
                                results.append({
                                    "text": row[0],
                                    "metadata": {
                                        "document_id": row[1],
                                        "source": row[5].split("_chunk_")[0] if row[5] else "Unknown",
                                        "source_system": row[3],
                                        "space_key": row[4],
                                        "title": row[6] or "Unknown Title"
                                    },
                                    "distance": distance
                                })
                            # # If strict results are empty, use fallback threshold
                            elif len(results) == 0 and distance <= fallback_threshold:
                                results.append({
                                    "text": row[0],
                                    "metadata": {
                                        "document_id": row[1],
                                        "source": row[5].split("_chunk_")[0] if row[5] else "Unknown",
                                        "source_system": row[3],
                                        "space_key": row[4],
                                        "title": row[6] or "Unknown Title",
                                        "fallback_match": True  # Flag indicating fallback mode
                                    },
                                    "distance": distance
                                })

                        if len(results) == 0:
                            logger.warning(f"No results found even with fallback threshold {fallback_threshold}. Returning empty.")
                        elif any(r.get("metadata", {}).get("fallback_match") for r in results):
                            logger.info(f"Strict threshold returned zero results. Using fallback threshold: Retrieved {len(results)} documents.")
                        else:
                            logger.info(f"Cloud Search complete: Retrieved top {len(results)} relevant documents from PostgreSQL (strict threshold).")
                        
                        # Trim to top_k
                        results = results[:top_k]
                        
            except Exception as pg_q_err:
                logger.error(f"Cloud pgvector semantic search failed: {pg_q_err}")
            return results
            
        else:
            if not self.collection:
                logger.warning("RAG Database is offline, cannot execute query.")
                return results

            try:
                logger.info(f"Querying Knowledge Base semantically for: '{query}'")
                query_vector = self._generate_embedding(query)

                # Find any 5 to 6 digit ADO ticket IDs or 10-digit Confluence page IDs in the check_query
                explicit_ids_ado = re.findall(r'\b\d{5,6}\b', check_query)
                explicit_ids_conf = re.findall(r'\b\d{10}\b', check_query)

                where_filter = None
                if explicit_ids_ado or explicit_ids_conf:
                    filters = []
                    for exp_id in explicit_ids_ado:
                        filters.append({"document_id": f"ado_workitem_{exp_id}"})
                    for exp_id in explicit_ids_conf:
                        filters.append({"document_id": f"confluence_page_{exp_id}"})
                    
                    if len(filters) == 1:
                        where_filter = filters[0]
                    elif len(filters) > 1:
                        where_filter = {"$or": filters}
                    logger.info(f"Metadata pre-filtering active. Restricted search space to: {where_filter}")

                # # Fetch more results to enable fallback filtering
                search_results = self.collection.query(
                    query_embeddings=[query_vector],
                    n_results=top_k * 5,  # Fetch 15 instead of 3 to allow filtering + fallback
                    where=where_filter
                )

                if search_results and "documents" in search_results and search_results["documents"]:
                    docs = search_results["documents"][0]
                    metas = search_results["metadatas"][0] if "metadatas" in search_results else []
                    distances = search_results["distances"][0] if "distances" in search_results else []

                    # # Apply strict threshold with fallback
                    strict_threshold = settings.RAG_DISTANCE_THRESHOLD  # 0.60 (60% similarity)
                    fallback_threshold = settings.RAG_DISTANCE_THRESHOLD + 0.15  # 0.75 (25% similarity) if needed
                    used_fallback = False

                    for i in range(len(docs)):
                        distance = distances[i] if i < len(distances) else 0.0
                        # First pass: strict filtering
                        if distance <= strict_threshold:
                            results.append({
                                "text": docs[i],
                                "metadata": metas[i] if i < len(metas) else {},
                                "distance": distance
                            })
                        # # If strict results are empty, use fallback threshold
                        elif len(results) == 0 and distance <= fallback_threshold:
                            results.append({
                                "text": docs[i],
                                "metadata": {**(metas[i] if i < len(metas) else {}), "fallback_match": True},
                                "distance": distance
                            })
                            used_fallback = True

                    # Trim to top_k
                    results = results[:top_k]

                    if len(results) == 0:
                        logger.warning(f"No results found even with fallback threshold {fallback_threshold}. Knowledge base may be empty.")
                    elif used_fallback:
                        logger.info(f"Strict threshold returned zero results. Using fallback threshold: Retrieved {len(results)} documents.")
                    else:
                        logger.info(f"Search complete: Retrieved top {len(results)} relevant documents (strict threshold {strict_threshold}).")
                else:
                    logger.warning(f"Search returned no documents for query: '{query}'")
                    
            except Exception as e:
                logger.error(f"Semantic search failed: {e}")
            return results

    def purge_knowledge_base(self) -> bool:
        """Purges all index vectors from the active database engine."""
        if settings.DATABASE_TARGET == "CLOUD":
            from app.services.db_service import db_service
            logger.info("ADR-004 CLOUD: Purging Cloud PostgreSQL vector store...")
            try:
                with db_service._get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("TRUNCATE TABLE knowledge_base;")
                        conn.commit()
                logger.info("Cloud PostgreSQL vector store completely truncated.")
                return True
            except Exception as pg_p_err:
                logger.error(f"Failed to truncate PostgreSQL pgvector store: {pg_p_err}")
                return False
        else:
            if not self.chroma_client:
                return False
            try:
                self.chroma_client.delete_collection("vision_knowledge_base")
                self.collection = self.chroma_client.get_or_create_collection("vision_knowledge_base")
                logger.info("ChromaDB vector collection completely purged.")
                return True
            except Exception as e:
                logger.error(f"Failed to purge ChromaDB: {e}")
                return False

# Establish single, global instance for FastAPI import
rag_service = RAGService()
