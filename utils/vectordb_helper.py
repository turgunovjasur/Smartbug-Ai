# utils/vectordb_helper.py
import chromadb
from chromadb.config import Settings
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import json

load_dotenv()


class VectorDBHelper:
    def __init__(self):
        db_path = os.getenv('VECTOR_DB_PATH', './data/vector_db')

        print(f"VectorDB ga ulanmoqda: {db_path}")

        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        self.collection = self.client.get_or_create_collection(
            name="sprint_issues",
            metadata={"description": "All sprint issues with embeddings"}
        )

        print(f"Collection: {self.collection.count()} ta issue mavjud")

    def add_issue(self, issue_key, embedding, text, metadata):
        """Bitta issue qo'shish (eski format - backward compatibility)"""
        self.collection.add(
            ids=[issue_key],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )

    def add_issues_batch(self, keys, embeddings, texts, metadatas):
        """Ko'p issuelarni qo'shish (eski format - backward compatibility)"""
        self.collection.add(
            ids=keys,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

    def add_issue_with_chunks(
            self,
            issue_key: str,
            weighted_embedding: List[float],
            full_text: str,
            metadata: Dict[str, Any],
            chunks_data: List[Dict[str, Any]]
    ):
        """
        Yangi format - issue'ni chunks bilan qo'shish

        Args:
            issue_key: Issue key (DEV-1234)
            weighted_embedding: Weighted average embedding
            full_text: Full text for backward compatibility
            metadata: Issue metadata
            chunks_data: List of chunks with embeddings
        """
        # Chunks'ni JSON string ga aylantirish (ChromaDB metadata'da saqlash uchun)
        # Faqat text va type'ni saqlaymiz (embedding'larni yo'q, chunki katta)
        chunks_metadata = []
        for chunk in chunks_data:
            chunks_metadata.append({
                'type': chunk.get('type', 'unknown'),
                'text': chunk.get('text', '')[:200],  # Preview only
                'weight': chunk.get('weight', 1.0)
            })

        # Metadata'ga chunks info qo'shish
        metadata_with_chunks = {
            **metadata,
            'has_chunks': 'yes',
            'chunks_count': len(chunks_data),
            'chunks_preview': json.dumps(chunks_metadata, ensure_ascii=False)
        }

        self.collection.add(
            ids=[issue_key],
            embeddings=[weighted_embedding],
            documents=[full_text],
            metadatas=[metadata_with_chunks]
        )

    def add_issues_batch_with_chunks(
            self,
            keys: List[str],
            weighted_embeddings: List[List[float]],
            full_texts: List[str],
            metadatas: List[Dict[str, Any]],
            all_chunks_data: List[List[Dict[str, Any]]]
    ):
        """
        Batch format - ko'p issue'larni chunks bilan qo'shish
        """
        metadatas_with_chunks = []

        for metadata, chunks_data in zip(metadatas, all_chunks_data):
            # Chunks'ni JSON string ga aylantirish
            chunks_metadata = []
            for chunk in chunks_data:
                chunks_metadata.append({
                    'type': chunk.get('type', 'unknown'),
                    'text': chunk.get('text', '')[:200],
                    'weight': chunk.get('weight', 1.0)
                })

            metadata_with_chunks = {
                **metadata,
                'has_chunks': 'yes',
                'chunks_count': len(chunks_data),
                'chunks_preview': json.dumps(chunks_metadata, ensure_ascii=False)
            }
            metadatas_with_chunks.append(metadata_with_chunks)

        self.collection.add(
            ids=keys,
            embeddings=weighted_embeddings,
            documents=full_texts,
            metadatas=metadatas_with_chunks
        )

    def search(self, query_embedding, n_results=10, filters=None):
        """O'xshash issuelarni qidirish"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filters
        )
        return results

    def search_with_chunks(
            self,
            query_embedding: List[float],
            n_results: int = 20,
            filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Qidiruv - chunks data bilan

        Returns formatted results with chunks metadata
        """
        # ChromaDB'dan qidirish
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filters,
            include=['documents', 'metadatas', 'distances', 'embeddings']
        )

        if not results['ids'] or not results['ids'][0]:
            return []

        # Formatted results
        formatted_results = []

        for i in range(len(results['ids'][0])):
            distance = results['distances'][0][i]
            similarity = 1 - distance

            metadata = results['metadatas'][0][i]

            # Chunks'ni parse qilish
            chunks_data = []
            if metadata.get('has_chunks') == 'yes':
                try:
                    chunks_preview = json.loads(metadata.get('chunks_preview', '[]'))
                    chunks_data = chunks_preview
                except:
                    pass

            formatted_results.append({
                'key': results['ids'][0][i],
                'text': results['documents'][0][i],
                'similarity': similarity,
                'distance': distance,
                'metadata': metadata,
                'chunks': chunks_data,
                'embedding': results['embeddings'][0][i] if results.get('embeddings') else None
            })

        return formatted_results

    def get_stats(self):
        """Statistika"""
        total = self.collection.count()

        # Chunks bilan va bo'lmagan issuelar
        try:
            with_chunks = self.collection.get(
                where={"has_chunks": "yes"},
                limit=1
            )
            chunks_count = len(with_chunks['ids']) if with_chunks['ids'] else 0
        except:
            chunks_count = 0

        return {
            'total_issues': total,
            'with_chunks': chunks_count
        }

    def rebuild_index(self):
        """
        Index'ni qayta qurishni boshlash

        DIQQAT: Bu barcha ma'lumotlarni o'chiradi!
        """
        try:
            self.client.delete_collection("sprint_issues")
            print("Eski collection o'chirildi")

            self.collection = self.client.create_collection(
                name="sprint_issues",
                metadata={"description": "All sprint issues with embeddings"}
            )
            print("Yangi collection yaratildi")

            return True
        except Exception as e:
            print(f"Rebuild error: {e}")
            return False