from pydantic import BaseModel
from enum import Enum


class DocumentItem(BaseModel):
    name: str
    path: str
    size: int


class FileDeleteRequest(BaseModel):
    name: str


class ChunkingStrategies(str, Enum):
    SEMANTIC = "semantic",
    RECURSIVE = "recursive"
