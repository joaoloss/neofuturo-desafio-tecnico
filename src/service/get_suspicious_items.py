import random

from src import app_state
from src.config import SIMILARITY_THRESHOLD

class GetSuspiciousItemsService:
    """Service to find suspicious items after manual group changes."""

    @staticmethod
    def find_suspicious_items_in_group(group_a_idx: int, group_b_idx: int) -> list[dict[str, str | float]]:
        """
        Detects items currently assigned to group A that may be misclassified and should instead belong to group B..

        Args:
            group_a_idx (int): The index of the first group.
            group_b_idx (int): The index of the second group.
        Returns:
            list[str]: List of system IDs of suspicious items.
        """

        group_b = app_state.groups.get(group_b_idx)
        group_a = app_state.groups.get(group_a_idx)

        if not group_a or not group_b:
            return []
        
        items_a = list(group_a.items.values())
        items_b = list(group_b.items.values())
        key_words_b = group_b.key_words

        suspicious_items = list()
        for item_a in items_a:
            score = item_a.compare_with_items(items_b)

            if score < SIMILARITY_THRESHOLD or any(kw in item_a.original_description for kw in key_words_b):
                suspicious_items.append({"system_id": item_a.system_id, "similarity_score": score, "description": item_a.original_description})

        return suspicious_items