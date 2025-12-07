import re
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer

class TextSplitter:
    def __init__(self, model_name: str = "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr", max_tokens: int = 500, overlap: int = 50):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.max_tokens = max_tokens
        self.overlap = overlap
        
        # LangChain'in splitter'ını BERT tokenizer uzunluğuna göre yapılandırıyoruz
        self.splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            tokenizer=self.tokenizer,
            chunk_size=self.max_tokens,
            chunk_overlap=self.overlap,
            separators=["\n\n", "\n", ". ", "? ", "! ", ";", ",", " ", ""], # Öncelik sırası
            strip_whitespace=True
        )

    def split_text(self, text: str, source_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Splits text into chunks based on Articles (Madde) and token limits using LangChain.
        """
        # Normalize newlines
        text = text.replace('\r\n', '\n')
        
        lines = text.split('\n')
        
        chunks = []
        current_section = "Genel"
        current_article = "Giriş"
        current_buffer = []
        
        # Regex for "MADDE 1", "MADDE 1.", "Madde 1", "MADDE 6/A", "EK MADDE 1", "GEÇİCİ MADDE 3"
        article_pattern = re.compile(r"^\s*((?:EK\s+|GEÇİCİ\s+)?MADDE\s+\d+[A-Z\d\/]*)\.?\s*(.*)", re.IGNORECASE)
        # Regex for sections like "BİRİNCİ BÖLÜM", "İKİNCİ KISIM"
        section_pattern = re.compile(r"^\s*([A-ZİĞÜŞÖÇ\s]+(BÖLÜM|KISIM))\s*$", re.IGNORECASE)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for Section Header
            section_match = section_pattern.match(line)
            if section_match:
                current_section = section_match.group(1).strip()
                continue

            # Check for Article Header
            article_match = article_pattern.match(line)
            if article_match:
                # Flush previous
                if current_buffer:
                    self._flush_buffer(chunks, current_buffer, current_article, current_section, source_metadata)
                    current_buffer = []
                
                # Start new
                current_article = article_match.group(1).upper()
                rest_of_line = article_match.group(2).strip()
                if rest_of_line:
                    current_buffer.append(rest_of_line)
            else:
                current_buffer.append(line)
        
        # Flush remaining
        if current_buffer:
            self._flush_buffer(chunks, current_buffer, current_article, current_section, source_metadata)
            
        return chunks

    def _flush_buffer(self, chunks: List[Dict[str, Any]], buffer: List[str], article: str, section: str, metadata: Dict[str, Any]):
        full_text = " ".join(buffer)
        
        # LangChain ile akıllı bölme
        text_chunks = self.splitter.split_text(full_text)
        
        for i, chunk_text in enumerate(text_chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "article_number": article,
                "section": section,
                "chunk_index": i
            })
            
            # Bağlamı güçlendirmek için madde başlığını metne ekliyoruz
            final_text = f"{article}: {chunk_text}"
            
            chunks.append({
                "text": final_text,
                "metadata": chunk_metadata
            })

