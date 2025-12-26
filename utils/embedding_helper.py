# utils/embedding_helper.py
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import numpy as np

load_dotenv()


class EmbeddingHelper:
    def __init__(self):
        model_name = os.getenv('EMBEDDING_MODEL', 'intfloat/multilingual-e5-large')
        models_dir = os.getenv('MODELS_DIR', './models')

        # Agar relative path bo'lsa, root directory ga nisbatan hisoblash
        if not os.path.isabs(models_dir):
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            models_dir = os.path.join(root_dir, models_dir)

        print(f"Embedding model yuklanmoqda...")
        print(f"Path: {models_dir}")

        self.model = SentenceTransformer(model_name, cache_folder=models_dir)
        print("Model tayyor!")

    def encode_text(self, text):
        """Matnni vektorga aylantirish"""
        prefixed_text = f"passage: {text}"
        return self.model.encode(prefixed_text).tolist()

    def encode_query(self, query):
        """Query ni vektorga aylantirish (qidiruv uchun)"""
        prefixed_query = f"query: {query}"
        return self.model.encode(prefixed_query).tolist()

    def encode_batch(self, texts, show_progress=True):
        """Ko'p matnni bir vaqtda encode qilish"""
        prefixed_texts = [f"passage: {text}" for text in texts]
        return self.model.encode(
            prefixed_texts,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        ).tolist()

    def encode_chunks(self, chunks: List[Dict[str, str]], show_progress=True) -> List[List[float]]:
        """
        Chunk'larni encode qilish

        Args:
            chunks: List of chunks with 'text' and 'weight' keys
            show_progress: Progress bar ko'rsatish

        Returns:
            List of embeddings (one per chunk)
        """
        if not chunks:
            return []

        # Har bir chunk'ning text'ini olish
        chunk_texts = [chunk.get('text', '') for chunk in chunks]

        # Batch encode
        embeddings = self.encode_batch(chunk_texts, show_progress=show_progress)

        return embeddings

    def encode_chunks_weighted(
            self,
            chunks: List[Dict[str, str]],
            show_progress=True
    ) -> Dict[str, Any]:
        """
        Chunk'larni encode qilish va weighted average hisoblash

        Returns:
            {
                'chunk_embeddings': List of individual embeddings,
                'weighted_average': Single weighted average embedding,
                'chunks_metadata': Original chunks with embeddings
            }
        """
        if not chunks:
            return {
                'chunk_embeddings': [],
                'weighted_average': [],
                'chunks_metadata': []
            }

        # Har bir chunk'ni encode qilish
        chunk_embeddings = self.encode_chunks(chunks, show_progress=show_progress)

        # Weighted average hisoblash
        weights = [chunk.get('weight', 1.0) for chunk in chunks]
        total_weight = sum(weights)

        if total_weight > 0 and chunk_embeddings:
            weighted_embeddings = [
                np.array(emb) * (weight / total_weight)
                for emb, weight in zip(chunk_embeddings, weights)
            ]
            weighted_average = np.sum(weighted_embeddings, axis=0).tolist()
        else:
            weighted_average = []

        # Metadata
        chunks_with_embeddings = []
        for chunk, embedding in zip(chunks, chunk_embeddings):
            chunks_with_embeddings.append({
                **chunk,
                'embedding': embedding
            })

        return {
            'chunk_embeddings': chunk_embeddings,
            'weighted_average': weighted_average,
            'chunks_metadata': chunks_with_embeddings
        }