# 🇹🇷 Türkiye Enerji Mevzuatı RAG Chatbot

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![React](https://img.shields.io/badge/react-18%2B-cyan)
![Gemma](https://img.shields.io/badge/Model-Gemma%203%204B-orange)

Bu proje, **Türkiye Enerji Mevzuatı** (Kanunlar, Yönetmelikler, Tebliğler vb.) üzerine uzmanlaşmış, **RAG (Retrieval-Augmented Generation)** mimarisi kullanan yapay zeka destekli bir asistan uygulamasıdır. 

Kullanıcıların mevzuatla ilgili sorularını yanıtlar, yanıtlarını resmi belgelere dayandırır ve kaynak gösterir.

---

## 🚀 Özellikler

*   **RAG Mimarisi:** Sorulara ezbere değil, güncel PDF belgelerinden (ChromaDB vektör veritabanı) arama yaparak cevap verir.
*   **Fine-Tuned Model:** Google **Gemma 3 4B** modeli, enerji mevzuatı soru-cevap çiftleriyle özel olarak eğitilmiştir (LoRA).
*   **Streaming Yanıt:** ChatGPT benzeri, kelime kelime akan hızlı yanıt sistemi (SSE).
*   **Modern Arayüz:** React, Tailwind CSS ve Framer Motion ile geliştirilmiş, şık ve kullanıcı dostu arayüz.
*   **Kaynak Gösterimi:** Her cevabın altında, bilginin hangi kanunun kaçıncı maddesinden alındığını gösteren interaktif etiketler.
*   **Akıllı Chunking:** PDF belgeleri madde madde (Article-based) bölünerek anlam bütünlüğü korunmuştur.

---

## 🛠️ Teknoloji Yığını

### Backend (Python)
*   **FastAPI:** Yüksek performanslı asenkron API sunucusu.
*   **LangChain:** RAG zinciri ve belge işleme.
*   **ChromaDB:** Vektör veritabanı (Persistent mode).
*   **Hugging Face Transformers & PEFT:** Model yükleme ve LoRA adaptör entegrasyonu.
*   **PyMuPDF (fitz):** PDF metin çıkarma.

### Frontend (React)
*   **Vite:** Hızlı geliştirme ortamı.
*   **Tailwind CSS v4:** Modern stil işlemleri.
*   **Framer Motion:** Akıcı animasyonlar.
*   **Lucide React:** İkon seti.

### Model & Eğitim
*   **Base Model:** `google/gemma-3-4b-it`
*   **Embedding Model:** `emrecan/bert-base-turkish-cased-mean-nli-stsb-tr`
*   **Eğitim Platformu:** Google Colab (L4 GPU)

---

## 📦 Kurulum

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyin.

### Gereksinimler
*   Python 3.10 veya üzeri
*   Node.js 18 veya üzeri
*   NVIDIA GPU (Önerilen: En az 6GB VRAM) - *CPU ile çalışabilir ama yavaştır.*

### 1. Repoyu Klonlayın
```bash
git clone https://github.com/Omntg/enerji-mevzuati-rag-finetune.git
cd enerji-mevzuati-rag-finetune
```

### 2. Backend Kurulumu
```bash
# Sanal ortam oluşturun
python -m venv .venv

# Sanal ortamı aktif edin (Windows)
.venv\Scripts\activate
# (Linux/Mac) source .venv/bin/activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt
# (Not: requirements.txt yoksa manuel kurulum gerekebilir, projede torch, fastapi, langchain vb. yüklü olmalı)
```

### 3. Veri Tabanını Oluşturma (Ingestion)
PDF dosyalarınızı `ENERJI DATA` klasörüne atın ve scripti çalıştırın:
```bash
python ingest_data.py
```
*Bu işlem PDF'leri okur, parçalar ve `chroma_db` klasörüne kaydeder.*

### 4. Uygulamayı Başlatma

**Terminal 1 (Backend):**
```bash
uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm install
npm run dev
```

Tarayıcıda `http://localhost:5173` adresine giderek kullanmaya başlayın.

---

## 🧠 Model Eğitimi (Fine-Tuning)

Bu projede kullanılan model, ham Gemma 3 modeli değildir. Enerji mevzuatı üzerine özel olarak **SFT (Supervised Fine-Tuning)** tekniği ile eğitilmiştir.

*   **Eğitim Kodları:** `training/finetune_gemma_colab.ipynb` dosyasında Google Colab üzerinde çalıştırılabilir not defterini bulabilirsiniz.
*   **Veri Seti:** Mevzuat maddelerinden üretilen Soru-Cevap çiftleri (JSONL formatında).
*   **Yöntem:** QLoRA (4-bit quantization + LoRA) kullanılarak L4 GPU üzerinde eğitilmiştir.

---

## 📂 Proje Yapısı

```
enerji-mevzuati-chatbot/
├── ENERJI DATA/          # Ham PDF dosyaları
├── chroma_db/            # Vektör veritabanı (Embeddings)
├── fine_tuned_models/    # Eğitilmiş LoRA adaptör dosyaları
├── frontend/             # React arayüz kodları
│   ├── src/
│   └── ...
├── src/                  # Backend kaynak kodları
│   ├── api.py            # FastAPI sunucusu
│   ├── chat_engine.py    # RAG ve LLM mantığı
│   ├── rag_pipeline.py   # Embedding ve Veritabanı işlemleri
│   ├── pdf_extractor.py  # PDF okuma modülü
│   └── text_splitter.py  # Metin parçalama mantığı
├── training/             # Eğitim not defterleri
│   └── finetune_gemma_colab.ipynb
├── ingest_data.py        # Veri yükleme scripti
└── run_bot.py            # Terminal tabanlı test aracı
```

---

## ⚠️ Yasal Uyarı

Bu yapay zeka asistanı bilgilendirme amaçlıdır. Ürettiği cevaplar %100 doğruluk garantisi taşımaz ve hukuki tavsiye yerine geçmez. Lütfen kritik kararlarınızda resmi mevzuat metinlerini ve hukuk danışmanlarını referans alınız.

---

## 🤝 Katkıda Bulunma

Pull request'ler kabul edilir. Büyük değişiklikler için önce tartışma (issue) açmanızı rica ederiz.

## 📄 Lisans

[MIT](LICENSE)
