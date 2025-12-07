import sys
import json
import chromadb
import os

# Increase field limit for large JSONs
json_limit = 100 * 1024 * 1024 # 100MB
sys.set_int_max_str_digits(0) # Python 3.11+ safety limit removal if needed

def main():
    print(f"Worker using ChromaDB version: {chromadb.__version__}", file=sys.stdout)
    try:
        # Read JSON payload from stdin
        input_data = sys.stdin.read()
        if not input_data:
            print("Error: No input data received", file=sys.stderr)
            sys.exit(1)
            
        data = json.loads(input_data)
        
        persist_directory = data.get("persist_directory", "chroma_db")
        collection_name = data.get("collection_name", "enerji_mevzuati")
        documents = data.get("documents", [])
        embeddings = data.get("embeddings", [])
        metadatas = data.get("metadatas", [])
        ids = data.get("ids", [])
        
        if not documents:
            print("Warning: No documents to add", file=sys.stderr)
            sys.exit(0)

        # Initialize ChromaDB
        # This process ONLY imports chromadb, no torch.
        client = chromadb.PersistentClient(path=persist_directory)
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"} 
        )
        
        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Successfully added {len(documents)} documents via worker process.")
        
    except Exception as e:
        print(f"CRITICAL ERROR in chroma_worker: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
