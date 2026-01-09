import pandas as pd
from pathlib import Path
import pdfplumber

from src.config import logger, SELECTING_USEFUL_COLS_PROMPT
from src.llm import LLM
from src.domain import Item
from src import app_state

class PDFItemCreatorService:
    """Service to create items from a PDF file."""

    @staticmethod
    async def process_pdf_file(file_path: Path) -> list[Item]:
        tables = list()
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables():
                    cols = table[0]
                    content = table[1:]
                    tables.append(pd.DataFrame(content, columns=cols))

        if not tables:
            logger.warning(f"No tables found in PDF file: {file_path}")
            return []

        df = pd.concat(tables, ignore_index=True)
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