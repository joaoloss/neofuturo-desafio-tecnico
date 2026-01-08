import re
import nltk; nltk.download('rslp')
from nltk.stem import RSLPStemmer
import random
import Levenshtein
from unidecode import unidecode
from uuid import uuid4

from src.config import JACCARD_WEIGHT, LEVENSHTEIN_WEIGHT

class Item:
    """
    Represents an item with personalized attributes used for similarity calculations.
    Attributes:
        system_id (str): System-generated unique identifier for the item.
        original_id (str): Unique identifier for the item defined by the ingested file.
        origin_file (str): The file from which the item was ingested.
        original_description (str): The original textual description of the item.
        words_set (set): Set of unique stemmed words from the item's description for Jaccard distance calculations.
        unified_description (str): Unified stemmed description string for Levenshtein distance calculations.
        group_id (int | None): The group ID to which the item belongs.
    """

    stemmer = RSLPStemmer()

    def __init__(self, descriptive_cols_data: list[str], origin_file: str, item_id: str):
        complete_description = unidecode(" ".join(descriptive_cols_data))
        complete_description = re.sub(r"\s+", " ", complete_description).strip().lower()
        stemmed_description = [self.stemmer.stem(word) for word in complete_description.split()]

        self.system_id = str(uuid4())
        self.original_id = item_id
        self.origin_file = origin_file
        self.original_description = complete_description
        self.words_set = set(stemmed_description)
        self.unified_description = "".join(stemmed_description)
        self.group_id = None
    
    def compare_with_items(self, other_items: list["Item"]) -> list[float]:
        """
        Calculates the average similarity score with the given group of items by sampling
        up to 5 items from the group and averaging their similarity scores.
        """

        group_size = len(other_items)
        sample_idxs = list(range(group_size)) if group_size < 5 else random.sample(range(group_size), 5)

        avg_score = 0.0
        for idx in sample_idxs:
            other_item = other_items[idx]
            avg_score += self.compute_similarity(other_item)
        avg_score = avg_score / len(sample_idxs)

        return avg_score
    
    def compute_similarity(self, other_item: "Item") -> float:
        """
        Computes similarity score with another item.
        """
        jaccard_weight = JACCARD_WEIGHT
        levenshtein_weight = LEVENSHTEIN_WEIGHT

        jaccard_dist = Item._jaccard_distance(self.words_set, other_item.words_set)
        levenshtein_dist = Item._levenshtein_similarity(self.unified_description, other_item.unified_description)
        combined_dist = (jaccard_weight * jaccard_dist + levenshtein_weight * levenshtein_dist) / 2.0
        return combined_dist
    
    @staticmethod
    def _levenshtein_similarity(x: str, y: str) -> float:
        distance = Levenshtein.distance(x, y)
        max_len = max(len(x), len(y))
        return distance / max_len if max_len != 0 else 1.0
    
    @staticmethod
    def _jaccard_distance(x: set, y: set) -> float:
        inter = len(x.intersection(y))
        union = len(x) + len(y) - inter
        if union == 0:
            return 0
        else:
            return 1 - inter / union
    
    