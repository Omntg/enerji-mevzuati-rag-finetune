import glob
import os
import sys

# Fix for potential OpenMP conflict on Windows causing silent crash
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add project root to path
sys.path.append(os.getcwd())

from src.pdf_extractor import PDFExtractor
from src.text_splitter import TextSplitter
# Import RAGPipeline last, which imports chromadb.
# Trying to load torch (in TextSplitter) BEFORE chromadb to fix DLL crash.
from src.rag_pipeline import RAGPipeline

def main():
    data_dir = "ENERJI DATA"
    if not os.path.exists(data_dir):
        print(f"Directory {data_dir} not found.")
        return

    print("Initializing RAG Pipeline (loading models and DB)...")
    pipeline = RAGPipeline(persist_directory="chroma_db")
    splitter = TextSplitter()
    
    files = glob.glob(os.path.join(data_dir, "*.pdf"))
    # TEST MODU KAPALI: Tüm dosyaları işle
    # test_file = os.path.join(data_dir, "1.5.6446.pdf")
    # if os.path.exists(test_file):
    #     files = [test_file]
    # else:
    #     print(f"Test file {test_file} not found.")
    #     files = []
    
    print(f"Found {len(files)} PDF files to ingest.")
    
    total_chunks = 0
    
    for file_path in files:
        file_name = os.path.basename(file_path)
        print(f"Processing {file_name}...", flush=True)
        
        try:
            # 1. Extract
            print("  Extracting text...", flush=True)
            extractor = PDFExtractor(file_path)
            text = extractor.extract_text()
            print("  Text extracted.", flush=True)
            
            # 2. Split
            print("  Splitting text...", flush=True)
            base_metadata = {
                "source_file": file_name,
                "document_title": file_name.replace(".pdf", "") 
            }
            chunks = splitter.split_text(text, base_metadata)
            print(f"  Split into {len(chunks)} chunks.", flush=True)
            
            if not chunks:
                print(f"  No chunks generated for {file_name}.", flush=True)
                continue
                
            # 3. Ingest
            print("  Adding to ChromaDB...", flush=True)
            pipeline.add_documents(chunks)
            total_chunks += len(chunks)
            print("  Done with this file.", flush=True)
            
        except Exception as e:
            print(f"  Error processing {file_name}: {e}", flush=True)
            import traceback
            traceback.print_exc()
            
    print("="*60)
    print(f"Ingestion Complete. Total Chunks Added: {total_chunks}")
    print("="*60)

if __name__ == "__main__":
    main()
