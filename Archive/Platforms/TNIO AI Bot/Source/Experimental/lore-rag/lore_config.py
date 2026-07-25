from pathlib import Path


ROOT_DIR = Path("/home/REDACTED_DEPLOYMENT_USER/lore-rag")
GWS_BIN = Path("/home/REDACTED_DEPLOYMENT_USER/.npm-global/bin/gws")
ROOT_FOLDER_ID = "REDACTED_GOOGLE_DRIVE_FOLDER_ID_001"
ROOT_FOLDER_NAME = "TNIO"

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
EMBED_MODEL = "bge-m3"
COLLECTION_NAME = "lore"

EXPORT_DIR = ROOT_DIR / "exports"
STATE_DIR = ROOT_DIR / "state"
INDEX_DIR = ROOT_DIR / "index" / "chroma"
LOG_DIR = ROOT_DIR / "logs"

MANIFEST_PATH = STATE_DIR / "manifest.json"
CHUNKS_PATH = STATE_DIR / "chunks.jsonl"
RECORDS_DIR = STATE_DIR / "records"
RECORD_MANIFEST_PATH = RECORDS_DIR / "record_manifest.json"


DOC_MIME = "application/vnd.google-apps.document"
SHEET_MIME = "application/vnd.google-apps.spreadsheet"
FOLDER_MIME = "application/vnd.google-apps.folder"

MAX_CHARS = 1800
OVERLAP_CHARS = 250
DEFAULT_SEARCH_LIMIT = 8


# --------------------------------------------------------------------------- #
# Agent / answering tunables
# --------------------------------------------------------------------------- #

ANSWER_MODEL = "openai-codex/gpt-5.4-mini"
PLANNER_MODEL = "openai-codex/gpt-5.4-mini"
ROUTE_MODEL = "openai-codex/gpt-5.4-mini"
RERANK_MODEL = "openai-codex/gpt-5.4-mini"

AGENT_MAX_SECONDS = 18
AGENT_MAX_ITERATIONS = 4

RERANK_TOP_K = 18
ANSWER_TOP_K = 6
RERANK_MIN_SCORE = 4.0
RERANK_TIMEOUT_SECONDS = 8
