# ============================================================================
# PROJECT V.I.S.I.O.N. - PERSISTENT SQLite / CLOUD POSTGRES DATABASE SERVICE
# ============================================================================
# File Description:
# This service manages database connections, schemas, and query execution
# natively for both local (SQLite) and cloud (PostgreSQL) environments.
# The toggle is controlled via settings.DATABASE_TARGET to support seamless,
# zero-code cloud migration.
# ============================================================================

import sqlite3
import os
import logging
from datetime import datetime

# Configure clean logging
logger = logging.getLogger(__name__)

# Define platform-aware database storage path (Prevents serverless Cloud Run read-only disk crashes!)
if os.name != 'nt': # Running on Cloud Run (Linux/Unix container)
    DB_DIR = "/tmp/data"
else: # Running locally (Windows/Mac)
    DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data"))

DB_PATH = os.path.join(DB_DIR, "chat_history.db")

class PostgreSQLConnectionWrapper:
    """
    SaaS Connection Leak Shield: Automatically commits/rolls back transactions
    AND guarantees that the TCP socket connection is closed when exiting the context!
    """
    def __init__(self, conn):
        self._conn = conn

    def __getattr__(self, name):
        # Forward all standard attributes and methods directly to the connection
        return getattr(self._conn, name)

    def __enter__(self):
        return self._conn.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            # Let psycopg2 commit or roll back the active transaction natively
            self._conn.__exit__(exc_type, exc_val, exc_tb)
        finally:
            # Guarantee that the connection socket is closed and returned to the pool!
            self._conn.close()
            logger.info("Database Connection Shield: Cloud SQL Connection safely closed and returned to pool.")

class DatabaseService:
    """
    DatabaseService handles permanent, secure SQLite (local) and PostgreSQL (cloud)
    storage for V.I.S.I.O.N. and manages history and parent documents.
    """
    def __init__(self):
        """Initializes the service, creates folders, and bootstraps the schema."""
        # Ensure local directories exist regardless
        os.makedirs(DB_DIR, exist_ok=True)
        # Initialize schema tables dynamically
        self.init_db()

    def _get_connection(self):
        """Helper method that returns an active, thread-safe connection based on active target."""
        from app.core.config import settings
        if settings.DATABASE_TARGET == "CLOUD":
            import psycopg2
            try:
                return psycopg2.connect(
                    host=settings.PG_HOST,
                    port=settings.PG_PORT,
                    database=settings.PG_DATABASE,
                    user=settings.PG_USER,
                    password=settings.PG_PASSWORD,
                    connect_timeout=5
                )
            except psycopg2.OperationalError as e:
                #: Fail-Open to Local SQLite if Cloud DB is down!
                logger.error(f"FATAL: PostgreSQL Cloud Connection failed: {e}. Falling back to LOCAL SQLite!")
                settings.DATABASE_TARGET = "LOCAL"
                # Fall through to SQLite logic below
        
        # SQLite Fallback / Default
        conn = sqlite3.connect(DB_PATH)
        # Enable high-concurrency WAL Mode and Normal Synchronization (Phase 4 Database Tuning)
        # This allows background sync indexing writes and foreground user reads to execute concurrently!
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        except Exception as e:
            logger.warning(f"Failed to tune SQLite parameters: {e}")
        return conn

    @property
    def placeholder(self) -> str:
        """Dynamically returns the parameter placeholder character for the active engine."""
        from app.core.config import settings
        return "%s" if settings.DATABASE_TARGET == "CLOUD" else "?"

    def init_db(self):
        """Creates the messages logging and documents tables if they do not already exist in the database."""
        from app.core.config import settings
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if settings.DATABASE_TARGET == "CLOUD":
                    # Create PostgreSQL chat_sessions table schema
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS chat_sessions (
                            session_id VARCHAR(100) PRIMARY KEY,
                            title VARCHAR(255) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            admin_name VARCHAR(100) NOT NULL
                        )
                    """)
                    # Create PostgreSQL messages schema with foreign key references and CASCADE
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS messages (
                            id SERIAL PRIMARY KEY,
                            sender VARCHAR(50) NOT NULL,
                            text TEXT NOT NULL,
                            admin_name VARCHAR(100) NOT NULL,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            session_id VARCHAR(100) DEFAULT 'default_session' REFERENCES chat_sessions(session_id) ON DELETE CASCADE
                        )
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS documents (
                            document_id VARCHAR(100) PRIMARY KEY,
                            title VARCHAR(255) NOT NULL,
                            content TEXT NOT NULL,
                            source_system VARCHAR(50) NOT NULL,
                            space_key VARCHAR(50) NOT NULL,
                            summary TEXT,
                            status VARCHAR(50),
                            doc_type VARCHAR(50),
                            version INTEGER DEFAULT 1,
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            confluence_version INTEGER DEFAULT 1
                        )
                    """)
                    # Create PostgreSQL system_settings table schema
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS system_settings (
                            key VARCHAR(100) PRIMARY KEY,
                            value TEXT NOT NULL
                        )
                    """)
                    
                    # Create sync_log table to track document synchronization ---
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS sync_log (
                            sync_id SERIAL PRIMARY KEY,
                            document_id VARCHAR(100) NOT NULL,
                            source_system VARCHAR(50) NOT NULL,
                            sync_type VARCHAR(20) NOT NULL,
                            status VARCHAR(20) NOT NULL,
                            chunk_count INTEGER DEFAULT 0,
                            vector_count INTEGER DEFAULT 0,
                            started_at TIMESTAMP NOT NULL,
                            completed_at TIMESTAMP,
                            error_message TEXT
                        )
                    """)
                    
                    # Pre-compile the pgvector extension and knowledge_base table in PostgreSQL
                    try:
                        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS knowledge_base (
                                chunk_id VARCHAR(255) PRIMARY KEY,
                                embedding vector(768) NOT NULL,
                                content TEXT NOT NULL,
                                source_system VARCHAR(50),
                                space_key VARCHAR(50),
                                document_id VARCHAR(100)
                            )
                        """)
                        logger.info("Cloud PostgreSQL pgvector table schema pre-checked successfully.")
                    except Exception as pgv_err:
                        logger.warning(f"Could not initialize pgvector extension/table (ensure extension is installed in Postgres): {pgv_err}")
                else:
                    # Create SQLite chat_sessions table schema
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS chat_sessions (
                            session_id TEXT PRIMARY KEY,
                            title TEXT NOT NULL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            admin_name TEXT NOT NULL
                        )
                    """)
                    # Create 'messages' table with strict fields for history tracking
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS messages (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            sender TEXT NOT NULL,
                            text TEXT NOT NULL,
                            admin_name TEXT NOT NULL,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            session_id TEXT DEFAULT 'default_session' REFERENCES chat_sessions(session_id) ON DELETE CASCADE
                        )
                    """)
                    # Create 'documents' table to store raw parent documents for Parent-Document Collapsing (ADR-004)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS documents (
                            document_id TEXT PRIMARY KEY,
                            title TEXT NOT NULL,
                            content TEXT NOT NULL,
                            source_system TEXT NOT NULL,
                            space_key TEXT NOT NULL,
                            summary TEXT,
                            status TEXT,
                            doc_type TEXT,
                            version INTEGER DEFAULT 1,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            last_synced_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            confluence_version INTEGER DEFAULT 1
                        )
                    """)
                    # Create 'system_settings' table to store dynamic environment configs and persistent prompt directives
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS system_settings (
                            key TEXT PRIMARY KEY,
                            value TEXT NOT NULL
                        )
                    """)
                    
                    # Create sync_log table to track document synchronization ---
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS sync_log (
                            sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            document_id TEXT NOT NULL,
                            source_system TEXT NOT NULL,
                            sync_type TEXT NOT NULL,
                            status TEXT NOT NULL,
                            chunk_count INTEGER DEFAULT 0,
                            vector_count INTEGER DEFAULT 0,
                            started_at DATETIME NOT NULL,
                            completed_at DATETIME,
                            error_message TEXT
                        )
                    """)
                    
                    # --- GRACEFUL AUTOMATIC SQLITE SCHEMA MIGRATIONS ---
                    # Safely run ALTER TABLE statements to add new metadata columns if they do not exist
                    new_cols = [
                        ("summary", "TEXT"),
                        ("status", "TEXT"),
                        ("doc_type", "TEXT"),
                        ("version", "INTEGER DEFAULT 1")
                    ]
                    for col_name, col_type in new_cols:
                        try:
                            cursor.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type};")
                            logger.info(f"SQLite Migrator: Appended new column [{col_name}] to documents table successfully.")
                        except sqlite3.OperationalError:
                            # Column already exists, safe to ignore!
                            pass

                    # ---: Add freshness tracking columns for existing databases ---
                    freshness_cols = [
                        ("last_synced_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
                        ("confluence_version", "INTEGER DEFAULT 1")
                    ]
                    for col_name, col_type in freshness_cols:
                        try:
                            cursor.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type};")
                            logger.info(f"SQLite Migrator: Appended freshness column [{col_name}] to documents table successfully.")
                        except sqlite3.OperationalError:
                            # Column already exists, safe to ignore!
                            pass

                # --- PostgreSQL Migration for freshness columns ---
                if settings.DATABASE_TARGET == "CLOUD":
                    try:
                        cursor.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;");
                        logger.info("PostgreSQL Migrator: Appended last_synced_at column to documents table successfully.")
                    except Exception as pg_mig_err:
                        logger.warning(f"PostgreSQL Migrator: Column migration for last_synced_at failed (may already exist): {pg_mig_err}")
                    try:
                        cursor.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS confluence_version INTEGER DEFAULT 1;");
                        logger.info("PostgreSQL Migrator: Appended confluence_version column to documents table successfully.")
                    except Exception as pg_mig_err:
                        logger.warning(f"PostgreSQL Migrator: Column migration for confluence_version failed (may already exist): {pg_mig_err}")
                
                # --- UNIFIED CONFIG SYNC BOOTSTRAPPING (PHASE 4) ---
                # Create the database-driven configuration table
                if settings.DATABASE_TARGET == "CLOUD":
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS config_sync (
                            id SERIAL PRIMARY KEY,
                            target_type VARCHAR(50) NOT NULL,
                            target_key VARCHAR(100) NOT NULL,
                            is_active BOOLEAN DEFAULT TRUE,
                            last_synced_at TIMESTAMP NULL,
                            is_syncing BOOLEAN DEFAULT FALSE
                        )
                    """)
                else:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS config_sync (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            target_type TEXT NOT NULL,
                            target_key TEXT NOT NULL,
                            is_active INTEGER DEFAULT 1,
                            last_synced_at DATETIME NULL,
                            is_syncing INTEGER DEFAULT 0
                        )
                    """)
                    
                # Graceful Migration: Add is_syncing if it doesn't exist
                if settings.DATABASE_TARGET == "LOCAL":
                    try:
                        cursor.execute("ALTER TABLE config_sync ADD COLUMN is_syncing INTEGER DEFAULT 0;")
                        logger.info("SQLite Migrator: Appended is_syncing lock column to config_sync table successfully.")
                    except sqlite3.OperationalError:
                        pass
                else:
                    try:
                        cursor.execute("ALTER TABLE config_sync ADD COLUMN IF NOT EXISTS is_syncing BOOLEAN DEFAULT FALSE;")
                        logger.info("PostgreSQL Migrator: Appended is_syncing lock column to config_sync table successfully.")
                    except Exception as pg_mig_err:
                        pass
                
                # Idempotently seed/align corporate Confluence spaces from environment configuration on every boot!
                from app.core.config import settings
                default_spaces = [s.strip() for s in settings.CONFLUENCE_SPACES.split(",") if s.strip()]
                
                if default_spaces:
                    logger.info(f"Database Config: Idempotently aligning active Confluence Spaces from environment: {default_spaces}")
                    p = "%s" if settings.DATABASE_TARGET == "CLOUD" else "?"
                    for space in default_spaces:
                        # Safely check if this space target already exists in the config_sync registry
                        cursor.execute("SELECT COUNT(*) FROM config_sync WHERE target_type = ? AND target_key = ?", ("CONFLUENCE_SPACE", space))
                        if cursor.fetchone()[0] == 0:
                            # If it is a brand-new space, append it cleanly as active!
                            is_active_val = 'TRUE' if settings.DATABASE_TARGET == "CLOUD" else '1'
                            cursor.execute(f"INSERT INTO config_sync (target_type, target_key, is_active) VALUES ({p}, {p}, {is_active_val})", ("CONFLUENCE_SPACE", space))
                            logger.info(f"Database Config: Dynamically appended new space target [{space}] from environment on boot.")

                # Execute migration to append session_id if missing on messages table
                if settings.DATABASE_TARGET == "CLOUD":
                    try:
                        cursor.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS session_id VARCHAR(100) DEFAULT 'default_session';")
                        logger.info("PostgreSQL Migrator: Checked/Appended session_id column to messages table successfully.")
                    except Exception as pg_mig_err:
                        logger.warning(f"PostgreSQL Migrator: Column migration for session_id failed: {pg_mig_err}")
                else:
                    try:
                        cursor.execute("ALTER TABLE messages ADD COLUMN session_id TEXT DEFAULT 'default_session';")
                        logger.info("SQLite Migrator: Appended session_id column to messages table successfully.")
                    except sqlite3.OperationalError:
                        # Column already exists, safe to ignore!
                        pass

                # Auto-seed default chat session if chat_sessions is empty
                cursor.execute("SELECT COUNT(*) FROM chat_sessions")
                if cursor.fetchone()[0] == 0:
                    logger.info("Auto-seeding default chat session.")
                    p = "%s" if settings.DATABASE_TARGET == "CLOUD" else "?"
                    cursor.execute(f"INSERT INTO chat_sessions (session_id, title, admin_name) VALUES ({p}, {p}, {p})", ("default_session", "Default Session", settings.DEFAULT_ADMIN_NAME or "admin"))

                # Create and seed the strict 'users' table schema
                p = "%s" if settings.DATABASE_TARGET == "CLOUD" else "?"
                if settings.DATABASE_TARGET == "CLOUD":
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            username VARCHAR(100) PRIMARY KEY,
                            password VARCHAR(100) NOT NULL,
                            role VARCHAR(50) NOT NULL
                        )
                    """)
                    
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_sessions (
                            token VARCHAR(255) PRIMARY KEY,
                            username VARCHAR(100) NOT NULL,
                            role VARCHAR(50) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
                        )
                    """)
                else:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            username TEXT PRIMARY KEY,
                            password TEXT NOT NULL,
                            role TEXT NOT NULL
                        )
                    """)
                    
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_sessions (
                            token TEXT PRIMARY KEY,
                            username TEXT NOT NULL,
                            role TEXT NOT NULL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
                        )
                    """)
                
                # Idempotent seeding of user credentials (Preserves manually added DB users!)
                default_users = [
                    ("sandesh", "vision@sandesh", "ADMIN")
                ]
                
                if settings.DATABASE_TARGET == "CLOUD":
                    # PostgreSQL ON CONFLICT DO NOTHING
                    cursor.executemany("""
                        INSERT INTO users (username, password, role) 
                        VALUES (%s, %s, %s)
                        ON CONFLICT (username) DO NOTHING
                    """, default_users)
                else:
                    # SQLite INSERT OR IGNORE
                    cursor.executemany("""
                        INSERT OR IGNORE INTO users (username, password, role) 
                        VALUES (?, ?, ?)
                    """, default_users)
                    
                logger.info("Database Config: Idempotently seeded core users. Manual DB additions preserved.")

                conn.commit()
                logger.info(f"V.I.S.I.O.N. database schema initialized successfully for [{settings.DATABASE_TARGET}] mode.")
        except Exception as e:
            logger.error(f"Failed to initialize database schema: {e}")

    def save_document(self, document_id: str, title: str, content: str, source_system: str, space_key: str, summary: str = "", status: str = "Active", doc_type: str = "Confluence", version: int = 1, last_synced_at: str = None, confluence_version: int = 1) -> bool:
        """Saves or updates a raw document inside the active engine for Parent-Document Collapsing (ADR-004). 
        Now tracks last_synced_at timestamp and Confluence page version for freshness detection."""
        from datetime import datetime
        p = self.placeholder
        # Use current timestamp if not provided
        sync_timestamp = last_synced_at or datetime.utcnow().isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if self.placeholder == "?": # SQLite (No ON CONFLICT ... DO UPDATE support on old python SQLite)
                    cursor.execute(f"""
                        INSERT OR REPLACE INTO documents (document_id, title, content, source_system, space_key, summary, status, doc_type, version, timestamp, last_synced_at, confluence_version)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                    """, (document_id, title, content, source_system, space_key, summary, status, doc_type, version, sync_timestamp, confluence_version))
                else: # PostgreSQL
                    cursor.execute(f"""
                        INSERT INTO documents (document_id, title, content, source_system, space_key, summary, status, doc_type, version, timestamp, last_synced_at, confluence_version)
                        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, CURRENT_TIMESTAMP, {p}, {p})
                        ON CONFLICT(document_id) DO UPDATE SET
                            title=excluded.title,
                            content=excluded.content,
                            source_system=excluded.source_system,
                            space_key=excluded.space_key,
                            summary=excluded.summary,
                            status=excluded.status,
                            doc_type=excluded.doc_type,
                            version=excluded.version,
                            timestamp=CURRENT_TIMESTAMP,
                            last_synced_at=excluded.last_synced_at,
                            confluence_version=excluded.confluence_version
                    """, (document_id, title, content, source_system, space_key, summary, status, doc_type, version, sync_timestamp, confluence_version))
                conn.commit()
                logger.info(f"Raw document [{title}] stored/updated in active database (Version: {confluence_version}, Synced: {sync_timestamp}).")
                return True
        except Exception as e:
            logger.error(f"Failed to save raw document to active database: {e}")
            return False

    def get_document(self, document_id: str) -> dict | None:
        """Retrieves a raw document by its unique ID for full-text RAG context reconstruction."""
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT document_id, title, content, source_system, space_key, summary, status, doc_type, version FROM documents
                    WHERE document_id = {p}
                """, (document_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        "document_id": row[0],
                        "title": row[1],
                        "content": row[2],
                        "source_system": row[3],
                        "space_key": row[4],
                        "summary": row[5] or "",
                        "status": row[6] or "Active",
                        "doc_type": row[7] or "Confluence",
                        "version": row[8] or 1
                    }
        except Exception as e:
            logger.error(f"Failed to fetch raw document from active database: {e}")
        return None

    def get_all_document_titles(self) -> list:
        """Retrieves all unique document titles from the persistent database (for dynamic fallback typo correction)."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT title FROM documents")
                rows = cursor.fetchall()
                return [row[0] for row in rows if row[0]]
        except Exception as e:
            logger.error(f"Failed to retrieve document titles: {e}")
            return []

    def save_message(self, sender: str, text: str, admin_name: str, session_id: str = "default_session") -> bool:
        """Saves a single dialogue message (from ADMIN or VISION) into the database, scoped to a specific session."""
        # Ignore structural background notifications or model system directives
        if text.startswith("[SYSTEM:") or "[MODEL_OVERRIDE:" in text:
            return False

        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Ensure the session exists in chat_sessions to satisfy foreign key constraints
                cursor.execute("SELECT COUNT(*) FROM chat_sessions WHERE session_id = ?", (session_id,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute(f"INSERT INTO chat_sessions (session_id, title, admin_name) VALUES ({p}, {p}, {p})", (session_id, "New Session", admin_name))

                # Insert the message tuple
                cursor.execute(f"""
                    INSERT INTO messages (sender, text, admin_name, session_id)
                    VALUES ({p}, {p}, {p}, {p})
                """, (sender, text, admin_name, session_id))
                conn.commit()
                logger.info(f"Dialogue saved to active database from [{sender}] in session [{session_id}].")
                return True
        except Exception as e:
            logger.error(f"Failed to write message log to active database: {e}")
            return False

    def get_chat_sessions(self, admin_name: str) -> list[dict]:
        """Queries active sessions owned by the authenticated user."""
        p = self.placeholder
        sessions = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT session_id, title, created_at, admin_name FROM chat_sessions
                    WHERE admin_name = {p}
                    ORDER BY created_at DESC
                """, (admin_name,))
                rows = cursor.fetchall()
                for row in rows:
                    sessions.append({
                        "session_id": row[0],
                        "title": row[1],
                        "created_at": str(row[2]),
                        "admin_name": row[3]
                    })
        except Exception as e:
            logger.error(f"Failed to fetch chat sessions for user {admin_name}: {e}")
        return sessions

    def create_chat_session(self, session_id: str, title: str, admin_name: str) -> bool:
        """Saves a new session row."""
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO chat_sessions (session_id, title, admin_name)
                    VALUES ({p}, {p}, {p})
                """, (session_id, title, admin_name))
                conn.commit()
                logger.info(f"Created chat session [{title}] with ID [{session_id}] for {admin_name}.")
                return True
        except Exception as e:
            logger.error(f"Failed to create chat session: {e}")
            return False

    def rename_chat_session(self, session_id: str, new_title: str, admin_name: str) -> bool:
        """Renames the session (validates ownership: WHERE session_id = ? AND admin_name = ?)."""
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE chat_sessions SET title = {p}
                    WHERE session_id = {p} AND admin_name = {p}
                """, (new_title, session_id, admin_name))
                conn.commit()
                logger.info(f"Renamed session {session_id} to [{new_title}] for {admin_name}.")
                return True
        except Exception as e:
            logger.error(f"Failed to rename chat session: {e}")
            return False

    def delete_chat_session(self, session_id: str, admin_name: str) -> bool:
        """Deletes the session row (which cascades and purges all associated messages)."""
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Enforce foreign key constraints explicitly for SQLite
                if p == "?":
                    cursor.execute("PRAGMA foreign_keys = ON;")
                
                # Deleting the session row
                cursor.execute("DELETE FROM chat_sessions WHERE session_id = ? AND admin_name = ?", (session_id, admin_name))
                # Explicitly delete associated messages in the same transaction to guarantee 100% orphan cleanup
                cursor.execute("DELETE FROM messages WHERE session_id = ? AND admin_name = ?", (session_id, admin_name))
                
                conn.commit()
                logger.info(f"Purged session {session_id} and all its messages for {admin_name}.")
                return True
        except Exception as e:
            logger.error(f"Failed to delete chat session: {e}")
            return False

    def get_chat_history_for_session(self, session_id: str, admin_name: str, limit: int = 10) -> list[dict]:
        """Retrieves the last N messages scoped strictly to the session AND the logged-in admin (sorted DESC, returned ASC)."""
        p = self.placeholder
        history = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT sender, text, admin_name FROM (
                        SELECT id, sender, text, admin_name FROM messages
                        WHERE session_id = ? AND admin_name = ?
                        ORDER BY id DESC LIMIT ?
                    ) sub ORDER BY id ASC
                """, (session_id, admin_name, limit))
                rows = cursor.fetchall()
                for sender, text, row_admin_name in rows:
                    history.append({
                        "sender": sender,
                        "text": text,
                        "admin_name": row_admin_name
                    })
        except Exception as e:
            logger.error(f"Failed to fetch chat history for session {session_id} and admin {admin_name}: {e}")
        return history

    def update_session_title_idempotent(self, session_id: str, new_title: str, admin_name: str = None) -> bool:
        """Updates the session title only if the current title is an unmodified default string."""
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Expand the WHERE clause to match the Python trigger conditions
                if admin_name:
                    cursor.execute(f"""
                        UPDATE chat_sessions SET title = {p}
                        WHERE session_id = {p} AND title IN ('New Session', 'General Session', 'Default Session') AND admin_name = {p}
                    """, (new_title, session_id, admin_name))
                else:
                    cursor.execute(f"""
                        UPDATE chat_sessions SET title = {p}
                        WHERE session_id = {p} AND title IN ('New Session', 'General Session', 'Default Session')
                    """, (new_title, session_id))
                
                # Check if any row was actually updated
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Idempotently updated session {session_id} title to [{new_title}].")
                    return True
                else:
                    logger.warning(f"Session {session_id} title update rejected. Session is either already renamed or does not exist.")
                    return False
        except Exception as e:
            logger.error(f"Failed to idempotently update session title: {e}")
            return False

    def get_chat_history(self, limit: int = 50) -> list:
        """Retrieves the last N messages from active database, formatted as readable timeline rows."""
        history = []
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Query the latest entries in chronological order (cross-compatible subquery structure)
                cursor.execute(f"""
                    SELECT sender, text, admin_name FROM (
                        SELECT id, sender, text, admin_name FROM messages 
                        ORDER BY id DESC LIMIT {p}
                    ) sub ORDER BY id ASC
                """, (limit,))
                rows = cursor.fetchall()
                
                # Format into structured chat array matching the Vue frontend expectation
                for sender, text, admin_name in rows:
                    if sender == "ADMIN":
                        history.append(f"[ADMIN]: {text}")
                    else:
                        history.append(text)
        except Exception as e:
            logger.error(f"Failed to fetch chat history from active database: {e}")
        
        return history

    def clear_chat_history(self) -> bool:
        """Purges all entries from the messages table. Invoked when purging session memory."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Empty the messages table completely
                cursor.execute("DELETE FROM messages")
                conn.commit()
                logger.info("Active database conversation history completely purged.")
                return True
        except Exception as e:
            logger.error(f"Failed to clear active database: {e}")
            return False

    # --- CONFIG SYNC GETTERS & SETTERS (PHASE 4) ---
    def get_active_sync_targets(self, target_type: str) -> list[str]:
        """Queries the database-driven config table dynamically for active sync target keys (e.g. MAGELLAN)."""
        targets = []
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT target_key FROM config_sync 
                    WHERE target_type = {p} AND is_active = {"1" if p == "?" else "TRUE"}
                """, (target_type,))
                rows = cursor.fetchall()
                targets = [r[0] for r in rows if r[0]]
                logger.info(f"Database Config: Retrieved {len(targets)} active targets for [{target_type}].")
        except Exception as e:
            logger.error(f"Failed to fetch active sync targets for [{target_type}]: {e}")
        return targets

    def deactivate_sync_target(self, target_type: str, target_key: str) -> bool:
        """: Deactivates an invalid sync target to prevent endless 404 polling loops."""
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE config_sync SET is_active = {'FALSE' if p == '%s' else '0'}
                    WHERE target_type = {p} AND target_key = {p}
                """, (target_type, target_key))
                conn.commit()
                logger.info(f"Database Config: Deactivated invalid sync target [{target_type}: {target_key}].")
                return True
        except Exception as e:
            logger.error(f"Failed to deactivate invalid sync target [{target_type}: {target_key}]: {e}")
            return False

    def update_sync_timestamp(self, target_type: str, target_key: str) -> bool:
        """Updates the completion timestamp for a specific synchronization workspace target."""
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE config_sync SET last_synced_at = CURRENT_TIMESTAMP
                    WHERE target_type = {p} AND target_key = {p}
                """, (target_type, target_key))
                conn.commit()
                logger.info(f"Database Config: Recorded successful sync completion for [{target_type}: {target_key}].")
                return True
        except Exception as e:
            logger.error(f"Failed to update sync timestamp for [{target_type}: {target_key}]: {e}")
            return False

    def acquire_sync_lock(self, target_type: str, target_key: str) -> bool:
        """: Acquires a distributed database lock to prevent concurrent sync executions."""
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if currently locked
                cursor.execute(f"SELECT is_syncing FROM config_sync WHERE target_type = {p} AND target_key = {p}", (target_type, target_key))
                row = cursor.fetchone()
                
                if not row:
                    logger.warning(f"Lock Acquisition Failed: Target [{target_type}:{target_key}] not found.")
                    return False
                    
                is_syncing = row[0]
                # In SQLite it's 1/0, in Postgres it's True/False
                if is_syncing in [1, True, "TRUE", "1"]:
                    logger.warning(f"Sync Lock Rejected: A sync is already in progress for [{target_type}:{target_key}].")
                    return False
                    
                # Not locked. Acquire the lock!
                cursor.execute(f"""
                    UPDATE config_sync SET is_syncing = {'TRUE' if p == '%s' else '1'}
                    WHERE target_type = {p} AND target_key = {p}
                """, (target_type, target_key))
                conn.commit()
                logger.info(f"Sync Lock Acquired for [{target_type}:{target_key}].")
                return True
        except Exception as e:
            logger.error(f"Failed to acquire sync lock: {e}")
            return False

    def release_sync_lock(self, target_type: str, target_key: str) -> bool:
        """Releases the distributed database sync lock."""
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE config_sync SET is_syncing = {'FALSE' if p == '%s' else '0'}
                    WHERE target_type = {p} AND target_key = {p}
                """, (target_type, target_key))
                conn.commit()
                logger.info(f"Sync Lock Released for [{target_type}:{target_key}].")
                return True
        except Exception as e:
            logger.error(f"Failed to release sync lock: {e}")
            return False

    # --- SYSTEM SETTINGS CONFIGURATION ADAPTERS (PHASE 4 - CLOUD PERSISTENT) ---
    def get_setting(self, key: str, default: str = "") -> str:
        """Retrieves a persistent setting value from the database."""
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT value FROM system_settings WHERE key = {p}", (key,))
                row = cursor.fetchone()
                return row[0] if row else default
        except Exception as e:
            logger.warning(f"Failed to get setting '{key}' from DB: {e}")
            return default

    def save_setting(self, key: str, value: str) -> bool:
        """Saves or updates a persistent setting in the database (Upsert)."""
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if p == "?": # SQLite (ON CONFLICT Support)
                    cursor.execute("""
                        INSERT INTO system_settings (key, value) 
                        VALUES (?, ?) 
                        ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """, (key, value))
                else: # PostgreSQL (ON CONFLICT Support)
                    cursor.execute("""
                        INSERT INTO system_settings (key, value) 
                        VALUES (%s, %s) 
                        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                    """, (key, value))
                conn.commit()
                logger.info(f"Database Settings: Successfully saved/updated setting '{key}' in persistent database.")
                return True
        except Exception as e:
            logger.error(f"Failed to save setting '{key}' to DB: {e}")
            return False

    def authenticate_user(self, username: str, password: str) -> dict | None:
        """Queries the persistent database to verify credentials, strictly blocking un-enrolled logins."""
        p = self.placeholder
        try:
            username_clean = username.strip().lower()
            password_clean = password.strip()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Check if the user exists in our database
                if p == "?":
                    cursor.execute("SELECT username, password, role FROM users WHERE LOWER(username) = LOWER(?)", (username_clean,))
                else:
                    cursor.execute("SELECT username, password, role FROM users WHERE LOWER(username) = LOWER(%s)", (username_clean,))
                row = cursor.fetchone()
                
                if row:
                    # User exists! Verify their password match
                    stored_pass = row[1]
                    role = row[2]
                    if stored_pass == password_clean:
                        logger.info(f"Authentication: User [{row[0]}] successfully authenticated under role [{role}].")
                        return {"username": row[0], "role": role}
                    else:
                        logger.warning(f"Authentication: Failed login attempt for user [{row[0]}] - Incorrect password.")
                        return None
                else:
                    logger.warning(f"Authentication: Failed login attempt - User [{username_clean}] does not exist.")
                    return None
        except Exception as e:
            logger.error(f"Failed to authenticate user '{username}' against database: {e}")
        return None

    def generate_auth_token(self, username: str, role: str) -> str | None:
        """Generates a secure 64-character token and saves it to user_sessions."""
        import secrets
        token = secrets.token_hex(32)
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO user_sessions (token, username, role)
                    VALUES ({p}, {p}, {p})
                """, (token, username, role))
                conn.commit()
                logger.info(f"Authentication: Secure DB token generated for user [{username}].")
                return token
        except Exception as e:
            logger.error(f"Failed to generate auth token: {e}")
            return None

    def validate_auth_token(self, token: str) -> dict | None:
        """Validates a token against the user_sessions table."""
        if not token:
            return None
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT username, role FROM user_sessions WHERE token = {p}", (token,))
                row = cursor.fetchone()
                if row:
                    return {"username": row[0], "role": row[1]}
        except Exception as e:
            logger.error(f"Failed to validate auth token: {e}")
        return None

    # Sync Tracking & Deduplication Methods ---
    def record_sync_start(self, document_id: str, source_system: str, sync_type: str) -> bool:
        """Records the start of a document sync operation."""
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO sync_log (document_id, source_system, sync_type, status, started_at)
                    VALUES ({p}, {p}, {p}, {p}, CURRENT_TIMESTAMP)
                """, (document_id, source_system, sync_type, "IN_PROGRESS"))
                conn.commit()
                logger.info(f"Sync tracking: Recorded START for [{source_system}:{document_id}] (Type: {sync_type})")
                return True
        except Exception as e:
            logger.error(f"Failed to record sync start: {e}")
            return False

    def record_sync_complete(self, document_id: str, source_system: str, chunk_count: int = 0, vector_count: int = 0, error: str = None) -> bool:
        """Records the completion of a document sync operation."""
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                status = "ERROR" if error else "COMPLETE"
                cursor.execute(f"""
                    UPDATE sync_log SET status = {p}, completed_at = CURRENT_TIMESTAMP, 
                                        chunk_count = {p}, vector_count = {p}, error_message = {p}
                    WHERE document_id = {p} AND source_system = {p} AND status = 'IN_PROGRESS'
                    ORDER BY started_at DESC LIMIT 1
                """, (status, chunk_count, vector_count, error, document_id, source_system))
                conn.commit()
                if error:
                    logger.error(f"Sync tracking: Recorded COMPLETE (ERROR) for [{source_system}:{document_id}] - {error}")
                else:
                    logger.info(f"Sync tracking: Recorded COMPLETE for [{source_system}:{document_id}] ({chunk_count} chunks, {vector_count} vectors)")
                return True
        except Exception as e:
            logger.error(f"Failed to record sync completion: {e}")
            return False

    def is_recently_synced(self, document_id: str, source_system: str, min_age_minutes: int = 30) -> bool:
        """
        Checks if a document was successfully synced within the last N minutes.
        Returns True if document was recently synced (should skip re-sync).
        Returns False if not synced yet or older than threshold (should sync).
        """
        p = self.placeholder
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Calculate timestamp for min_age_minutes ago
                if p == "?":  # SQLite
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM sync_log 
                        WHERE document_id = {p} AND source_system = {p} 
                        AND status = 'COMPLETE'
                        AND completed_at >= datetime('now', '-{min_age_minutes} minutes')
                    """, (document_id, source_system))
                else:  # PostgreSQL
                    cursor.execute(f"""
                        SELECT COUNT(*) FROM sync_log 
                        WHERE document_id = {p} AND source_system = {p} 
                        AND status = 'COMPLETE'
                        AND completed_at >= NOW() - INTERVAL '{min_age_minutes} minutes'
                    """, (document_id, source_system))
                
                count = cursor.fetchone()[0]
                if count > 0:
                    logger.info(f"Dedup check: [{source_system}:{document_id}] was synced <{min_age_minutes}min ago. Skipping re-sync.")
                    return True
                else:
                    logger.info(f"Dedup check: [{source_system}:{document_id}] needs re-sync (no recent completion found).")
                    return False
        except Exception as e:
            logger.error(f"Failed to check sync recency: {e}")
            return False

    def get_sync_status(self, document_id: str = None, source_system: str = None) -> list[dict]:
        """Retrieves sync operation history filtered by document and/or source."""
        p = self.placeholder
        results = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if document_id and source_system:
                    cursor.execute(f"""
                        SELECT document_id, source_system, sync_type, status, chunk_count, vector_count, started_at, completed_at
                        FROM sync_log
                        WHERE document_id = {p} AND source_system = {p}
                        ORDER BY started_at DESC LIMIT 10
                    """, (document_id, source_system))
                elif document_id:
                    cursor.execute(f"""
                        SELECT document_id, source_system, sync_type, status, chunk_count, vector_count, started_at, completed_at
                        FROM sync_log
                        WHERE document_id = {p}
                        ORDER BY started_at DESC LIMIT 20
                    """, (document_id,))
                elif source_system:
                    cursor.execute(f"""
                        SELECT document_id, source_system, sync_type, status, chunk_count, vector_count, started_at, completed_at
                        FROM sync_log
                        WHERE source_system = {p}
                        ORDER BY started_at DESC LIMIT 20
                    """, (source_system,))
                else:
                    cursor.execute("""
                        SELECT document_id, source_system, sync_type, status, chunk_count, vector_count, started_at, completed_at
                        FROM sync_log
                        ORDER BY started_at DESC LIMIT 50
                    """)
                
                rows = cursor.fetchall()
                for row in rows:
                    results.append({
                        "document_id": row[0],
                        "source_system": row[1],
                        "sync_type": row[2],
                        "status": row[3],
                        "chunk_count": row[4],
                        "vector_count": row[5],
                        "started_at": str(row[6]),
                        "completed_at": str(row[7]) if row[7] else None
                    })
        except Exception as e:
            logger.error(f"Failed to retrieve sync status: {e}")
        return results

# Establish single, global instance for FastAPI import
db_service = DatabaseService()
