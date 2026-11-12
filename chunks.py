import os
from pathlib import Path
from pinecone import Pinecone
from pinecone import ServerlessSpec
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
load_dotenv()

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
embeddings = OllamaEmbeddings(model="qwen3-embedding:8b", dimensions=1024)
recursive_text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    length_function=len
)

semantic_chunker = SemanticChunker(
    embeddings,
    breakpoint_threshold_type="percentile"
)


def load_and_split_document(chunking_strategy, document_path: str = "./documents") -> list[Document]:
    documents = []
    document_dir = Path(document_path)
    for file in document_dir.iterdir():
        if file.is_file():
            file_extension = os.path.splitext(file)[1].lower()

            if file_extension == ".pdf":
                loader = PyPDFLoader(file)
            elif file_extension == ".txt":
                loader = TextLoader(file)
            else:
                print(f"Unsupported File Format : {file_extension}")
                continue

            documents.extend(loader.load())

    if chunking_strategy == "semantic":
        return semantic_chunker.create_documents([doc.page_content for doc in documents])
    elif chunking_strategy == "recursive":
        return recursive_text_splitter.split_documents(documents)

    raise ValueError("Documents are not found.")


def index_document_to_pinecone(chunks: list[Document], index_name: str = "chunk-index"):
    try:
        if not pc.has_index(index_name):
            pc.create_index(
                name=index_name,
                dimension=1024,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )

        index = pc.Index(index_name)
        document_embedings = embeddings.embed_documents(
            [chunk.page_content for chunk in chunks])

        vectors = [
            {
                "id": str(chunk.metadata["document_id"]),
                "values": embedding,
                "metadata": {
                    "source": chunk.metadata["source"],
                    "page": chunk.metadata["page"],
                    "page_label": chunk.metadata["page_label"],
                    "text": chunk.page_content

                }
            } for chunk, embedding in zip(chunks, document_embedings)
        ]

        index.upsert(vectors=vectors)

        return True
    except Exception as e:
        print(f"Excep at 'index_document_to_pinecone' --> {str(e)}")
        return False
