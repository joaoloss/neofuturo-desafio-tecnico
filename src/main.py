from fastapi import FastAPI, UploadFile, BackgroundTasks
from contextlib import asynccontextmanager
from datetime import datetime
import pandas as pd
import os
from pathlib import Path
from threading import Lock
import json
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

from src.config import Settings, SELECTING_USEFUL_COLS_PROMPT
from src.llm import LLM
from src.domain import Item
from src.grouping import GroupingWorker
from src.state import app_state

logger = Settings.config_logger()
storage_path = Path("ingested_files"); os.makedirs(storage_path, exist_ok=True)

async def process_csv_file(file_path: Path):
    df = pd.read_csv(file_path)
    cols = set(df.columns)
    cols_hash = hash(frozenset(cols))

    useful_cols = await app_state.get_cached_columns(cols_hash)
    if useful_cols is None:
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
        await app_state.set_cached_columns(cols_hash, useful_cols)
    else:
        logger.debug(f"Cache hit for useful columns.")
    
    logger.debug(f"Cached useful columns for hash {cols_hash}: {useful_cols}")

    id_col = useful_cols.split(",")[0].strip()
    descriptive_cols = [col.strip() for col in useful_cols.split(",") if col.strip() != id_col]
    
    items_to_add = list()
    for _, row in df.iterrows():
        id_ = row.get(id_col, None)
        descriptive_cols_data = [str(row[col]) for col in descriptive_cols if col in row]
        item = Item(
            descriptive_cols_data=descriptive_cols_data,
            origin_file=str(file_path),
            item_id=str(id_)
        )
        items_to_add.append(item)
    
    await GroupingWorker.group_items(items_to_add)
        
content_hashes = set(); content_hashes_lock = Lock()
async def save_file(uploaded_file: UploadFile) -> Path | None:
    """
    Save uploaded file if its content is new (not a duplicate). Return file path if saved, else None.
    """
    content = await uploaded_file.read()
    content_hash = hash(content)

    added = await app_state.add_content_hash(content_hash)
    if not added:
        return None # Duplicate file
    
    file_location = storage_path / f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded_file.filename}"
    with open(file_location, "wb") as f:
        f.write(content)

    return file_location

@asynccontextmanager
async def lifespan(app: FastAPI):
    pass

    yield

    # Dump groups into a JSON file for inspection
    os.makedirs("dump", exist_ok=True)
    output = dict()
    for group_idx, items in app_state.groups.items():
        output[group_idx] = [{"description": item.original_description, "item_id": item.id, "origin_file": item.origin_file} for item in items]
    
    with open("dump/groups.json", "w") as f:
        json.dump(output, f, indent=4)

app = FastAPI(lifespan=lifespan)

@app.post("/uploadfile/")
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    
    if file.filename.endswith(".csv"):
        file_location = await save_file(file)
        if file_location: # New file saved
            background_tasks.add_task(process_csv_file, file_location)
        
        return {"info": f"file '{file.filename}' received."}
    else:
        return {"error": "Only CSV files are supported."}

@app.get("/groups/")
async def get_groups(limit: int = 10, offset: int = 0, itens_per_group: int = 3):
    """Get paginated groups for inspection"""
    async with app_state.groups_lock:
        total = len(app_state.groups)
        groups_slice = dict(list(app_state.groups.items())[offset:offset+limit])
        
        result = {}
        for group_idx, items in groups_slice.items():
            result[group_idx] = {
                "size": len(items),
                "items": [
                    {
                        "item_id": item.id,
                        "description": item.original_description,
                        "origin_file": item.origin_file
                    }
                    for item in items[:itens_per_group]
                ]
            }
        
        return {
            "total_groups": total,
            "offset": offset,
            "limit": limit,
            "groups": result
        }

