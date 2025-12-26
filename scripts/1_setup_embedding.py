# scripts/1_setup_embedding.py
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("🤖 EMBEDDING MODEL NI YUKLAB OLISH")
print("=" * 70)
print()

model_name = os.getenv('EMBEDDING_MODEL', 'intfloat/multilingual-e5-large')
models_dir = os.getenv('MODELS_DIR', './models')

print(f"📦 Model: {model_name}")
print(f"📁 Saqlash joyi: {models_dir}")
print()
print("⏳ Yuklanmoqda (birinchi marta 2-3 GB)...")
print()

# Model ni yuklab olish
model = SentenceTransformer(model_name, cache_folder=models_dir)

print()
print("✅ Model muvaffaqiyatli yuklandi!")
print()

# Test qilish
test_texts = [
    "Login sahifasida xatolik",
    "Ошибка на странице входа",
    "Error on login page"
]

print("🧪 TEST:")
for text in test_texts:
    embedding = model.encode(text)
    print(f"   ✓ '{text}' → {len(embedding)} dimensional vector")

print()
print("=" * 70)
print("🎉 TAYYOR!")
print("=" * 70)