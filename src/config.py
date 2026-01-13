import os
from dotenv import load_dotenv

load_dotenv()

VECTOR_DB_PATH = "./vector-db"
KNOWLEDGE_BASE_PATH = "./data/knowledgeBase.json"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GEMINI_MODEL = "google_genai:gemini-2.0-flash"

# Ensure API Key is set
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY not found in environment variables")