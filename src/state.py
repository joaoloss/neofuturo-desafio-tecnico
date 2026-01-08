from dataclasses import dataclass, field
import asyncio
from pathlib import Path
import os
import json

from src.domain import Item, Group

@dataclass
class AppState:
    """Represents the global application state."""

    # Data stores
    groups: dict[int, Group] = field(default_factory=dict)
    cols_hashed: dict[int, str] = field(default_factory=dict)
    content_hashes: set[int] = field(default_factory=set)
    
    # Locks for async safety
    groups_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    content_hashes_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    cols_hashed_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    # Statistics
    total_processed_files: int = 0
    total_items_processed: int = 0
    
    async def add_content_hash(self, content_hash: int) -> bool:
        """Add content hash if not duplicate, returns True if added"""
        async with self.content_hashes_lock:
            if content_hash in self.content_hashes:
                return False
            self.content_hashes.add(content_hash)
            return True
    
    async def get_cached_columns(self, cols_hash: int) -> str | None:
        """Get cached useful columns for a column hash"""
        async with self.cols_hashed_lock:
            return self.cols_hashed.get(cols_hash)
    
    async def set_cached_columns(self, cols_hash: int, useful_cols: str):
        """Cache useful columns for a column hash"""
        async with self.cols_hashed_lock:
            self.cols_hashed[cols_hash] = useful_cols
    
    async def add_to_group(self, group_id: int, item: Item):
        """Safely add item to a group"""

        group = None
        async with self.groups_lock:
            if group_id not in self.groups: # Create group if not exists
                self.groups[group_id] = Group(group_id)
            group = self.groups[group_id]
            self.total_items_processed += 1
        
        await group.add_item(item)

    async def change_item_group(self, item_id: str, new_group_idx: int) -> int | None:
        """
        Change the group of an item manually. Returns the previous group index if successful, or None if the item was not found.
        
        Args:
            item_id (str): system ID of the item to move.
            new_group_idx (int): Target group index to move the item to (-1 for new group).
        """

        async with self.groups_lock:

            if new_group_idx != -1 and new_group_idx not in self.groups.keys():
                return False  # Target group does not exist

            # Find the item and its current group
            current_group_idx = None
            current_group = None
            item_to_move = None
            for idx, group in self.groups.items():
                item = await group.get_item_by_id(item_id)
                if item:
                    current_group = group
                    current_group_idx = idx
                    item_to_move = item
                    break
            
            if not item_to_move:
                return None # Item not found
            
            # Remove from current group
            await current_group.remove_item(item_to_move)
            
            # Add to new group or create new group
            if new_group_idx == -1:
                new_group_idx = max(self.groups.keys(), default=-1) + 1
                self.groups[new_group_idx] = Group(new_group_idx)
            
            new_group = self.groups[new_group_idx]
            await new_group.add_item(item_to_move)
        
        return current_group_idx
    
    async def create_new_group(self, item: Item) -> int:
        """Create a new group with the item, returns new group ID"""
        new_group = None
        async with self.groups_lock:
            new_group_id = max(self.groups.keys(), default=-1) + 1
            new_group = Group(new_group_id)
            self.groups[new_group_id] = new_group
            self.total_items_processed += 1
            
        await new_group.add_item(item)
        return new_group.group_id
    
    async def dump(self, folder_path: str):
        """Dump the current state of groups into a JSON file for inspection"""

        os.makedirs(folder_path, exist_ok=True)
        folder_path = Path(folder_path)

        output = dict()
        async with self.groups_lock:
            for group_idx, group in self.groups.items():
                async with group.lock:
                    output[group_idx] = [{"description": item.original_description, "system_item_id": item.system_id, "origin_file": item.origin_file} for item in group.items.values()]
        
        with open(folder_path / "groups.json", "w") as f:
            json.dump(output, f, indent=4)

app_state = AppState()