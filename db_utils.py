import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from langchain_core.documents import Document
load_dotenv()


# db configutation variables
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")


# connect to db
def connect_to_db(
    db_name: str = DB_NAME,
    db_user: str = DB_USER,
    db_password: str = DB_PASSWORD,
    db_host: str = DB_HOST,
    db_port: int = DB_PORT
):
    try:
        conn = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        return cursor
    except Exception as e:
        print(f"Error connecting to database : {db_name} --> {str(e)}")
        raise str(e)


# create metadata table
def create_metadata():
    cursor = connect_to_db()

    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metadata(
                id SERIAL PRIMARY KEY,
                producer TEXT,
                creator TEXT,
                creationdate TIMESTAMP,
                moddate TIMESTAMP,
                source TEXT, 
                total_pages INT,
                page INT,
                page_label TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.connection.commit()
    except Exception as e:
        print(f"Error ar 'create_metadata_logs' : {str(e)}")
        return

    finally:
        cursor.connection.close()


# insert the metadata into db returning id
def save_metadata(chunks: list[Document]):
    cursor = connect_to_db()
    try:
        sql = """
                INSERT INTO metadata (
                    producer,
                    creator,
                    creationdate,
                    moddate,
                    source,
                    total_pages,
                    page,
                    page_label
                ) VALUES (%s, %s, %s,%s, %s, %s,%s, %s)
                RETURNING id;
            """

        for chunk in chunks:
            metadata = chunk.metadata
            cursor.execute(
                sql, (
                    metadata.get("producer"),
                    metadata.get("creator"),
                    metadata.get("creationdate"),
                    metadata.get("moddate"),
                    metadata.get("source"),
                    metadata.get("total_pages"),
                    metadata.get("page"),
                    metadata.get("page_label"),
                )
            )
            metadata_id = cursor.fetchone()["id"]
            metadata["document_id"] = str(metadata_id)

        cursor.connection.commit()
        return chunks
    except Exception as e:
        print(f"Error at 'save_metadata' --> {str(e)}")
        cursor.connection.rollback()
        raise str(e)

    finally:
        cursor.close()
        cursor.connection.close()
