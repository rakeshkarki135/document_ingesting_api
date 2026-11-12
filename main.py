
import os
import shutil
from pathlib import Path

from fastapi import FastAPI
from pydantic_models import DocumentItem, FileDeleteRequest, ChunkingStrategies, Chunks
from fastapi import UploadFile, File, HTTPException
from pypdf import PdfReader
from chunks import load_and_split_document, recursive_text_splitter, semantic_chunker, index_document_to_pinecone
from db_utils import create_metadata, save_metadata


app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Welcome to Document Ingesation API."}


@app.post("/upload-doc")
def upload_document_files(file: UploadFile = File(...)):

    allowed_extensions = [".pdf", ".txt"]
    file_extensions = os.path.splitext(file.filename)[1].lower()

    if file_extensions not in allowed_extensions:
        raise HTTPException(
            status_code=500, detail=f"Unsupported file format allowed types are {",".join(allowed_extensions)}"
        )

    file_path = f"./documents/{file.filename}"
    if os.path.exists(file_path):
        raise HTTPException(
            status_code=400, detail="File already Exists"
        )

    try:
        # save and upload file to temporary fie
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Bad Request : {str(e)}"
        )

    return {"message": f"File Uploaded successfuly as {file_path}"}


@app.get("/list-doc", response_model=list[DocumentItem])
def list_documents():
    files_list = []
    file_path = Path("./documents")
    for file in file_path.iterdir():
        if file.is_file():
            files_list.append(
                {
                    "name": file.name,
                    "path": str(file),
                    "size": file.stat().st_size
                }
            )

    return files_list


@app.post("/delete-doc")
def delete_document(request: FileDeleteRequest):
    files_dir = Path("./documents")

    for file in files_dir.iterdir():
        if file.name == request.name:
            os.remove(file)
            return {"message": "File deleted successfully."}

    return {"message": "File does not Exist."}


@app.post("/process-doc")
def process_the_document(strategy: ChunkingStrategies):
    chunks = load_and_split_document(
        chunking_strategy=strategy
    )

    if not chunks:
        raise HTTPException(
            status_code=404, detail="No Chunks were created. Please make sure you have uploaded documents."
        )

    chunks = save_metadata(chunks=chunks)
    if not chunks:
        raise HTTPException(
            status_code=500, detail="Error on saving the metadata."
        )

    success = index_document_to_pinecone(chunks)

    if success:
        return {"message": "Document processed successfully"}

    return {"message": "Failed to add embeddings to Pinecone."}
