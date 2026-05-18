import os

# Set dummy environment variables before any test imports
# This allows modules with module-level API clients to load without real credentials
# The tests that use cosine_similarity don't make real API calls
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")
os.environ.setdefault("QDRANT_HOST", "localhost")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
