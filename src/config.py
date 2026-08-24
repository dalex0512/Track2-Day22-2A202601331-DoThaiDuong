"""
Tải cấu hình từ file .env và thiết lập biến môi trường LangSmith.

⚠️  Import module này TRƯỚC KHI import bất kỳ thư viện LangChain nào.
    config.py tự động set LANGCHAIN_* vào os.environ khi được import.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from utils.console import configure_utf8_console

configure_utf8_console()

# Tải .env từ thư mục gốc của project (Lab/)
_root = Path(__file__).parent.parent
load_dotenv(_root / ".env")

# ── LangSmith — PHẢI set trước khi import LangChain ──────────────────────
# Hỗ trợ cả tên LANGSMITH_* hiện tại và alias LANGCHAIN_* cũ.
_langsmith_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY", "")
_langsmith_project = (
    os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT", "day22-lab")
)
_langsmith_endpoint = (
    os.getenv("LANGSMITH_ENDPOINT")
    or os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
)
_langsmith_tracing = (
    os.getenv("LANGSMITH_TRACING") or os.getenv("LANGCHAIN_TRACING_V2", "true")
)

os.environ["LANGSMITH_TRACING"] = _langsmith_tracing
os.environ["LANGCHAIN_TRACING_V2"] = _langsmith_tracing
os.environ["LANGSMITH_API_KEY"] = _langsmith_key
os.environ["LANGCHAIN_API_KEY"] = _langsmith_key
os.environ["LANGSMITH_PROJECT"] = _langsmith_project
os.environ["LANGCHAIN_PROJECT"] = _langsmith_project
os.environ["LANGSMITH_ENDPOINT"] = _langsmith_endpoint
os.environ["LANGCHAIN_ENDPOINT"] = _langsmith_endpoint

# ── Provider mặc định ─────────────────────────────────────────────────────
# Đổi giá trị PROVIDER trong .env: openai | gemini | anthropic | ollama | openrouter
PROVIDER = os.getenv("PROVIDER", "openai").lower()

# ── OpenAI ────────────────────────────────────────────────────────────────
OPENAI_API_KEY         = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL        = os.getenv("OPENAI_BASE_URL", "")   # để trống nếu dùng OpenAI chính thức
OPENAI_MODEL           = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# ── Google Gemini ─────────────────────────────────────────────────────────
GOOGLE_API_KEY          = os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL            = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_EMBEDDING_MODEL  = os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")

# ── Anthropic ─────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL   = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

# ── Ollama (local, không cần API key) ────────────────────────────────────
OLLAMA_BASE_URL         = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL            = os.getenv("OLLAMA_MODEL", "llama3.1")
OLLAMA_EMBEDDING_MODEL  = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

# ── OpenRouter ────────────────────────────────────────────────────────────
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL    = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# ── LangSmith ─────────────────────────────────────────────────────────────
LANGSMITH_API_KEY = _langsmith_key
LANGSMITH_PROJECT = _langsmith_project


def _is_missing(value: str) -> bool:
    """Coi giá trị rỗng hoặc placeholder trong .env.example là chưa cấu hình."""
    normalized = value.strip().lower()
    return not normalized or normalized.startswith("your_")


def validate() -> bool:
    """
    Kiểm tra các biến môi trường bắt buộc đã được cấu hình.
    Trả về True nếu hợp lệ, False nếu thiếu.
    """
    missing = []

    valid_providers = {"openai", "gemini", "anthropic", "ollama", "openrouter"}
    if PROVIDER not in valid_providers:
        print(
            f"❌ PROVIDER không hợp lệ: '{PROVIDER}'. "
            f"Chọn một trong: {', '.join(sorted(valid_providers))}"
        )
        return False

    if _is_missing(LANGSMITH_API_KEY):
        missing.append("LANGSMITH_API_KEY hoặc LANGCHAIN_API_KEY (LangSmith)")

    if PROVIDER == "openai" and _is_missing(OPENAI_API_KEY):
        missing.append("OPENAI_API_KEY")
    elif PROVIDER == "gemini" and _is_missing(GOOGLE_API_KEY):
        missing.append("GOOGLE_API_KEY")
    elif PROVIDER == "anthropic" and _is_missing(ANTHROPIC_API_KEY):
        missing.append("ANTHROPIC_API_KEY")
    elif PROVIDER == "openrouter" and _is_missing(OPENROUTER_API_KEY):
        missing.append("OPENROUTER_API_KEY")
    if PROVIDER in {"anthropic", "openrouter"} and _is_missing(OPENAI_API_KEY):
        missing.append("OPENAI_API_KEY (dùng cho embeddings)")
    # Ollama: không cần API key

    if missing:
        print("⚠️  Thiếu biến môi trường:")
        for m in missing:
            print(f"   - {m}")
        print("   Hãy kiểm tra file .env của bạn (xem .env.example để biết thêm).")
        return False

    print(f"✅ Config OK  |  Provider: {PROVIDER.upper()}  |  Project: {LANGSMITH_PROJECT}")
    return True


if __name__ == "__main__":
    validate()
