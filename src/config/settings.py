import os
import logging
import sys
from dotenv import load_dotenv; load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-5-nano-2025-08-07")

SIMILARITY_THRESHOLD = 0.35
JACCARD_WEIGHT = 1.30
LEVENSHTEIN_WEIGHT = 0.70