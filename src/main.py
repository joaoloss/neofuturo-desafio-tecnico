from fastapi import FastAPI, UploadFile, BackgroundTasks
from contextlib import asynccontextmanager
from datetime import datetime
import os
from pathlib import Path

from src.config import logger
from src.service import CSVItemCreatorService, GroupingService, GetSuspiciousItemsService
from . import app_state

storage_path = Path("ingested_files"); os.makedirs(storage_path, exist_ok=True)

async def background_file_processing(file_path: Path) -> None:
    """Background task to process uploaded CSV file."""

    if file_path.suffix.lower() == ".csv":
        items = await CSVItemCreatorService.process_csv_file(file_path)
    else:
        logger.warning(f"Unsupported file type for file: {file_path}")
        return
    
    logger.debug(f"Processing {len(items)} items from file: {file_path}")
    await GroupingService.group_items(items)
    logger.debug(f"Completed processing for file: {file_path}")
        
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

    await app_state.dump("dump")

app = FastAPI(lifespan=lifespan)

@app.post("/uploadfile/")
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks):
    """Endpoint to upload a file for processing."""

    file_location = await save_file(file)
    if file_location: # New file saved
        background_tasks.add_task(background_file_processing, file_location)
        
    return {"info": f"file '{file.filename}' received."}

@app.post("/changeitemgroup/")
async def change_item_group(item_id: str, new_group_idx: int, key_words: list[str] = []):
    """
    Change the group of an item manually.

    Args:
        item_id (str): system ID of the item to move.
        new_group_idx (str): Target group index to move the item to (-1 for new group).
        key_words (list[str], optional): Important keywords that items of the new group should have.
    """

    old_group_idx = await app_state.change_item_group(item_id, new_group_idx)
    if old_group_idx is None:
        return {"info": f"Item with system ID '{item_id}' not found and/or target group with ID {new_group_idx} does not exist."}

    if key_words:
        # Add key words to the new group
        target_group_idx = new_group_idx
        if new_group_idx == -1:
            # Get the newly created group ID
            async with app_state.groups_lock:
                target_group_idx = max(app_state.groups.keys())
        
        target_group = app_state.groups[target_group_idx]
        await target_group.add_key_words(key_words)
    
    suspicious_items = GetSuspiciousItemsService.find_suspicious_items_in_group(old_group_idx, new_group_idx)
    
    return {"info": f"Item with system ID '{item_id}' moved to group {new_group_idx} successfully.", "suspicious_items": suspicious_items}

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

