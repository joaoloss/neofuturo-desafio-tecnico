from fastapi import FastAPI, UploadFile
import pandas as pd
from pypdf import PdfReader
import os
from pathlib import Path
import asyncio

storage_path = Path("ingested_files")
os.makedirs(storage_path, exist_ok=True)

app = FastAPI()

async def simulate_long_task():
    print("Simulating a long task...")
    await asyncio.sleep(10)
    print("Long task completed.")

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    file_location = storage_path / file.filename
    with open(file_location, "wb") as f:
        content = await file.read()
        f.write(content)
    asyncio.create_task(simulate_long_task())
    

def main():
    print("Hello from neofuturo-desafio-tecnico!")

if __name__ == "__main__":
    main()
