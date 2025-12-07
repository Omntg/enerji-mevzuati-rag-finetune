import sys
import os

# src klasörünün Python tarafından görülebilmesi için
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.chat_engine import get_rag_chain

def main():
    # Eğer komut satırından soru geldiyse tek seferlik çalış
    if len(sys.argv) > 1:
        query = sys.argv[1]
        print(f"🚀 Tek seferlik soru modu: '{query}'")
        chain = get_rag_chain()
        print("🤖 Asistan: (Düşünüyor...)")
        res = chain.invoke({"query": query})
        print(f"\n{res['result'].strip()}")
        return

    print("🚀 Sistem Başlatılıyor... (Model ve Veritabanı yüklenirken bekleyiniz)")
    try:
        chain = get_rag_chain()
        print("\n✅ SİSTEM HAZIR! Enerji Mevzuatı hakkında sorularınızı sorabilirsiniz.")
        print("Çıkmak için 'q', 'exit' veya 'çıkış' yazabilirsiniz.\n")
        
        while True:
            try:
                query = input("ben: ")
                if query.lower() in ['q', 'exit', 'çıkış', 'quit']:
                    print("Görüşmek üzere! 👋")
                    break
                
                if not query.strip():
                    continue

                print("🤖 Asistan: (Düşünüyor...)")
                res = chain.invoke({"query": query})
                
                answer = res['result']
                sources = res['source_documents']

                # Temiz çıktı formatı
                print(f"\n{answer.strip()}")
                
                if sources:
                    print("\n--------------------------------------------------")
                    print("📚 KULLANILAN KAYNAKLAR:")
                    unique_sources = set()
                    for doc in sources:
                        src_file = doc.metadata.get('source_file', 'Bilinmiyor')
                        article = doc.metadata.get('article_number', 'Belirsiz')
                        section = doc.metadata.get('section', '-')
                        
                        # Aynı maddeyi tekrar tekrar yazdırmamak için kontrol
                        source_id = f"{src_file} - Madde {article}"
                        if source_id not in unique_sources:
                            print(f"• {source_id} (Bölüm: {section})")
                            unique_sources.add(source_id)
                    print("--------------------------------------------------\n")
                else:
                    print("\n(Kaynak belge bulunamadı)\n")

            except KeyboardInterrupt:
                print("\nİşlem iptal edildi.")
                break
            except Exception as e:
                print(f"❌ Bir hata oluştu: {e}")

    except Exception as e:
        print(f"❌ Başlatma Hatası: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
