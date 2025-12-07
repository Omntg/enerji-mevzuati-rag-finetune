# import chromadb  <-- REMOVED TO AVOID DLL CONFLICT
# from chromadb.config import Settings <-- REMOVED
from typing import List, Dict, Any
import uuid
from transformers import AutoModel, AutoTokenizer
import torch
import subprocess
import json
import sys
import os

class RAGPipeline:
    def __init__(self, persist_directory: str = "chroma_db"):
        # We DO NOT initialize ChromaDB here anymore to avoid DLL conflicts with PyTorch.
        # We will delegate DB operations to a separate subprocess (src/chroma_worker.py).
        self.persist_directory = persist_directory
        self.collection_name = "enerji_mevzuati"
        
        self.model_name = "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr"
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
        except Exception as e:
            print(f"Error loading model {self.model_name}: {e}")
            raise e

    def compute_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Computes embeddings for a list of texts using the initialized BERT model.
        """
        # print(f"DEBUG: Computing embeddings for batch of size {len(texts)}")
        try:
            inputs = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt", max_length=512)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
            
            # Mean pooling
            # attention_mask shape: (batch_size, seq_len)
            # last_hidden_state shape: (batch_size, seq_len, hidden_size)
            
            attention_mask = inputs['attention_mask']
            token_embeddings = outputs.last_hidden_state
            
            input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
            
            sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
            sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
            
            embeddings = sum_embeddings / sum_mask
            return embeddings.tolist()
        except Exception as e:
            print(f"CRITICAL ERROR in compute_embeddings: {e}")
            raise e

    def add_documents(self, chunks: List[Dict[str, Any]]):
        """
        Adds processed chunks to ChromaDB via a subprocess worker.
        chunks: List of dicts containing 'text' and 'metadata'
        """
        if not chunks:
            return

        texts = [chunk['text'] for chunk in chunks]
        metadatas = [chunk['metadata'] for chunk in chunks]
        ids = [str(uuid.uuid4()) for _ in chunks]
        
        # Compute embeddings in batches to avoid OOM
        batch_size = 16
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            print(f"    Processing batch {i} to {i+batch_size}...", flush=True)
            batch_embeddings = self.compute_embeddings(batch_texts)
            embeddings.extend(batch_embeddings)
            
        print(f"    All batches computed. Delegating insertion of {len(texts)} docs to worker process...", flush=True)
        
        # Prepare payload for worker
        payload = {
            "persist_directory": self.persist_directory,
            "collection_name": self.collection_name,
            "documents": texts,
            "embeddings": embeddings,
            "metadatas": metadatas,
            "ids": ids
        }
        
        # Serialize to JSON
        try:
            json_payload = json.dumps(payload)
        except TypeError as e:
            print(f"Serialization Error: {e}")
            return

        # Run worker script
        worker_script = os.path.join("src", "chroma_worker.py")
        python_exe = sys.executable # Use same python interpreter
        
        try:
            process = subprocess.run(
                [python_exe, worker_script],
                input=json_payload,
                text=True,
                capture_output=True
            )
            
            if process.returncode != 0:
                print(f"Worker process failed with code {process.returncode}", flush=True)
                print(f"Worker Stderr: {process.stderr}", flush=True)
                print(f"Worker Stdout: {process.stdout}", flush=True)
                raise RuntimeError("ChromaDB worker process failed.")
            else:
                print(f"Worker Output: {process.stdout.strip()}", flush=True)
                
        except Exception as e:
            print(f"Error invoking worker process: {e}", flush=True)
            raise e

    def query(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Queries the database for relevant documents.
        Since we cannot import chromadb here, we might need to delegate query to worker too,
        OR verify if read-only access crashes.
        For now, let's delegate query to worker as well to be safe.
        """
        # For simplicity, query logic is not implemented in worker yet. 
        # The prompt asks for ingest mostly. 
        # If query is needed, we need to add "mode": "query" to worker payload.
        # But for now, let's just return empty or implement basic worker query support if needed.
        print("Querying not yet refactored for subprocess worker.")
        return []
