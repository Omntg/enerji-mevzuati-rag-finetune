import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from peft import PeftModel
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from transformers import TextIteratorStreamer
from threading import Thread

# --- Yapılandırma ---
CURRENT_DIR = os.getcwd()
PERSIST_DIRECTORY = os.path.join(CURRENT_DIR, "chroma_db")
EMBEDDING_MODEL_NAME = "emrecan/bert-base-turkish-cased-mean-nli-stsb-tr"
# Adapter config'den aldığımız temel model
BASE_MODEL_NAME = "google/gemma-3-4b-it"
ADAPTER_PATH = os.path.join(CURRENT_DIR, "fine_tuned_models", "gemma3-4b-lora-final")

# Modeli global olarak yükleyelim ki her istekte tekrar yüklenmesin (API için)
_global_model = None
_global_tokenizer = None

def load_retriever(k: int = 3):
    """
    ChromaDB vektör veritabanını yükler ve bir retriever döndürür.
    k: Getirilecek en alakalı belge sayısı.
    """
    print(f"[INFO] Veritabanina baglaniliyor: {PERSIST_DIRECTORY}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    
    vectorstore = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embeddings,
        collection_name="enerji_mevzuati"
    )
    
    return vectorstore.as_retriever(search_kwargs={"k": k})

def load_llm_streaming():
    """
    Streaming destekli model ve tokenizer'ı yükler.
    Geriye (model, tokenizer) döner.
    """
    global _global_model, _global_tokenizer
    
    if _global_model is not None:
        return _global_model, _global_tokenizer

    print(f"[INFO] Tokenizer yukleniyor: {ADAPTER_PATH}")
    try:
        tokenizer = AutoTokenizer.from_pretrained(ADAPTER_PATH)
    except:
        tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_NAME)

    print(f"[INFO] Temel Model Yukleniyor: {BASE_MODEL_NAME}")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_NAME,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        trust_remote_code=True
    )
    
    print(f"[INFO] LoRA Adapter Entegre Ediliyor: {ADAPTER_PATH}")
    model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)
    model = model.merge_and_unload()
    
    _global_model = model
    _global_tokenizer = tokenizer
    
    return model, tokenizer

def format_docs(docs):
    # Belgeler arasına net bir ayraç koyarak modelin karışmamasını sağlayalım
    return "\n\n--- YENİ BELGE ---\n\n".join(doc.page_content for doc in docs)

def get_rag_chain_streaming(question: str, context: str):
    """
    Generator fonksiyonu: Verilen bağlam ve soruya göre cevabı parça parça üretir.
    """
    model, tokenizer = load_llm_streaming()
    
    # Not: Retrieval işlemi dışarıda (API katmanında) yapılıp buraya sadece metin (context) gelecek.
    
    # 2. Prompt Hazırla
    template = """<start_of_turn>user
Sen Türkiye Enerji Mevzuatı konusunda uzman, yardımsever bir asistansın. 
Aşağıda farklı kaynaklardan alınmış 'Mevzuat Bağlamı' parçaları verilmiştir.
Bu parçalardaki bilgileri BİRLEŞTİREREK ve SENTEZLEYEREK soruyu detaylıca cevapla.
Eğer bir cümle yarım kalmışsa (kesilmişse), o cümleyi ihmal et.
Sadece verilen bağlamdaki bilgileri kullan, dışarıdan bilgi ekleme.
Eğer cevap bağlamda hiç yoksa "Verilen mevzuat metinlerinde bu sorunun cevabı bulunmamaktadır." de.

Mevzuat Bağlamı:
{context}

Soru:
{question}<end_of_turn>
<start_of_turn>model
"""
    prompt_text = template.format(context=context, question=question)
    
    # --- DETAYLI LOGLAMA ---
    print("\n" + "="*50)
    print(f"[PROMPT] LLM'e Giden Metin ({len(prompt_text)} karakter):")
    print("-" * 20)
    print(prompt_text.replace(context, f"[...BAĞLAM ({len(context)} karakter)...]")) # Bağlamı kısaltarak göster
    print("="*50 + "\n")
    # -----------------------

    inputs = tokenizer(prompt_text, return_tensors="pt").to(model.device)
    
    # 3. Streamer Oluştur
    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    
    # 4. Üretimi Ayrı Thread'de Başlat
    generation_kwargs = dict(
        **inputs, 
        streamer=streamer, 
        max_new_tokens=1024,      # Daha uzun cevaplar için artırıldı
        temperature=0.3,          # Biraz daha akıcılık için artırıldı
        do_sample=True,
        top_p=0.95,
        repetition_penalty=1.05   # Çok katı olmaması için düşürüldü
    )
    
    thread = Thread(target=model.generate, kwargs=generation_kwargs)
    thread.start()
    
    # 5. Token'ları Yakala ve Gönder
    for new_text in streamer:
        yield new_text


if __name__ == "__main__":
    # Dosya doğrudan çalıştırılırsa test modu başlar
    print("--- Enerji Mevzuatı Chatbot (Test Modu) ---")
    chain = get_rag_chain()
    
    while True:
        try:
            query = input("\n❓ Soru (Çıkış için 'q'): ")
            if query.lower() == 'q':
                break
            
            print("⏳ Düşünüyor...")
            result = chain.invoke({"query": query})
            
            print("\n🤖 Cevap:")
            print(result['result'].strip())
            
            print("\n📚 Kaynaklar:")
            seen_sources = set()
            for doc in result['source_documents']:
                source = doc.metadata.get('source_file', 'Bilinmiyor')
                article = doc.metadata.get('article_number', 'Belirsiz')
                key = f"{source} - {article}"
                if key not in seen_sources:
                    print(f"- {key}")
                    seen_sources.add(key)
                    
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Hata oluştu: {e}")
