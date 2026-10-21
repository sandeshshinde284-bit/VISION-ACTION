# /backend/sync_connectors.py

# ==============================================================================
# SECURE CORPORATE SSL BRIDGE - BYPASSES ZSCALER BY FORCING HTTP/REST OVER gRPC
# ==============================================================================
import os
import certifi
import pip_system_certs.wrapt_requests

# Force Google Cloud SDK to use standard HTTP/REST transport instead of gRPC.
# This makes it use Python's requests layer which is 100% patched by pip-system-certs!
os.environ["GOOGLE_CLOUD_DISABLE_GRPC"] = "true"

certifi_path = certifi.where()
os.environ["SSL_CERT_FILE"] = certifi_path
os.environ["REQUESTS_CA_BUNDLE"] = certifi_path

pip_system_certs.wrapt_requests.inject_truststore()
# ==============================================================================

import sys
import logging
import re
import requests
import time
import contextlib
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

# Ensure we can import app modules cleanly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.rag_service import rag_service
from app.services.security_service import security_service

# Initialize logger
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] - %(message)s")
logger = logging.getLogger("VisionConnectors")

# Use OS-agnostic temp directory
TEMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "temp_docs"))
os.makedirs(TEMP_DIR, exist_ok=True)

# ============================================================================
# Issue #6 Fix: Context Manager for Safe Temporary File Handling
# ============================================================================

@contextlib.contextmanager
def temp_confluence_document(filename: str):
    """
    Context manager for guaranteed temporary file cleanup.
    Ensures files are deleted even if ingestion fails mid-process.
    
    Usage:
        with temp_confluence_document(filename) as temp_file_path:
            with open(temp_file_path, "w") as f:
                f.write(content)
            rag_service.ingest_document(temp_file_path, filename)
            # Cleanup guaranteed even if exception occurs above
    """
    temp_file_path = os.path.join(TEMP_DIR, filename)
    try:
        yield temp_file_path
    finally:
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {filename}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {filename}: {e}")

def _mask_sensitive_log(text: str) -> str:
    """Scrubs log outputs to prevent leaking Personal Access Tokens (PATs)
    or corporate email addresses into the console/file logs.
    """
    if not text or not isinstance(text, str):
        return ""
    # Mask Base64 strings that look like Azure DevOps or Confluence PAT tokens
    masked = re.sub(r'[a-zA-Z0-9+/]{40,}={0,2}', '[TOKEN_REDACTED]', text)
    # Mask basic email structures
    masked = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[EMAIL_REDACTED]', masked)
    # Ensure ADO Organization / Confluence URL domains aren't leaked in raw tracebacks
    if settings.ADO_URL:
        ado_domain = settings.ADO_URL.replace('https://', '').replace('http://', '').strip('/')
        if ado_domain: masked = masked.replace(ado_domain, '[ADO_ORG_REDACTED]')
    return masked

def convert_html_to_markdown(html_text: str) -> str:
    """
    Helper that executes structural HTML to Markdown parsing via html2text.
    Replaces custom HTMLToMarkdownParser to resolve Issues 1.1, 1.2, 1.3, & 1.4 (Data Loss).
    Preserves tables, lists, code blocks, macros, and images perfectly.
    """
    if not html_text:
        return ""
    try:
        import html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.body_width = 0 # Don't wrap text aggressively
        h.ignore_images = False # Keep image references for diagrams
        h.protect_links = True
        
        markdown_text = h.handle(html_text)
        # Squeeze multiple newlines cleanly
        text = re.sub(r'\n{3,}', '\n\n', markdown_text).strip()
        return text
    except Exception as e:
        logger.warning(f"Native HTML to Markdown conversion failed: {e}")
        # Graceful fallback to regex if html2text isn't installed
        clean = re.sub(r'<[^>]+>', ' ', html_text)
        return re.sub(r'\s+', ' ', clean).strip()


def get_ado_comments(item_id: str) -> str:
    """
    Performs an authenticated REST call against ADO to fetch the discussion history
    for a work item, returning the 3 most recent comments formatted as Markdown.
    """
    url = settings.ADO_URL.rstrip('/')
    pat = settings.ADO_PAT.strip()
    
    # Standard endpoint to pull comments thread history
    api_endpoint = f"{url}/_apis/wit/workItems/{item_id}/comments?api-version=7.0-preview.3"
    
    try:
        res = requests.get(api_endpoint, auth=("", pat), timeout=10)
        if res.status_code != 200:
            return ""
            
        payload = res.json()
        comments = payload.get("comments", [])
        if not comments:
            return ""
            
        # Segment out the last 3 comments
        recent_comments = comments[-3:]
        comments_md = "\n### Recent Discussion History:\n"
        
        for c in recent_comments:
            author = c.get("createdBy", {}).get("displayName", "System")
            date_str = c.get("createdDate", "")
            
            # Formulate clear date tags (YYYY-MM-DD)
            if date_str:
                date_str = date_str[:10]
                
            raw_html = c.get("text", "")
            clean_comment = convert_html_to_markdown(raw_html)
            comments_md += f"* **{author}** ({date_str}): {clean_comment}\n"
            
        return comments_md
    except Exception as e:
        logger.warning(f"Could not retrieve discussion comments for ADO Work Item [{item_id}]: {e}")
    return ""


def _generate_document_summary(content: str) -> str:
    """Invokes a fast, stateless Gemini Flash call to generate a concise, 2-sentence summary of the document for rapid retrieval."""
    try:
        from vertexai.generative_models import GenerativeModel
        model = GenerativeModel(settings.GEMINI_MODEL)
        prompt = (
            "Summarize the core purpose and key architectural deliverables of the following technical document in exactly 2 professional sentences. "
            "Do not include any conversational filler, introductory words, or markdown lists. Write a single, solid paragraph.\n\n"
            f"Document Content:\n{content[:8000]}" # Guard token window constraints
        )
        response = model.generate_content([prompt])
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        logger.warning(f"Failed to generate dynamic LLM summary of document: {e}")
    return "No summary available."


def sync_confluence_page(page_id: str):
    """
    Performs an authenticated REST call against live Confluence, extracts page content,
    generates a 2-sentence summary, parses diagram images, and indexes it semantically.
    """
    url = settings.CONFLUENCE_URL.rstrip('/')
    pat = settings.CONFLUENCE_PAT.strip()

    if not url or not pat:
        logger.error("Confluence configurations (URL/PAT) are missing from .env!")
        return False

    # Issues 10.1 & 10.2 Fix: Expand restrictions.read and version.by for security and authorship metadata
    api_endpoint = f"{url}/wiki/rest/api/content/{page_id}?expand=body.storage,version,space,restrictions.read.restrictions.user,version.by"
    logger.info(f"Initiating live Confluence sync for Page ID [{page_id}]...")

    headers = {}
    auth = None

    # Handle Cloud (email:api_token) vs On-Premise Bearer Token
    if ":" in pat:
        email, token = pat.split(":", 1)
        auth = (email, token)
    else:
        headers["Authorization"] = f"Bearer {pat}"

    try:
        res = requests.get(api_endpoint, headers=headers, auth=auth, timeout=15)
        if res.status_code != 200:
            logger.error(f"Confluence API failure: HTTP {res.status_code} - {res.text}")
            return False

        data = res.json()
        title = data.get("title", f"Confluence Page {page_id}")
        
        # 🛡️ SECURITY GUARDRAIL: Block Restricted Pages
        restrictions = data.get("restrictions", {}).get("read", {}).get("restrictions", {}).get("user", {}).get("results", [])
        if restrictions:
            logger.warning(f"SECURITY BLOCK: Skipping Page [{title}]. Document is RESTRICTED and confidential.")
            return False

        html_body = data.get("body", {}).get("storage", {}).get("value", "")
        
        # Issue #1, #10, #10.1 Fix: Extract live Space Key, Document Version, and Author
        live_version = data.get("version", {}).get("number", 1)
        author = data.get("version", {}).get("by", {}).get("displayName", "System User")
        space_key = data.get("space", {}).get("key", "UNKNOWN_SPACE")

        # Parse raw HTML into clean Markdown structure (capturing diagram image links!)
        markdown_text = convert_html_to_markdown(html_body)
        full_content = f"Confluence Page Title: {title}\nSpace Key: {space_key}\nVersion: v{live_version}\nAuthor: {author}\n\nPage Content:\n{markdown_text}"

        # Generate a high-speed, 2-sentence document summary
        logger.info("Generating dynamic 2-sentence summary...")
        doc_summary = _generate_document_summary(full_content)

        # --- ISSUE #D FIX: Check if document was recently synced to prevent duplicates ---
        document_id = f"confluence_page_{page_id}"
        from app.services.db_service import db_service
        if db_service.is_recently_synced(document_id, "CONFLUENCE", min_age_minutes=30):
            logger.info(f"Skipping Confluence page [{page_id}] - already synced within last 30 minutes (dedup logic)")
            return True  # Not an error, just skipped

        # Record sync start for tracking
        db_service.record_sync_start(document_id, "CONFLUENCE", "full_page_sync")
        
        # Issue #6 Fix: Use context manager for guaranteed cleanup
        with temp_confluence_document(filename) as temp_file_path:
            with open(temp_file_path, "w", encoding="utf-8") as tf:
                tf.write(full_content)

            # Ingest document securely into vector store with enriched metadata
            logger.info(f"Injecting page text into RAG pipeline...")
            from datetime import datetime
            sync_timestamp = datetime.utcnow().isoformat()
            custom_metadata = {
                "document_id": f"confluence_page_{page_id}",
                "title": title,
                "source_system": "CONFLUENCE",
                "space_key": space_key,
                "summary": doc_summary,
                "status": "Active",
                "doc_type": "Confluence",
                "version": live_version,
                "author": author,
                "last_synced_at": sync_timestamp,
                "confluence_version": live_version
            }
            success = rag_service.ingest_document(temp_file_path, filename, custom_metadata=custom_metadata)
            
            # Store in database with freshness tracking
            if success:
                from app.services.db_service import db_service
                db_service.save_document(
                    document_id=document_id,
                    title=title,
                    content=full_content,
                    source_system="CONFLUENCE",
                    space_key=space_key,
                    summary=doc_summary,
                    status="Active",
                    doc_type="Confluence",
                    version=live_version,
                    last_synced_at=sync_timestamp,
                    confluence_version=live_version
                )
                # --- ISSUE #D FIX: Record sync completion ---
                db_service.record_sync_complete(
                    document_id=document_id,
                    source_system="CONFLUENCE",
                    chunk_count=len(full_content.split("\n")),
                    vector_count=1  # 1 document synced
                )
                logger.info(f"Synchronized updated Confluence page: [{title}]")
                return True
            else:
                # --- ISSUE #D FIX: Record sync failure ---
                db_service.record_sync_complete(
                    document_id=document_id,
                    source_system="CONFLUENCE",
                    chunk_count=0,
                    vector_count=0,
                    error="Failed to ingest document into RAG service"
                )
                logger.error(f"Failed to synchronize Confluence Page [{title}].")
                return False
            # Cleanup is GUARANTEED by context manager even if exception occurs

    except Exception as e:
        logger.exception(f"Critical crash during Confluence Page [{page_id}] synchronization")
        return False


def sync_recent_confluence_pages(minutes: int = 30):
    """
    Queries Confluence for all pages modified in the last N minutes using CQL,
    and automatically indexes them into the vector database.
    """
    url = settings.CONFLUENCE_URL.rstrip('/')
    pat = settings.CONFLUENCE_PAT.strip()

    if not url or not pat:
        logger.error("Confluence configurations (URL/PAT) are missing from .env!")
        return 0

    # Confluence CQL now() only supports h (hours), d (days), w (weeks) - it does NOT support m (minutes)!
    # We convert minutes to hours to ensure absolute Atlassian API compliance.
    hours = max(1, minutes // 60)
    cql = f'type="page" AND lastmodified >= now("-{hours}h")'
    api_endpoint = f"{url}/wiki/rest/api/search"
    logger.info(f"Polling Confluence for updates in the last [{hours}] hours using CQL...")

    headers = {}
    auth = None

    # Handle Cloud (email:api_token) vs On-Premise Bearer Token
    if ":" in pat:
        email, token = pat.split(":", 1)
        auth = (email, token)
    else:
        headers["Authorization"] = f"Bearer {pat}"

    try:
        # Pass parameters via requests' params dict to ensure correct URL encoding
        params = {
            "cql": cql,
            "expand": "content.body.storage,content.version,content.space", # Fetch version and space
            "limit": 50
        }
        res = requests.get(api_endpoint, headers=headers, auth=auth, params=params, timeout=20)
        if res.status_code != 200:
            logger.error(f"Confluence Search API failure: HTTP {res.status_code} - {res.text}")
            return 0

        payload = res.json()
        results = payload.get("results", [])
        logger.info(f"Found [{len(results)}] Confluence pages modified in the last [{minutes}] minutes.")

        sync_count = 0
        for item in results:
            content = item.get("content", {})
            page_id = content.get("id")
            title = content.get("title", f"Page {page_id}")
            status = content.get("status", "current")
            
            #& 1.6 Fix: Dynamically extract space_key and version
            live_version = content.get("version", {}).get("number", 1)
            space_key = content.get("space", {}).get("key", "UNKNOWN_SPACE")

            # Data Hygiene: Reject archived, draft, or trashed pages
            if status in ["archived", "draft", "trashed"]:
                logger.info(f"Skipping page [{title}] due to document status: [{status}]")
                continue

            html_body = content.get("body", {}).get("storage", {}).get("value", "")

            # Parse raw HTML into clean Markdown structure (capturing diagram image links!)
            markdown_text = convert_html_to_markdown(html_body)
            full_content = f"Confluence Page Title: {title}\nSpace Key: {space_key}\nVersion: v{live_version}\n\nPage Content:\n{markdown_text}"

            # Generate summary
            logger.info("Generating dynamic 2-sentence summary...")
            doc_summary = _generate_document_summary(full_content)

            # --- ISSUE #D FIX: Check if document was recently synced to prevent duplicates ---
            document_id = f"confluence_page_{page_id}"
            from app.services.db_service import db_service
            if db_service.is_recently_synced(document_id, "CONFLUENCE", min_age_minutes=30):
                logger.info(f"Skipping Confluence page [{title}] - already synced within last 30 minutes (dedup logic)")
                continue  # Skip this page

            # Record sync start for tracking
            db_service.record_sync_start(document_id, "CONFLUENCE", "delta_sync")

            # Write to temporary file
            filename = f"confluence_page_{space_key}_{page_id}.txt"
            
            # Issue #6 Fix: Use context manager for guaranteed cleanup
            with temp_confluence_document(filename) as temp_file_path:
                with open(temp_file_path, "w", encoding="utf-8") as tf:
                    tf.write(full_content)

                # Ingest securely with freshness tracking
                from datetime import datetime
                sync_timestamp = datetime.utcnow().isoformat()
                custom_metadata = {
                    "document_id": f"confluence_page_{page_id}",
                    "title": title,
                    "source_system": "CONFLUENCE",
                    "space_key": space_key,
                    "summary": doc_summary,
                    "status": "Active",
                    "doc_type": "Confluence",
                    "version": live_version,
                    "last_synced_at": sync_timestamp,
                    "confluence_version": live_version
                }
                success = rag_service.ingest_document(temp_file_path, filename, custom_metadata=custom_metadata)
                
                # Store in database with freshness tracking
                if success:
                    from app.services.db_service import db_service
                    db_service.save_document(
                        document_id=document_id,
                        title=title,
                        content=full_content,
                        source_system="CONFLUENCE",
                        space_key=space_key,
                        summary=doc_summary,
                        status="Active",
                        doc_type="Confluence",
                        version=live_version,
                        last_synced_at=sync_timestamp,
                        confluence_version=live_version
                    )
                    # --- ISSUE #D FIX: Record sync completion ---
                    db_service.record_sync_complete(
                        document_id=document_id,
                        source_system="CONFLUENCE",
                        chunk_count=len(full_content.split("\n")),
                        vector_count=1
                    )
                    logger.info(f"Synchronized updated Confluence page: [{title}]")
                    sync_count += 1
                else:
                    # --- ISSUE #D FIX: Record sync failure ---
                    db_service.record_sync_complete(
                        document_id=document_id,
                        source_system="CONFLUENCE",
                        chunk_count=0,
                        vector_count=0,
                        error="Failed to ingest document into RAG service"
                    )
                # Cleanup is GUARANTEED by context manager even if exception occurs

        return sync_count

    except Exception as e:
        logger.exception("Critical crash during Confluence delta synchronization")
        return 0


def sync_ado_workitem(item_id: str):
    """
    Performs Hybrid Ingestion (ADR-004) against live Azure DevOps.
    Saves the full detailed comments and specifications inside the SQLite document store for collapsing,
    but indexes strictly a lightweight, high-density metadata string in ChromaDB for semantic discovery
    without database bloat.
    """
    url = settings.ADO_URL.rstrip('/')
    pat = settings.ADO_PAT.strip()

    if not url or not pat:
        logger.error("ADO configurations (URL/PAT) are missing from .env!")
        return False

    api_endpoint = f"{url}/_apis/wit/workitems/{item_id}?api-version=7.0"
    logger.info(f"Initiating live Azure DevOps sync for Work Item ID [{item_id}]...")

    try:
        # ADO expects HTTP Basic authentication with empty username and PAT as password
        res = requests.get(api_endpoint, auth=("", pat), timeout=15)
        if res.status_code != 200:
            logger.error(f"ADO API failure: HTTP {res.status_code} - {res.text}")
            return False

        data = res.json()
        fields = data.get("fields", {})
        
        title = fields.get("System.Title", f"Work Item {item_id}")
        item_type = fields.get("System.WorkItemType", "Task")
        state = fields.get("System.State", "Unknown")
        assigned_to = fields.get("System.AssignedTo", {}).get("displayName", "Unassigned")
        project_name = fields.get("System.TeamProject", "GLOBAL")
        description = fields.get("System.Description", "")
        repro_steps = fields.get("Microsoft.TCM.ReproSteps", fields.get("Microsoft.VSTS.TCM.ReproSteps", ""))

        # Clean HTML fields into structured Markdown preserving format
        clean_desc = convert_html_to_markdown(description)
        clean_repro = convert_html_to_markdown(repro_steps)
        
        # Fetch the active discussion comments thread (ADR-004 Spec 2)
        comments_md = get_ado_comments(item_id)

        #: Dynamically extract ADO Revision as version
        live_version = fields.get("System.Rev", 1)

        # Build our full detailed Object-Graph Markdown profile for collapsing RAG
        full_content = (
            f"### 🐛 Azure DevOps Work Item #{item_id}\n"
            f"- **Title:** {title}\n"
            f"- **Type:** {item_type}\n"
            f"- **Status:** {state}\n"
            f"- **Assigned To:** {assigned_to}\n"
            f"- **Project Name:** {project_name}\n"
            f"- **Revision:** v{live_version}\n\n"
            f"#### Description:\n{clean_desc}\n\n"
        )
        if clean_repro:
            full_content += f"#### Reproduction Steps:\n{clean_repro}\n\n"
        if comments_md:
            full_content += comments_md

        # --- STEP 2.C: HYBRID ADO INDEX (PREVENTS DATABASE BLOAT) ---
        # Instead of storing the full description and comments inside ChromaDB,
        # we generate a compact, dense, and lightweight semantic indexing string.
        # This keeps the vector database ultra-slim while enabling perfect semantic discovery!
        semantic_index_string = (
            f"ADO Ticket ID: #{item_id} | Title: {title} | Type: {item_type} | "
            f"Project: {project_name} | State: {state} | Assigned To: {assigned_to}"
        )

        # Write the semantic index string to temporary document in cache for vectorization
        filename = f"ado_workitem_{item_id}.txt"
        
        # Issue #6 Fix: Use context manager for guaranteed cleanup
        with temp_confluence_document(filename) as temp_file_path:
            with open(temp_file_path, "w", encoding="utf-8") as tf:
                tf.write(semantic_index_string)

            # Ingest the lightweight string to ChromaDB, but pass the FULL detailed content to the documents store!
            logger.info(f"Injecting lightweight ADO metadata index to RAG database...")
            custom_metadata = {
                "document_id": f"ado_workitem_{item_id}",
                "title": f"ADO Item #{item_id}: {title}",
                "source_system": "ADO",
                "space_key": project_name,
                "summary": title,
                "status": state,
                "doc_type": item_type,
                "version": live_version
            }
            
            # To pass the full content to parent-document collapsing, we temporarily hijack the ingest_document pipeline:
            # We manually save the full content in SQLite first, then ingest the lightweight file to ChromaDB!
            from app.services.db_service import db_service
            db_service.save_document(
                document_id=custom_metadata["document_id"],
                title=custom_metadata["title"],
                content=full_content, # The FULL specification is saved in SQLite for parent collapsing!
                source_system="ADO",
                space_key=project_name,
                summary=title,
                status=state,
                doc_type=item_type,
                version=live_version
            )
            
            # Ingest the lightweight semantic string file into ChromaDB!
            success = rag_service.ingest_document(temp_file_path, filename, custom_metadata=custom_metadata)
            
            if success:
                logger.info(f"Successfully synchronized ADO Work Item [{title}]!")
                return True
            else:
                logger.error(f"Failed to synchronize ADO Work Item [{title}].")
                return False
            # Cleanup is GUARANTEED by context manager even if exception occurs

    except Exception as e:
        logger.exception(f"Critical crash during ADO Work Item [{item_id}] synchronization")
        return False


def sync_recent_ado_items(minutes: int = 30):
    """
    Queries Azure DevOps using WIQL to find all tickets modified in the last N minutes,
    and automatically indexes them.
    """
    url = settings.ADO_URL.rstrip('/')
    pat = settings.ADO_PAT.strip()

    if not url or not pat:
        logger.error("ADO configurations (URL/PAT) are missing from .env!")
        return 0

    # Calculate date threshold in YYYY-MM-DD format as WIQL requires Date Precision
    since_date = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).strftime("%Y-%m-%d")
    
    # Scope crawls strictly Project-by-Project (supports comma-separated multi-projects!)
    project_filter = ""
    project_raw = getattr(settings, "ADO_PROJECT", "").strip()
    if project_raw:
        # Split by comma and strip whitespaces
        projects = [p.strip() for p in project_raw.split(",") if p.strip()]
        if len(projects) == 1:
            project_filter = f" AND [System.TeamProject] = '{projects[0]}'"
            logger.info(f"Scoping ADO WIQL query to single Project: [{projects[0]}]")
        elif len(projects) > 1:
            # Format into WIQL-compliant IN list, e.g. IN ('proj-1', 'proj-2')
            in_list = ", ".join([f"'{p}'" for p in projects])
            project_filter = f" AND [System.TeamProject] IN ({in_list})"
            logger.info(f"Scoping ADO WIQL query to multiple Projects: {projects}")
        
    wiql_query = f"SELECT [System.Id] FROM WorkItems WHERE [System.ChangedDate] >= '{since_date}'{project_filter}"

    api_endpoint = f"{url}/_apis/wit/wiql?api-version=7.0"
    logger.info(f"Polling ADO for work items modified since [{since_date}] using WIQL...")

    try:
        res = requests.post(api_endpoint, json={"query": wiql_query}, auth=("", pat), timeout=20)
        if res.status_code != 200:
            logger.error(f"ADO WIQL Query failure: HTTP {res.status_code} - {res.text}")
            return 0

        payload = res.json()
        work_items = payload.get("workItems", [])
        logger.info(f"Found [{len(work_items)}] ADO work items updated since [{since_date}].")

        sync_count = 0
        for item in work_items:
            item_id = str(item.get("id"))
            if sync_ado_workitem(item_id):
                sync_count += 1

        return sync_count

    except Exception as e:
        logger.exception("Critical crash during ADO delta synchronization")
        return 0


def sync_confluence_space(space_key: str, minutes: int = None) -> int:
    """
    Synchronizes a specific Confluence space.
    - If minutes is provided: Runs a highly efficient CQL Delta search for pages modified in that window.
    - If minutes is None: Runs a deep full space crawl recursively following page pagination.
    - Strict Data Hygiene: Discards drafts, trashed, or archived pages, indexing strictly 'current' live pages.
    - FinOps token saving: Checks database first, skipping unmodified pages.
    """
    url = settings.CONFLUENCE_URL.rstrip('/')
    pat = settings.CONFLUENCE_PAT.strip()

    if not url or not pat:
        logger.error("Confluence configurations (URL/PAT) are missing from .env!")
        return 0

    headers = {}
    auth = None
    if ":" in pat:
        email, token = pat.split(":", 1)
        auth = (email, token)
    else:
        headers["Authorization"] = f"Bearer {pat}"

    # Determine crawling query strategy (Delta vs. Full)
    sync_count = 0
    pages_to_process = []

    if minutes is not None:
        # Case A: Time-specified dynamic delta sync
        hours = max(1, minutes // 60)
        cql = f'space = "{space_key}" AND type = "page" AND lastmodified >= now("-{hours}h")'
        api_endpoint = f"{url}/wiki/rest/api/search"
        logger.info(f"Initiating dynamic Confluence delta sync for Space [{space_key}] over last {hours} hours...")
        
        try:
            params = {
                "cql": cql,
                "expand": "content.body.storage,content.version",
                "limit": 50
            }
            res = requests.get(api_endpoint, headers=headers, auth=auth, params=params, timeout=20)
            if res.status_code == 200:
                payload = res.json()
                results = payload.get("results", [])
                for item in results:
                    content = item.get("content", {})
                    if content:
                        pages_to_process.append(content)
            else:
                logger.error(f"Confluence CQL search failed: HTTP {res.status_code} - {res.text}")
        except Exception as e:
            masked_error = _mask_sensitive_log(str(e))
            logger.error(f"Confluence CQL search failed: {masked_error}")
    else:
        # Case B: Deep full space crawl (Hydration) with recursive pagination
        api_endpoint = f"{url}/wiki/rest/api/content?spaceKey={space_key}&expand=body.storage,version&limit=50"
        logger.info(f"Initiating deep, recursive Confluence Full Hydration for Space [{space_key}]...")
        
        active_url = api_endpoint
        while active_url:
            try:
                res = requests.get(active_url, headers=headers, auth=auth, timeout=20)
                if res.status_code != 200:
                    logger.error(f"Confluence Full Space query failed: HTTP {res.status_code} - {res.text}")
                    break
                    
                payload = res.json()
                results = payload.get("results", [])
                for content in results:
                    pages_to_process.append(content)
                
                # Dynamic Link Pagination (follows Atlassian's 'next' page link)
                next_path = payload.get("_links", {}).get("next", "")
                if next_path:
                    active_url = f"{url}/wiki{next_path}" if not next_path.startswith("http") else next_path
                else:
                    active_url = None
                    
            except Exception as e:
                logger.error(f"Failed to paginate full Confluence space [{space_key}]: {e}")
                break

    # Process all matched pages through our strict data-hygiene and FinOps layers
    from app.services.db_service import db_service
    logger.info(f"Retrieved [{len(pages_to_process)}] total raw pages for Space [{space_key}]. Processing...")

    for content in pages_to_process:
        page_id = content.get("id")
        title = content.get("title", f"Page {page_id}")
        status = content.get("status", "current").lower()
        version = content.get("version", {}).get("number", 1)

        # 🧼 STRICT DATA HYGIENE GUARDRAIL: Discard drafts, archived, trashed, or deleted documents
        if status in ["draft", "archived", "trashed", "deleted", "deleted_trash"] or status != "current":
            logger.info(f"🧼 Data Hygiene Block: Skipping Page [{title}] due to document status: [{status}]")
            continue

        # 💸 STRICT FINOPS GUARDRAIL: Skip vectorization if document version matches existing DB record
        existing_doc = db_service.get_document(f"confluence_page_{page_id}")
        if existing_doc and existing_doc.get("version") == version:
            logger.info(f"💸 FinOps Guardrail: Skipping Page [{title}] (Version [{version}] already semantically indexed, saves tokens!)")
            sync_count += 1 # Count as successful/active
            continue

        html_body = content.get("body", {}).get("storage", {}).get("value", "")
        markdown_text = convert_html_to_markdown(html_body)
        full_content = f"Confluence Page Title: {title}\nSpace Key: {space_key}\n\nPage Content:\n{markdown_text}"

        logger.info(f"Generating dynamic summary for [{title}]...")
        doc_summary = _generate_document_summary(full_content)

        # Write to temporary file for RAG injection (includes space and title for clean citation names!)
        safe_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', title)
        filename = f"confluence_page_{space_key}_{safe_title}_{page_id}.txt"
        temp_file_path = os.path.join(TEMP_DIR, filename)

        with open(temp_file_path, "w", encoding="utf-8") as tf:
            tf.write(full_content)

        #: Add freshness tracking
        from datetime import datetime
        sync_timestamp = datetime.utcnow().isoformat()
        custom_metadata = {
            "document_id": f"confluence_page_{page_id}",
            "title": title,
            "source_system": "CONFLUENCE",
            "space_key": space_key,
            "summary": doc_summary,
            "status": "Active",
            "doc_type": "Confluence",
            "version": version,
            "last_synced_at": sync_timestamp,
            "confluence_version": version
        }
        success = rag_service.ingest_document(temp_file_path, filename, custom_metadata=custom_metadata)
        
        # Store in database with freshness tracking
        if success:
            from app.services.db_service import db_service
            db_service.save_document(
                document_id=f"confluence_page_{page_id}",
                title=title,
                content=full_content,
                source_system="CONFLUENCE",
                space_key=space_key,
                summary=doc_summary,
                status="Active",
                doc_type="Confluence",
                version=version,
                last_synced_at=sync_timestamp,
                confluence_version=version
            )
        
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        if success:
            logger.info(f"Synchronized updated Confluence page: [{title}] (v{version})")
            sync_count += 1

    return sync_count


def sync_all_active_confluence_spaces(minutes: int = None) -> int:
    """Queries the database config table and sequentially synchronizes all active Confluence Spaces."""
    from app.services.db_service import db_service
    active_spaces = db_service.get_active_sync_targets("CONFLUENCE_SPACE")
    
    if not active_spaces:
        logger.warning("No active Confluence spaces found inside the database config_sync table!")
        return 0

    url = settings.CONFLUENCE_URL.rstrip('/')
    pat = settings.CONFLUENCE_PAT.strip()
    headers = {}
    auth = None
    if pat:
        if ":" in pat:
            email, token = pat.split(":", 1)
            auth = (email, token)
        else:
            headers["Authorization"] = f"Bearer {pat}"

    total_synced = 0
    for space in active_spaces:
        #: Validate Space Exists Before Crawling
        if url and pat:
            try:
                validate_endpoint = f"{url}/wiki/rest/api/space/{space}"
                val_res = requests.get(validate_endpoint, headers=headers, auth=auth, timeout=10)
                if val_res.status_code == 404:
                    logger.warning(f"Config Validation Failed: Space '{space}' does not exist on Confluence (HTTP 404). Deactivating target.")
                    db_service.deactivate_sync_target("CONFLUENCE_SPACE", space)
                    continue
            except Exception as e:
                masked = _mask_sensitive_log(str(e))
                logger.warning(f"Failed to validate space '{space}': {masked}")

        #& 6.2 Fix: Acquire distributed mutex lock before syncing!
        if not db_service.acquire_sync_lock("CONFLUENCE_SPACE", space):
            logger.warning(f"Skipping sync for '{space}': Sync already in progress (Locked).")
            continue

        try:
            space_synced = sync_confluence_space(space, minutes)
            if space_synced > 0:
                db_service.update_sync_timestamp("CONFLUENCE_SPACE", space)
            total_synced += space_synced
        except Exception as e:
            #: Catch and log silent background daemon crashes safely
            masked = _mask_sensitive_log(str(e))
            logger.error(f"FATAL: Background sync crashed for space '{space}': {masked}")
        finally:
            # Always release the distributed lock, even if the sync script crashes!
            db_service.release_sync_lock("CONFLUENCE_SPACE", space)

    logger.info(f"Total synchronized pages across all active spaces: {total_synced}")
    return total_synced


def run_recent_sync_cycle(minutes: int = 30):
    """Executes a single delta sync cycle across Confluence."""
    logger.info("=" * 80)
    logger.info(f"STARTING V.I.S.I.O.N. SYNCHRONIZATION CYCLE (Last {minutes} mins)")
    logger.info("=" * 80)

    conf_count = sync_all_active_confluence_spaces(minutes)

    logger.info("=" * 80)
    logger.info(f"SYNCHRONIZATION COMPLETED. Ingested {conf_count} Confluence pages.")
    logger.info("=" * 80)


if __name__ == "__main__":
    print("\n=========================================================================")
    print("V.I.S.I.O.N. ENTERPRISE ECOSYSTEM CONNECTORS SYNC UTILITY")
    print("=========================================================================\n")
    
    import argparse
    parser = argparse.ArgumentParser(description="Synchronize Confluence assets natively.")
    parser.add_argument("--confluence", help="Confluence Page ID to pull and index")
    parser.add_argument("--sync-recent", type=int, help="Fetch Confluence pages modified in the last N minutes")
    parser.add_argument("--daemon", action="store_true", help="Start continuous background daemon polling every 30 mins")
    args = parser.parse_args()

    if args.confluence:
        sync_confluence_page(args.confluence)
    elif args.sync_recent is not None:
        run_recent_sync_cycle(args.sync_recent)
    elif args.daemon:
        logger.info("V.I.S.I.O.N. Sync Daemon started. Polling Confluence every 30 minutes...")
        try:
            while True:
                run_recent_sync_cycle(30)
                logger.info("Sync Daemon sleeping for 30 minutes...")
                time.sleep(30 * 60) # Sleep for 30 minutes
        except KeyboardInterrupt:
            logger.info("V.I.S.I.O.N. Sync Daemon terminated by user.")
    else:
        print("Error: Please provide a target for synchronization.")
        print("Usage examples:")
        print("  python sync_connectors.py --confluence 123456")
        print("  python sync_connectors.py --sync-recent 30")
        print("  python sync_connectors.py --daemon")
    print()
