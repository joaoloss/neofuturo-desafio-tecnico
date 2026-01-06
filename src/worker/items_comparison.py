import Levenshtein

class ItemsComparison:

    @staticmethod
    def similarity(item1: str, item2: str) -> float:
        jaccard_dist = ItemsComparison._jaccard_distance(set(item1.item_description.split()), set(item2.item_description.split()))
        levenshtein_dist = ItemsComparison._levenshtein_similarity(item1, item2)

        combined_dist = (1.3 * jaccard_dist + 0.7 * levenshtein_dist) / 2.0
        return combined_dist 
    
    @staticmethod
    def _levenshtein_similarity(x, y):
        distance = Levenshtein.distance(x.unified_stemmed, y.unified_stemmed)
        max_len = max(len(x.unified_stemmed), len(y.unified_stemmed))
        return distance / max_len if max_len != 0 else 1.0
    
    @staticmethod
    def _jaccard_distance(x, y):
        inter = len(x.intersection(y))
        union = len(x) + len(y) - inter
        if union == 0:
            return 0
        else:
            return 1 - inter / union