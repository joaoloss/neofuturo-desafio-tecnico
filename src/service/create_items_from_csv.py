import pandas as pd
from pathlib import Path

from src.config import logger, SELECTING_USEFUL_COLS_PROMPT
from src.llm import LLM
from src.domain import Item, Group
from src import app_state

class CSVItemCreatorService:
    """Service to create items from a CSV file."""

    @staticmethod
    async def process_csv_file(file_path: Path) -> list[Item]:
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
        
        return items_to_add