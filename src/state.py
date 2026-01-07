from dataclasses import dataclass, field
from typing import Dict, Set, List
import asyncio

from src.domain.item import Item

@dataclass
class AppState:
    # Data stores
    groups: Dict[int, List[Item]] = field(default_factory=dict)
    cols_hashed: Dict[int, str] = field(default_factory=dict)
    content_hashes: Set[int] = field(default_factory=set)
    
    # Locks for async safety
    groups_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    content_hashes_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    cols_hashed_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    
    # Statistics
    total_processed_files: int = 0
    total_items_processed: int = 0
    
    def get_next_group_id(self) -> int:
        """Get next available group ID"""
        return max(self.groups.keys(), default=-1) + 1
    
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
        async with self.groups_lock:
            if group_id not in self.groups:
                self.groups[group_id] = list()
            self.groups[group_id].append(item)
            self.total_items_processed += 1
    
    async def create_new_group(self, item: Item) -> int:
        """Create a new group with the item, returns new group ID"""
        async with self.groups_lock:
            new_group_id = self.get_next_group_id()
            self.groups[new_group_id] = [item]
            self.total_items_processed += 1
            return new_group_id

app_state = AppState()