import os
import logging
import sys
from dotenv import load_dotenv; load_dotenv()
from functools import lru_cache

class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    llm_model_name: str = os.getenv("LLM_MODEL_NAME", "gpt-5-nano-2025-08-07")

    @staticmethod
    def config_logger(level=logging.DEBUG):
        logger = logging.getLogger("app")
        if logger.handlers:
            return logger # already configured

        logger.setLevel(logging.DEBUG) # let handlers check log levels
        logger.propagate = False # prevent double logging

        pattern = "[%(levelname)s - %(asctime)s] %(message)s"
        formatter = logging.Formatter(pattern)
        
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(level)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

        return logger