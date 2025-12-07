import glob
import os
import sys

# Add project root to path to find src
sys.path.append(os.getcwd())

from src.pdf_extractor import PDFExtractor
from src.text_splitter import TextSplitter

def main():
    # Use a specific file known to have splits (from previous output, 1.5.5346.pdf had splits in MADDE 3)
    file_path = os.path.join("ENERJI DATA", "1.5.5346.pdf")
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return

    print(f"Analyzing {file_path} for split integrity...")
    
    extractor = PDFExtractor(file_path)
    text = extractor.extract_text()
    
    splitter = TextSplitter()
    chunks = splitter.split_text(text, {"source_file": "1.5.5346.pdf"})

    # Group chunks by article to find split ones
    article_chunks = {}
    for chunk in chunks:
        art_num = chunk['metadata']['article_number']
        if art_num not in article_chunks:
            article_chunks[art_num] = []
        article_chunks[art_num].append(chunk)

    split_found = False
    print("\n" + "="*80)
    print("CHECKING FOR MID-SENTENCE CUTS")
    print("="*80)

    for art_num, chunk_list in article_chunks.items():
        if len(chunk_list) > 1:
            split_found = True
            print(f"\nArticle: {art_num} has {len(chunk_list)} chunks.")
            
            for i in range(len(chunk_list) - 1):
                current_chunk = chunk_list[i]['text']
                next_chunk = chunk_list[i+1]['text']
                
                # Get the transition point
                # Since we have overlap, we need to be careful what we show.
                # But the user asked if they are cut in the middle.
                # The splitter uses overlap (stride = 80% of max_tokens).
                # So the end of chunk N will be repeated at start of chunk N+1.
                # However, the *end* of chunk N is still an arbitrary token point.
                
                print(f"\n--- Split between Chunk {i} and Chunk {i+1} ---")
                print(f"End of Chunk {i} (last 80 chars):")
                print(f"'{current_chunk[-80:]}'")
                print("-" * 20)
                print(f"Start of Chunk {i+1} (first 80 chars):")
                print(f"'{next_chunk[:80]}'")
                
                # Check if the end looks like a sentence ending
                last_char = current_chunk.strip()[-1]
                if last_char not in ['.', ':', '!', '?']:
                     print("\n>>> WARNING: Chunk does NOT end with punctuation. Likely mid-sentence cut.")
                else:
                     print("\n>>> INFO: Chunk ends with punctuation.")

    if not split_found:
        print("No multi-chunk articles found in this file to test.")

if __name__ == "__main__":
    main()
