import pandas as pd
from pathlib import Path

class CSVWorker:
    def __init__(self, items, items_lock):
        self.items = items
        self.items_lock = items_lock

    async def process_csv_file(self, file_path: Path):
        df = pd.read_csv(file_path)
        with self.items_lock:
            for _, row in df.iterrows():
                self.items.append(row.to_dict())