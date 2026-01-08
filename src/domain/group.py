from asyncio import Lock

from . import Item

class Group:
    """
    Represents a group of similar items.
    Attributes:
        group_id (int): Unique identifier for the group.
        items (dict[str, Item]): Dictionary of items in the group, keyed by their system_id.
        key_words (set[str]): Set of key words associated with the group.
        lock (Lock): Asynchronous lock for thread-safe operations on the group.
    """

    def __init__(self, group_id: int):
        self.group_id = group_id
        self.items: dict[str, Item] = dict()
        self.key_words: set[str] = set()
        self.lock = Lock()
    
    async def add_item(self, item: Item):
        """Adds an item to the group."""

        async with self.lock:
            self.items[item.system_id] = item
            item.group_id = self.group_id
    
    async def remove_item(self, item_id: str) -> Item | None:
        """Removes an item from the group by its ID. Returns the removed item, or None if not found."""
        
        async with self.lock:
            item = self.items.pop(item_id, None)
            if item:
                item.group_id = None
            return item
    
    async def get_item_by_id(self, system_item_id: str) -> Item | None:
        """Returns the item with the given system ID if it exists in the group."""
        
        async with self.lock:
            item = self.items.get(system_item_id)
            return item

    async def add_key_words(self, key_words: list[str]):
        """Adds key words to the group. Both original and stemmed versions are stored."""
        
        key_words = [kw.strip().lower() for kw in key_words if kw.strip()]
        stemmed_key_words = {Item.stemmer.stem(kw) for kw in key_words}

        async with self.lock:
            for kw in key_words:
                self.key_words.add(kw)
            for skw in stemmed_key_words:
                self.key_words.add(skw)