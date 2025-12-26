# scripts/view_database.py
import json
from dotenv import load_dotenv

from utils.vectordb_helper import VectorDBHelper

load_dotenv()

print("=" * 70)
print("💾 VECTORDB MA'LUMOTLARINI KO'RISH")
print("=" * 70)
print()

# VectorDB ga ulanish
vectordb_helper = VectorDBHelper()

# Statistika
stats = vectordb_helper.get_stats()
print(f"📊 Jami issue: {stats['total_issues']} ta")
print()

# Barcha ma'lumotlarni olish
print("📋 MA'LUMOTLARNI YUKLAB OLISH...")
all_data = vectordb_helper.collection.get(
    include=['documents', 'metadatas', 'embeddings']
)

print(f"✅ Yuklandi: {len(all_data['ids'])} ta issue")
print()

# Sprint bo'yicha statistika
sprint_stats = {}
for metadata in all_data['metadatas']:
    sprint_id = metadata.get('sprint_id', 'Unknown')
    sprint_stats[sprint_id] = sprint_stats.get(sprint_id, 0) + 1

print("=" * 70)
print("📈 SPRINT BO'YICHA STATISTIKA")
print("=" * 70)
for sprint_id, count in sorted(sprint_stats.items()):
    print(f"   Sprint {sprint_id}: {count} ta issue")
print()

# Type bo'yicha statistika
type_stats = {}
for metadata in all_data['metadatas']:
    issue_type = metadata.get('type', 'Unknown')
    type_stats[issue_type] = type_stats.get(issue_type, 0) + 1

print("=" * 70)
print("📊 TYPE BO'YICHA STATISTIKA")
print("=" * 70)
for issue_type, count in sorted(type_stats.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / len(all_data['ids'])) * 100
    print(f"   {issue_type:20s}: {count:3d} ta ({percentage:.1f}%)")
print()

# Status bo'yicha statistika
status_stats = {}
for metadata in all_data['metadatas']:
    status = metadata.get('status', 'Unknown')
    status_stats[status] = status_stats.get(status, 0) + 1

print("=" * 70)
print("🎯 STATUS BO'YICHA STATISTIKA")
print("=" * 70)
for status, count in sorted(status_stats.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / len(all_data['ids'])) * 100
    print(f"   {status:15s}: {count:3d} ta ({percentage:.1f}%)")
print()

# Birinchi 5 ta issue ni batafsil ko'rsatish
print("=" * 70)
print("📝 BIRINCHI 5 TA ISSUE (BATAFSIL)")
print("=" * 70)
print()

for i in range(min(5, len(all_data['ids']))):
    print(f"{'=' * 70}")
    print(f"Issue #{i + 1}")
    print(f"{'=' * 70}")
    print(f"🔑 Key: {all_data['ids'][i]}")
    print(f"📄 Document:")
    print(f"{all_data['documents'][i]}")
    print()
    print(f"📊 Metadata:")
    print(json.dumps(all_data['metadatas'][i], indent=2, ensure_ascii=False))
    print()
    print(f"🧮 Embedding: [{len(all_data['embeddings'][i])} dimensional vector]")
    print(f"   First 5 values: {all_data['embeddings'][i][:5]}")
    print()

# Muayyan issue ni qidirish
print("=" * 70)
print("🔍 MUAYYAN ISSUE NI QIDIRISH")
print("=" * 70)
issue_key = input("\n🔑 Issue key kiriting (masalan, DEV-6267): ").strip()

if issue_key:
    try:
        result = vectordb_helper.collection.get(
            ids=[issue_key],
            include=['documents', 'metadatas', 'embeddings']
        )

        if result['ids']:
            print()
            print(f"✅ Topildi: {issue_key}")
            print()
            print(f"📄 Document:")
            print(result['documents'][0])
            print()
            print(f"📊 Metadata:")
            print(json.dumps(result['metadatas'][0], indent=2, ensure_ascii=False))
            print()
            print(f"🧮 Embedding: [{len(result['embeddings'][0])} dimensional vector]")
            print(f"   First 10 values: {result['embeddings'][0][:10]}")
        else:
            print(f"\n❌ {issue_key} topilmadi")
    except Exception as e:
        print(f"\n❌ Xatolik: {e}")

print()
print("=" * 70)
print("✅ TAYYOR!")
print("=" * 70)