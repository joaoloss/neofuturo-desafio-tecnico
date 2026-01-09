from time import time

from src.config import logger, SELECTING_SIMILAR_ITEM_PROMPT, SIMILARITY_THRESHOLD, SIZE_CANDIDATES_GROUP_FOR_LLM_PROMPT
from src.domain import Item
from src.llm import LLM
from src import app_state

class GroupingService:
    """Provides services for grouping items based on similarity. It persists the results in the global app state."""

    @staticmethod
    async def group_items(items: list[Item]) -> None:
        """
        Groups items based on similarity.
        Args:
            items (list[Item]): The list of items to be grouped.
        """

        similarity_threshold = SIMILARITY_THRESHOLD

        if len(app_state.groups) == 0: # First items, create groups directly
            for item in items:
                await app_state.create_new_group(item)
            return

        time_start = time()
        llm_latency = 0.0
        llm_use_count = 0

        scores = await GroupingService._compute_scores(items)

        for i, item in enumerate(items): # For each item, decide which group to add to (or create new)
            item_scores = scores[i]
            similar_items = [(idx, score) for idx, score in item_scores if score < similarity_threshold]

            ask_llm = True
            if len(similar_items) == 1: # Add to existing group
                group_idx = similar_items[0][0]
                group_key_words = app_state.groups[group_idx].key_words

                count_key_words_in_item = sum(1 for kw in group_key_words if kw in item.original_description)
                if len(group_key_words) == 0 or (count_key_words_in_item / len(group_key_words) >= 0.8): # In case of having key words, require at least 80% match (adjustable)
                    ask_llm = False
                    await app_state.add_to_group(group_idx, item)

            if ask_llm: # Use LLM to decide from candidates
                num_similar = len(similar_items) if len(similar_items) < SIZE_CANDIDATES_GROUP_FOR_LLM_PROMPT else SIZE_CANDIDATES_GROUP_FOR_LLM_PROMPT
                candidate_groups = item_scores[:num_similar+1] # Take top N similar groups
                prompt = GroupingService._build_prompt(item, candidate_groups)

                llm_time_start = time()
                response = await LLM.execute(prompt)
                llm_latency += time() - llm_time_start
                llm_use_count += 1

                selected_idx = int(response)

                if selected_idx != -1: # Add to existing group
                    await app_state.add_to_group(selected_idx, item)
                else: # Create new group
                    await app_state.create_new_group(item)
        
        time_end = time()
        logger.info(f"Grouped {len(items)} items in {time_end - time_start:.2f} seconds. LLM latency: {llm_latency:.2f} seconds. LLM usage: {llm_use_count}/{len(items)}.")

    @staticmethod
    async def _compute_scores(items: list[Item]) -> list[tuple[int, float]]:
        """
        Compute similarity scores of items against existing groups. Returns a list of list: scores[i] has
        a list of tuple with (group_idx, score) for item i ordered ascending by score.
        """

        scores = list() # List of list: scores[i] has a list of tuple with (group_idx, score) for item i ordered ascending by score
        for item in items: # For each item, compare with each existing group
            item_scores = list()

            for group_idx, group_items in app_state.groups.items():
                score = item.compare_with_items(list(group_items.items.values()))
                item_scores.append((group_idx, score))
            
            item_scores.sort(key=lambda x: x[1]) # Sort scores ascending by score
            scores.append(item_scores)
        
        return scores

    @staticmethod
    def _build_prompt(item: Item, candidate_groups: list[tuple[int, float]]) -> str:
        """Builds the prompt for the LLM to select the most similar item from candidate groups."""
        
        prompt_items = list()
        for group_idx, _ in candidate_groups:
            group = app_state.groups[group_idx]
            representative_group_item = list(group.items.values())[0] # Take first item as representative
            prompt_items.append(f"- número do item: {group_idx}, descrição: {representative_group_item.original_description}")
        
        prompt = SELECTING_SIMILAR_ITEM_PROMPT.format(
            items="\n".join(prompt_items),
            item=f"Descrição: {item.original_description}",
            possible_values=", ".join([str(idx) for idx, _ in candidate_groups] + ["-1"])
        ).strip()

        return prompt