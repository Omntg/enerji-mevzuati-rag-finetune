# Proje Planı: Türkiye Enerji Mevzuatı RAG Chatbot

Bu belge, Türkiye enerji mevzuatı üzerine uzmanlaşmış, RAG (Retrieval-Augmented Generation) mimarisi kullanan bir chatbot geliştirme sürecini adım adım tanımlar.

## Faz 1: Veri Analizi ve Hazırlık (Tamamlandı/Devam Ediyor)
**Hedef:** `ENERJI DATA` klasöründeki PDF dosyalarının yapısal analizi ve RAG için uygun parçalama (chunking) stratejisinin belirlenmesi.

*   **Veri Kaynağı:** `ENERJI DATA/` dizinindeki PDF dosyaları (Kanunlar, Yönetmelikler).
*   **Belge Yapısı:** Belgeler hiyerarşik bir yapıdadır (Bölüm -> Madde -> Fıkra). Temel anlamsal bütünlük **Madde (Article)** seviyesindedir.
*   **Chunking Stratejisi:**
    1.  **Birincil Bölümleme:** Metinler **"MADDE X"** ibareleri referans alınarak maddelere bölünecektir.
    2.  **İkincil Bölümleme (Token Sınırı):** Kullanılacak embedding modeli (BERT) 512 token sınırına sahip olduğu için, uzun maddeler alt fıkralara ( (1), (2) vb.) veya 256-512 token'lık pencerelere (sliding window) bölünecektir.
    3.  **Metadata:** Her parça için zengin metadata çıkarılacaktır:
        *   `source_file`: Dosya adı (örn. 1.5.6446.pdf).
        *   `document_title`: Belge başlığı (örn. ELEKTRİK PİYASASI KANUNU).
        *   `article_number`: Madde numarası (örn. Madde 1).
        *   `section`: Varsa bölüm başlığı.

## Faz 2: RAG Pipeline Kurulumu (TAMAMLANDI)
**Durum:** Tamamlandı.
*   Windows `0xC0000005` hatası, ChromaDB işlemleri ayrı bir sürece (`chroma_worker.py`) taşınarak çözüldü.
*   ChromaDB sürümü stabilite için `0.4.24` olarak sabitlendi.
*   Tüm PDF verileri (819 chunk) başarıyla yüklendi.

## Faz 3: Retrieval (Erişim) Sistemi (TAMAMLANDI)
**Durum:** Tamamlandı.
*   **Kütüphane:** LangChain entegrasyonu yapıldı.
*   **Chunking İyileştirmesi:** Cümle bölünmelerini önlemek için `RecursiveCharacterTextSplitter` kullanıldı (500 token limit, 50 token overlap).
*   **Test:** `check_rag_status.py` ile veritabanı sorguları doğrulandı.

## Faz 4: Generation (Üretim) - Chatbot Entegrasyonu (TAMAMLANDI)
**Durum:** Tamamlandı.
*   **Motor:** `src/chat_engine.py` oluşturuldu. Gemma-3-4b-it + LoRA adaptörü LangChain zincirine bağlandı.
*   **Arayüz:** `run_bot.py` CLI uygulaması hazırlandı.
*   **Prompt:** "Enerji Mevzuatı Uzmanı" sistem promptu ve RAG şablonu tanımlandı.

## Faz 5: Frontend Geliştirme (Sıradaki Adım)
**Hedef:** Kullanıcı dostu bir arayüz.

1.  **Teknoloji:** Başlangıçta prototip için Python tabanlı **Gradio** veya **Streamlit**. Nihai sürüm için **React** (kullanıcı isteğine göre).
2.  **Özellikler:**
    *   Sohbet arayüzü.
    *   Kullanılan kaynakları (hangi kanun, hangi madde) gösterme özelliği.
**Hedef:** Kullanıcı dostu bir arayüz.

1.  **Teknoloji:** Başlangıçta prototip için Python tabanlı **Gradio** veya **Streamlit**. Nihai sürüm için **React** (kullanıcı isteğine göre).
2.  **Özellikler:**
    *   Sohbet arayüzü.
    *   Kullanılan kaynakları (hangi kanun, hangi madde) gösterme özelliği.

---

**Sonraki Adım:** `ENERJI DATA` klasöründeki PDF'leri okuyup, maddelere ayırarak ChromaDB'ye kaydeden Python scriptini (`ingest_data.py`) oluşturmak.
