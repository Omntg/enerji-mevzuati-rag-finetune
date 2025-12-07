from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import sys
import os

sys.path.append(os.path.join(os.getcwd(), "src"))

def check_article_14():
    print("🔍 Veritabanı kontrol ediliyor...")
    embedding_function = HuggingFaceEmbeddings(model_name="emrecan/bert-base-turkish-cased-mean-nli-stsb-tr")
    
    db = Chroma(
        persist_directory="chroma_db",
        embedding_function=embedding_function,
        collection_name="enerji_mevzuati"
    )
    
    # Metadata filtresi ile arama yapalım
    # Not: Metadata'da 'article_number' alanını 'MADDE 14' olarak kaydetmiştik.
    results = db.get(where={"article_number": "MADDE 14"})
    
    if results['ids']:
        print(f"✅ MADDE 14 bulundu! Toplam {len(results['ids'])} parça.")
        for i, text in enumerate(results['documents']):
            print(f"\n--- Parça {i+1} ---")
            print(text[:300] + "...") # İlk 300 karakteri göster
            print(f"Kaynak: {results['metadatas'][i]['source_file']}")
    else:
        print("❌ MADDE 14 veritabanında bulunamadı!")

    # Alternatif olarak "Lisanssız yürütülebilir" metnini içerenleri arayalım
    print("\n🔍 'Lisanssız yürütülebilir' içeren belgeler aranıyor...")
    results_text = db.get(where={"source_file": "1.5.6446.pdf"}) # Sadece bu dosyadakileri getir
    
    found_count = 0
    for doc in results_text['documents']:
        if "Lisanssız yürütülebilir" in doc or "muaf faaliyetler" in doc:
            print(f"\n--- Metin Eşleşmesi Bulundu ---")
            print(doc[:300] + "...")
            found_count += 1
            
    if found_count == 0:
        print("❌ Metin içinde de bulunamadı.")

if __name__ == "__main__":
    check_article_14()
