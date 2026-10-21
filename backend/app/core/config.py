from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Pydantic model for loading application settings from environment variables or a .env file.
    """
    # This tells pydantic-settings to look for a .env file, ignore extra variables, and ignore casing (V.I.S.I.O.N. Redesign)
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', case_sensitive=False, extra='ignore')

    # Define the settings we need. Pydantic will automatically look for these variables
    # in the environment or the .env file.
    GCP_PROJECT_ID: str = "gbr-mts-wgh-hkt-dev"
    GCP_LOCATION: str = "europe-west1"

    # Enforced Neural Model (Standard Magellon locked standard: gemini-2.5-flash)
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Token Sliding Window Context Budget configuration
    MAX_CONTEXT_TURNS: int = 10
    UI_HISTORY_LIMIT: int = 50 # How many messages to show in the Vue UI
    RAG_MAX_CONTEXT_CHARS: int = 30000
    RAG_MAX_LINK_DEPTH: int = 3

    # RAG Vector Search Configuration (Production-Hardened Strictness - Phase 4)
    RAG_DISTANCE_THRESHOLD: float = 0.60  # Stricter than before (was 0.45)
    RAG_HIGH_THRESHOLD: float = 0.40      # Even stricter for high-confidence (was 0.35)
    RAG_MARGIN_THRESHOLD: float = 0.15
    RAG_MIN_VIABLE_COUNT: int = 2
    RAG_MIN_CONSENSUS_COUNT: int = 2
    RAG_ALLOW_SINGLE_CHUNK_HIGH: bool = True
    RAG_SINGLE_CHUNK_HIGH_THRESHOLD: float = 0.30  # Very strict for single chunks
    RAG_USE_NEW_EVALUATOR: bool = True
    RAG_TOP_K: int = 3
    VERTEX_EMBEDDING_BATCH_SIZE: int = 15 # Sub-batching limit to prevent Google API 400 Payload Too Large errors
    MAX_UPLOAD_SIZE_MB: int = 15 # DoS Protection: Max megabytes allowed per file upload

    # Local Storage & Caching Paths
    LOCAL_DB_DIR: str = "C:/Users/w114216/.gemini/tmp/vision/data/chroma"
    LOCAL_TEMP_AUDIO_DIR: str = "temp_audio"
    LOCAL_TEMP_UPLOAD_DIR: str = "C:/Users/w114216/.gemini/tmp/vision/temp_docs"

    def model_post_init(self, __context):
        """Enforces strict, corporate configuration safety invariants on bootup (Fail-Fast)."""
        #: Fail-Fast if cloud production deployment is missing credentials
        if self.DATABASE_TARGET == "CLOUD":
            if not self.CONFLUENCE_URL or not self.CONFLUENCE_PAT:
                raise ValueError("Fail-Fast Security Guard: CONFLUENCE_URL and CONFLUENCE_PAT must be populated when DATABASE_TARGET is CLOUD.")
            if not self.ADO_URL or not self.ADO_PAT:
                raise ValueError("Fail-Fast Security Guard: ADO_URL and ADO_PAT must be populated when DATABASE_TARGET is CLOUD.")
        
        # # Validate Confluence URL is reachable 
        if self.CONFLUENCE_URL:
            try:
                import requests
                res = requests.head(self.CONFLUENCE_URL.rstrip('/'), timeout=10)
                if res.status_code >= 500:
                    raise ValueError(f"Confluence URL returned HTTP {res.status_code} (Server Error)")
                # 4xx errors might be auth-related, which is okay at startup
            except requests.exceptions.Timeout:
                raise ValueError(f"Confluence URL is unreachable (timeout after 10s): {self.CONFLUENCE_URL}")
            except requests.exceptions.ConnectionError as e:
                raise ValueError(f"Confluence URL is unreachable (connection failed): {self.CONFLUENCE_URL}. Error: {str(e)}")
            except Exception as e:
                # Log warning but don't fail-fast for other exceptions (might be normal during testing)
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not validate Confluence URL connectivity: {e}")
        
        # # Validate ADO URL is reachable
        if self.ADO_URL:
            try:
                import requests
                res = requests.head(self.ADO_URL.rstrip('/'), timeout=10)
                if res.status_code >= 500:
                    raise ValueError(f"ADO URL returned HTTP {res.status_code} (Server Error)")
            except requests.exceptions.Timeout:
                raise ValueError(f"ADO URL is unreachable (timeout after 10s): {self.ADO_URL}")
            except requests.exceptions.ConnectionError as e:
                raise ValueError(f"ADO URL is unreachable (connection failed): {self.ADO_URL}. Error: {str(e)}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Could not validate ADO URL connectivity: {e}")

        if not (0.0 <= self.RAG_HIGH_THRESHOLD <= 1.0):
            raise ValueError(f"RAG_HIGH_THRESHOLD must be between 0.0 and 1.0. Got: {self.RAG_HIGH_THRESHOLD}")
        if not (0.0 <= self.RAG_DISTANCE_THRESHOLD <= 1.0):
            raise ValueError(f"RAG_DISTANCE_THRESHOLD must be between 0.0 and 1.0. Got: {self.RAG_DISTANCE_THRESHOLD}")
        if self.RAG_HIGH_THRESHOLD > self.RAG_DISTANCE_THRESHOLD:
            raise ValueError(f"RAG_HIGH_THRESHOLD ({self.RAG_HIGH_THRESHOLD}) must be stricter or equal to RAG_DISTANCE_THRESHOLD ({self.RAG_DISTANCE_THRESHOLD}).")
        if self.RAG_SINGLE_CHUNK_HIGH_THRESHOLD > self.RAG_HIGH_THRESHOLD:
            raise ValueError(f"RAG_SINGLE_CHUNK_HIGH_THRESHOLD ({self.RAG_SINGLE_CHUNK_HIGH_THRESHOLD}) must be stricter or equal to RAG_HIGH_THRESHOLD ({self.RAG_HIGH_THRESHOLD}).")
        if not (0.0 <= self.RAG_MARGIN_THRESHOLD <= 1.0):
            raise ValueError(f"RAG_MARGIN_THRESHOLD must be between 0.0 and 1.0. Got: {self.RAG_MARGIN_THRESHOLD}")
        if self.RAG_MIN_VIABLE_COUNT < 1:
            raise ValueError(f"RAG_MIN_VIABLE_COUNT must be >= 1. Got: {self.RAG_MIN_VIABLE_COUNT}")
        if self.RAG_MIN_CONSENSUS_COUNT < 0:
            raise ValueError("RAG count limits cannot be negative.")
        if not (1 <= self.RAG_TOP_K <= 20):
            raise ValueError(f"RAG_TOP_K must be between 1 and 20. Got: {self.RAG_TOP_K}")

    # Enterprise Ecosystem Connectors (Phases 3.2 & 3.3)
    CONFLUENCE_URL: str = ""
    CONFLUENCE_PAT: str = "" 
    CONFLUENCE_SPACES: str = "ERK"
    ADO_URL: str = ""
    ADO_PAT: str = ""
    ADO_PROJECT: str = "Genoa Kiosk"
    ADO_TIMEOUT: int = 5           # Default JIT ADO REST API timeout in seconds (V.I.S.I.O.N. Refinement)

    # ADO Configuration)
    ADO_LOOKBACK_DAYS: int = 180  # How far back to search (default 6 months)
    ADO_INCLUDE_COMPLETED: bool = False  # Include closed/resolved tickets
    ADO_ENABLE_INTENT_CLASSIFICATION: bool = True  # Enable LLM intent (Layer 2)
    ADO_ENABLE_SCORING: bool = True  # Enable ticket scoring (Layer 3)
    ADO_RELEVANCE_THRESHOLD: float = 50.0  # Min score to return results (0-100)
    DATABASE_TARGET: str = "LOCAL" # Options: "LOCAL" (Chroma/SQLite) or "CLOUD" (Postgres/pgvector)

    # Cloud SQL PostgreSQL / pgvector Configurations (Phase 3.1 Cloud Production)
    PG_HOST: str = "127.0.0.1"
    PG_PORT: str = "5432"
    PG_DATABASE: str = "vision_db"
    PG_USER: str = "postgres"
    PG_PASSWORD: str = ""

# Create a single, importable instance of the settings.
settings = Settings()