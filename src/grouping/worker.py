from time import time

from src.domain import Item
from src.config import Settings, SELECTING_SIMILAR_ITEM_PROMPT
from src.llm import LLM
from src.state import app_state

logger = Settings.config_logger()

class GroupingWorker:

    @staticmethod
    async def group_items(items: list[Item]) -> None:
        """
        Groups items based on their origin file.
        Args:
            items (list[Item]): The list of items to be grouped.
        """

        similarity_threshold = Settings.similarity_threshold

        if len(app_state.groups) == 0: # First items, create groups directly
            for item in items:
                await app_state.create_new_group(item)
            return

        time_start = time()
        llm_latency = 0.0
        llm_use_count = 0

        scores = list() # List of list: scores[i] has a list of tuple with (group_idx, score) for item i ordered ascending by score
        for item in items: # For each item, compare with each existing group
            item_scores = list()

            async with app_state.groups_lock:
                for group_idx, group_items in enumerate(app_state.groups.values()):
                    score = item.compare_with_items(group_items)
                    item_scores.append((group_idx, score))
            
            item_scores.sort(key=lambda x: x[1]) # Sort scores ascending by score
            scores.append(item_scores)

        for i, item in enumerate(items): # For each item, decide which group to add to (or create new)
            item_scores = scores[i]
            similar_items = [(idx, score) for idx, score in item_scores if score < similarity_threshold]

            if len(similar_items) == 1: # Add to existing group
                group_idx = similar_items[0][0]
                await app_state.add_to_group(group_idx, item)

            else: # Use LLM to decide from candidates
                num_similar = len(similar_items) if len(similar_items) < 4 else 4
                candidate_groups = item_scores[:num_similar+1] # Take top N similar groups
                
                prompt_items = list()
                for group_idx, _ in candidate_groups:
                    group_item = app_state.groups[group_idx][0] # Take first item as representative
                    prompt_items.append(f"- número do item: {group_idx}, descrição: {group_item.original_description}")
                
                prompt = SELECTING_SIMILAR_ITEM_PROMPT.format(
                    items="\n".join(prompt_items),
                    item=f"Descrição: {item.original_description}",
                    possible_values=", ".join([str(idx) for idx, _ in candidate_groups] + ["-1"])
                ).strip()

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
        logger.info(f"Grouped {len(items)} items in {time_end - time_start:.2f} seconds. LLM latency: {llm_latency:.2f} seconds. LLM usage: {llm_use_count} times.")
