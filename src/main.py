from fastapi import FastAPI, UploadFile, BackgroundTasks
from datetime import datetime
import pandas as pd
import os
from pathlib import Path
from threading import Lock
from src.config.settings import Settings
from src.config.prompts import SELECTING_USEFUL_COLS_PROMPT
from src.llm.llm import LLM
import logging

logger = Settings.config_logger()

storage_path = Path("ingested_files"); os.makedirs(storage_path, exist_ok=True)

items = list(); items_lock = Lock()

cols_hashed = dict(); cols_hashed_lock = Lock()
async def process_csv_file(file_path: Path):
    df = pd.read_csv(file_path)
    cols = set(df.columns)
    cols_hash = hash(frozenset(cols))

    useful_cols = None
    with cols_hashed_lock:
        if cols_hash in cols_hashed:
            logger.debug(f"Cache hit for useful columns.")
            useful_cols = cols_hashed[cols_hash]
        else:
            logger.debug(f"Cache miss for useful columns. Determining via LLM.")
            cols = ", ".join(df.columns)
            item = df.iloc[0].to_dict()
            item = [f"- {k}: {v}" for k, v in item.items()]
            prompt = SELECTING_USEFUL_COLS_PROMPT.format(
                cols=", ".join(df.columns),
                item="\n".join(item)
            ).strip()
            response = await LLM.execute(prompt)
            useful_cols = response
            cols_hashed[cols_hash] = useful_cols
    
    logger.debug(f"Cached useful columns for hash {cols_hash}: {useful_cols}")

content_hashes = set(); content_hashes_lock = Lock()
async def save_file(uploaded_file: UploadFile) -> Path | None:
    content = await uploaded_file.read()
    content_hash = hash(content)

    with content_hashes_lock:
        if content_hash in content_hashes:
            return None
        content_hashes.add(content_hash)
    
    file_location = storage_path / f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.filename}"
    with open(file_location, "wb") as f:
        f.write(content)

    return file_location

app = FastAPI()

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    
    if not file.filename.endswith(".csv"):
        return {"error": "Only CSV files are supported."}

    file_location = await save_file(file)
    if file_location:
        background_tasks.add_task(process_csv_file, file_location)

    return {"info": f"file '{file.filename}' received."}
    
def main():
    print("Hello from neofuturo-desafio-tecnico!")

if __name__ == "__main__":
    main()
