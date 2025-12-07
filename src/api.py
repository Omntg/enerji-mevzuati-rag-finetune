from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import json
import asyncio
from contextlib import asynccontextmanager

# Modülleri import edebilmek için yol ayarı
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.chat_engine import get_rag_chain_streaming, load_retriever, format_docs

# --- Veri Modelleri ---
class QueryRequest(BaseModel):
    query: str

class SourceDoc(BaseModel):
    source_file: str
    article_number: str
    section: str
    content: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceDoc]

# --- Global Değişkenler ---
retriever = None

# --- Uygulama Başlangıcı (Lifespan) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global retriever
    print("[INFO] API Baslatiliyor...")
    # Retriever'ı bir kere yükle
    retriever = load_retriever()
    print("[OK] Retriever Hazir!")
    yield
    print("[INFO] API Kapatiliyor...")

app = FastAPI(title="Enerji Mevzuatı Chatbot API", lifespan=lifespan)

# --- CORS Ayarları ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Geliştirme ortamı için tüm kaynaklara izin ver
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpointler ---
@app.get("/")
async def root():
    return {"status": "active", "message": "Enerji Chatbot API Hazır"}

@app.post("/chat/stream")
async def chat_stream(request: QueryRequest):
    print(f"\n[SORU] {request.query}")
    
    async def event_generator():
        # 1. Kaynakları Bul
        print("[RETRIEVAL] Veritabanı sorgulanıyor...")
        
        # Skorları görmek için retriever'ın altındaki vectorstore'a erişiyoruz
        if hasattr(retriever, "vectorstore"):
            # k değerini retriever ayarlarından al, yoksa varsayılan 4
            k = retriever.search_kwargs.get("k", 4)
            # (Document, score) tupple'ları döner. Chroma için score genellikle mesafedir (düşük = daha iyi)
            docs_with_scores = retriever.vectorstore.similarity_search_with_score(request.query, k=k)
            docs = [doc for doc, _ in docs_with_scores]
            scores = [score for _, score in docs_with_scores]
        else:
            docs = retriever.invoke(request.query)
            scores = [None] * len(docs)
        
        # Loglama
        print("-" * 50)
        for i, (doc, score) in enumerate(zip(docs, scores)):
            source = doc.metadata.get('source_file', '?')
            article = doc.metadata.get('article_number', '?')
            score_txt = f" (Skor/Mesafe: {score:.4f})" if score is not None else ""
            print(f"[BELGE {i+1}] {source} ({article}){score_txt}")
            print(f"   Icerik: {doc.page_content}")
        print("-" * 50)
        
        # Kaynakları JSON formatına çevir
        formatted_sources = []
        seen_docs = set()
        for doc in docs:
            src_file = doc.metadata.get('source_file', 'Bilinmiyor')
            article = doc.metadata.get('article_number', 'Belirsiz')
            section = doc.metadata.get('section', '-')
            unique_key = f"{src_file}_{article}"
            if unique_key not in seen_docs:
                formatted_sources.append({
                    "source_file": src_file,
                    "article_number": str(article),
                    "section": str(section),
                    "content": doc.page_content
                })
                seen_docs.add(unique_key)
        
        # 2. Generator'ı Başlat
        # Not: get_rag_chain_streaming senkron çalışıyor (Thread içinde), 
        # burada async wrapper ile tokenları alacağız.
        context_text = format_docs(docs)
        stream_gen = get_rag_chain_streaming(request.query, context_text)
        
        for token in stream_gen:
            # Token verisi
            data = json.dumps({"token": token})
            yield f"data: {data}\n\n"
            # Küçük bir gecikme ekleyerek UI akışını pürüzsüzleştirebiliriz (opsiyonel)
            await asyncio.sleep(0.01)
            
        # 3. Bitişte Kaynakları Gönder
        sources_data = json.dumps({"sources": formatted_sources})
        yield f"data: {sources_data}\n\n"
        yield "event: end\ndata: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api:app", host="127.0.0.1", port=8000, reload=True)

