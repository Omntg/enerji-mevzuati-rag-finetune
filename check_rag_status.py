import os
import sys
sys.path.append(os.path.join(os.getcwd(), "src"))
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

def check_retrieval():
    print("🔍 RAG Bağlantı Testi Başlıyor...")
    
    persist_dir = os.path.join(os.getcwd(), "chroma_db")
    if not os.path.exists(persist_dir):
        print(f"❌ HATA: Veritabanı klasörü bulunamadı: {persist_dir}")
        return

    try:
        print("1. Embedding modeli yükleniyor...")
        embeddings = HuggingFaceEmbeddings(model_name="emrecan/bert-base-turkish-cased-mean-nli-stsb-tr")
        
        print("2. ChromaDB'ye bağlanılıyor...")
        vectorstore = Chroma(persist_directory=persist_dir, embedding_function=embeddings, collection_name="enerji_mevzuati")
        
        print("3. Örnek sorgu yapılıyor: 'Lisans başvurusu'")
        docs = vectorstore.similarity_search("Lisans başvurusu", k=2)
        
        if docs:
            for i, doc in enumerate(docs):
                print(f"\n✅ SONUÇ {i+1}: {doc.metadata.get('source_file')}")
                print("-" * 50)
                print(doc.page_content)
                print("-" * 50)
                print(f"📊 Metadata: {doc.metadata}")
        else:
            print("⚠️ UYARI: Veritabanı boş veya sonuç dönmedi.")
            
    except Exception as e:
        print(f"❌ KRİTİK HATA: {e}")

if __name__ == "__main__":
    check_retrieval()
