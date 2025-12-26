# utils/chunking_helper.py - V2 (Smart Chunking with Multilingual Support)
from typing import List, Dict, Any
import re


class ChunkingHelper:
    """
    Smart Chunking - Multilingual Support

    Turli tillardagi matnlarni (O'zbek, Rus, Ingliz) semantic chunks'ga bo'lish.
    Har bir chunk type'ga weight beriladi va embedding quality oshadi.

    Features:
    - Root cause detection (multilingual)
    - Solution extraction (multilingual)
    - Intelligent paragraph splitting
    - Language detection
    - Weighted semantic chunks
    """

    def __init__(self, max_chunk_length=800):
        """
        Args:
            max_chunk_length: Har bir chunk maksimal uzunligi (character)
        """
        self.max_chunk_length = max_chunk_length

        # Chunk type weights - semantik muhimlikka qarab
        self.weights = {
            'summary': 3.5,  # Eng muhim - task nima haqida
            'description': 2.5,  # Batafsil - nima qilish kerak
            'root_cause': 3.0,  # Bug sababi - juda muhim!
            'solution': 3.0,  # Yechim - bug fix uchun zarur
            'comments': 2.0,  # Discussion - context
            'return_reasons': 2.5,  # QA feedback - bug pattern
            'status_history': 1.5,  # Lifecycle - timing info
            'technical': 2.0,  # Technical details
            'metadata': 1.0  # Context - type, priority, etc.
        }

    def create_chunks(self, issue_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Issue'ni smart semantic chunks'ga bo'lish

        Strategy:
        1. Summary - har doim birinchi chunk
        2. Description - agar uzun bo'lsa, intelligent chunking
        3. Comments - root cause va solution ni ajratish
        4. Return Reasons - bug pattern detection
        5. Status History - timeline info
        6. Technical metadata - context

        Returns:
            List of chunks: [{'text': str, 'type': str, 'weight': float, 'language': str}, ...]
        """
        chunks = []

        # 1. SUMMARY - har doim mavjud, eng muhim
        if issue_data.get('summary'):
            summary_text = self._clean_text(issue_data['summary'])
            chunks.append({
                'text': f"Summary: {summary_text}",
                'type': 'summary',
                'weight': self.weights['summary'],
                'language': self._detect_primary_language(summary_text)
            })

        # 2. DESCRIPTION - intelligent chunking
        if issue_data.get('description'):
            desc_chunks = self._chunk_description(issue_data['description'])
            chunks.extend(desc_chunks)

        # 3. COMMENTS - root cause va solution extraction
        if issue_data.get('comments'):
            comment_chunks = self._chunk_comments(issue_data['comments'])
            chunks.extend(comment_chunks)

        # 4. RETURN REASONS - bug pattern
        if issue_data.get('return_reasons'):
            return_chunks = self._chunk_return_reasons(issue_data['return_reasons'])
            chunks.extend(return_chunks)

        # 5. STATUS HISTORY - timeline
        if issue_data.get('status_history'):
            history_chunk = self._create_status_history_chunk(issue_data['status_history'])
            if history_chunk:
                chunks.append(history_chunk)

        # 6. TECHNICAL METADATA - context
        metadata_chunk = self._create_metadata_chunk(issue_data)
        if metadata_chunk:
            chunks.append(metadata_chunk)

        # Agar hech qanday chunk bo'lmasa, minimal chunk yaratish
        if not chunks:
            chunks.append({
                'text': f"Issue {issue_data.get('key', 'Unknown')}: No content available",
                'type': 'metadata',
                'weight': 0.5,
                'language': 'en'
            })

        return chunks

    def _chunk_description(self, description: str) -> List[Dict[str, Any]]:
        """
        Description ni intelligent chunks'ga bo'lish

        Strategiya:
        - Root cause keywords detection
        - Solution keywords detection
        - Technical details extraction
        - Paragraph-based chunking
        """
        chunks = []
        desc_text = self._clean_text(description)

        if not desc_text:
            return chunks

        # Uzunlik bo'yicha qarash
        if len(desc_text) <= self.max_chunk_length:
            # Qisqa description - bitta chunk
            chunks.append({
                'text': f"Description: {desc_text}",
                'type': 'description',
                'weight': self.weights['description'],
                'language': self._detect_primary_language(desc_text)
            })
        else:
            # Uzun description - semantic chunking

            # Root cause detection
            root_cause_text = self._extract_root_cause(desc_text)
            if root_cause_text:
                chunks.append({
                    'text': f"Root Cause: {root_cause_text}",
                    'type': 'root_cause',
                    'weight': self.weights['root_cause'],
                    'language': self._detect_primary_language(root_cause_text)
                })

            # Solution detection
            solution_text = self._extract_solution(desc_text)
            if solution_text:
                chunks.append({
                    'text': f"Solution: {solution_text}",
                    'type': 'solution',
                    'weight': self.weights['solution'],
                    'language': self._detect_primary_language(solution_text)
                })

            # Agar root cause yoki solution topilmasa, oddiy chunking
            if not root_cause_text and not solution_text:
                # Paragraflarni ajratish
                paragraphs = self._split_into_paragraphs(desc_text)

                for i, para in enumerate(paragraphs):
                    if len(para.strip()) > 20:  # Juda qisqa paragraflarni o'tkazib yuborish
                        chunk_text = para[:self.max_chunk_length]
                        chunks.append({
                            'text': f"Description (part {i + 1}): {chunk_text}",
                            'type': 'description',
                            'weight': self.weights['description'] * (1.0 - i * 0.1),  # Birinchi qismlar muhimroq
                            'language': self._detect_primary_language(chunk_text)
                        })

        return chunks

    def _chunk_comments(self, comments: str) -> List[Dict[str, Any]]:
        """
        Comments ni chunking - root cause va solution detection
        """
        chunks = []
        comments_text = self._clean_text(comments)

        if not comments_text:
            return chunks

        # Root cause detection
        root_cause_text = self._extract_root_cause(comments_text)
        if root_cause_text:
            chunks.append({
                'text': f"Comment - Root Cause: {root_cause_text}",
                'type': 'root_cause',
                'weight': self.weights['root_cause'],
                'language': self._detect_primary_language(root_cause_text)
            })

        # Solution detection
        solution_text = self._extract_solution(comments_text)
        if solution_text:
            chunks.append({
                'text': f"Comment - Solution: {solution_text}",
                'type': 'solution',
                'weight': self.weights['solution'],
                'language': self._detect_primary_language(solution_text)
            })

        # Agar root cause/solution topilmasa, umumiy comment chunk
        if not root_cause_text and not solution_text:
            # Uzun commentlarni bo'lish
            if len(comments_text) > self.max_chunk_length:
                comments_text = comments_text[:self.max_chunk_length]

            chunks.append({
                'text': f"Comments: {comments_text}",
                'type': 'comments',
                'weight': self.weights['comments'],
                'language': self._detect_primary_language(comments_text)
            })

        return chunks

    def _chunk_return_reasons(self, return_reasons: str) -> List[Dict[str, Any]]:
        """
        Return reasons - QA feedback, bug pattern
        """
        chunks = []
        reasons_text = self._clean_text(return_reasons)

        if not reasons_text:
            return chunks

        # Har bir return'ni ajratish
        returns = reasons_text.split('\n')

        combined_reasons = []
        for ret in returns:
            ret = ret.strip()
            if ret and len(ret) > 10:
                combined_reasons.append(ret)

        if combined_reasons:
            # Barcha return reasons'ni bitta chunk'ga
            all_reasons = ' | '.join(combined_reasons)

            if len(all_reasons) > self.max_chunk_length:
                all_reasons = all_reasons[:self.max_chunk_length]

            chunks.append({
                'text': f"Return Reasons: {all_reasons}",
                'type': 'return_reasons',
                'weight': self.weights['return_reasons'],
                'language': self._detect_primary_language(all_reasons)
            })

        return chunks

    def _create_status_history_chunk(self, status_history: str) -> Dict[str, Any]:
        """
        Status history - lifecycle timeline
        """
        history_text = self._clean_text(status_history)

        if not history_text or len(history_text) < 10:
            return None

        # Faqat muhim transitionlarni olish
        important_transitions = []
        lines = history_text.split('\n')

        for line in lines[:10]:  # Birinchi 10 ta transition
            line = line.strip()
            if line and any(keyword in line.lower() for keyword in
                            ['testing', 'test', 'closed', 'done', 'return', 'clarification']):
                important_transitions.append(line)

        if important_transitions:
            history_summary = ' | '.join(important_transitions)

            if len(history_summary) > self.max_chunk_length:
                history_summary = history_summary[:self.max_chunk_length]

            return {
                'text': f"Status History: {history_summary}",
                'type': 'status_history',
                'weight': self.weights['status_history'],
                'language': 'mixed'
            }

        return None

    def _create_metadata_chunk(self, issue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Technical metadata - context chunk
        """
        metadata_parts = []

        # Type va Priority - eng muhim
        if issue_data.get('type'):
            metadata_parts.append(f"Type: {issue_data['type']}")

        if issue_data.get('priority'):
            metadata_parts.append(f"Priority: {issue_data['priority']}")

        # Components va Labels
        if issue_data.get('components'):
            components = str(issue_data['components'])[:100]
            metadata_parts.append(f"Components: {components}")

        if issue_data.get('labels'):
            labels = str(issue_data['labels'])[:100]
            metadata_parts.append(f"Labels: {labels}")

        # Assignee va Reporter
        if issue_data.get('assignee') and issue_data['assignee'] != 'Unassigned':
            metadata_parts.append(f"Assignee: {issue_data['assignee']}")

        if issue_data.get('reporter') and issue_data['reporter'] != 'Unknown':
            metadata_parts.append(f"Reporter: {issue_data['reporter']}")

        # Story Points va Return Count
        if issue_data.get('story_points'):
            metadata_parts.append(f"Story Points: {issue_data['story_points']}")

        if issue_data.get('return_count') and int(issue_data.get('return_count', 0)) > 0:
            metadata_parts.append(f"Return Count: {issue_data['return_count']}")

        # PR info
        if issue_data.get('pr_status'):
            metadata_parts.append(f"PR Status: {issue_data['pr_status']}")

        if metadata_parts:
            return {
                'text': ' | '.join(metadata_parts),
                'type': 'metadata',
                'weight': self.weights['metadata'],
                'language': 'mixed'
            }

        return None

    def _extract_root_cause(self, text: str) -> str:
        """
        Root cause keywords detection (multilingual)

        Detects root cause explanations in English, Russian, and Uzbek
        """
        text_lower = text.lower()

        # Multilingual keywords
        root_cause_keywords = [
            # English
            'root cause', 'caused by', 'reason:', 'because', 'due to',
            'error was', 'problem was', 'issue was', 'failure', 'bug was',
            # Russian
            'причина', 'из-за', 'корень проблемы', 'ошибка была',
            'проблема в том', 'дело в том', 'сбой', 'баг',
            # Uzbek
            'sabab', 'sababli', 'xatolik', 'muammo', 'noto\'g\'ri'
        ]

        # Keyword atrofidagi tekstni olish
        for keyword in root_cause_keywords:
            if keyword in text_lower:
                # Keyword indexini topish
                idx = text_lower.index(keyword)

                # Context olish: keyword oldidan 50 char, keyingi 400 char
                start = max(0, idx - 50)
                end = min(len(text), idx + 450)

                context = text[start:end].strip()

                # Agar matn yetarlicha uzun bo'lsa, qaytarish
                if len(context) > 100:
                    return context

        return ""

    def _extract_solution(self, text: str) -> str:
        """
        Solution keywords detection (multilingual)

        Detects solution descriptions in English, Russian, and Uzbek
        """
        text_lower = text.lower()

        # Multilingual keywords
        solution_keywords = [
            # English
            'solution:', 'fixed by', 'resolved by', 'fix:', 'to fix',
            'implemented', 'changed', 'updated', 'corrected', 'patched',
            # Russian
            'решение', 'исправлено', 'фикс', 'изменено',
            'реализовано', 'обновлено', 'поправлено', 'патч',
            # Uzbek
            'yechim', 'tuzatildi', 'o\'zgartirildi', 'yangilandi'
        ]

        for keyword in solution_keywords:
            if keyword in text_lower:
                idx = text_lower.index(keyword)
                start = max(0, idx - 50)
                end = min(len(text), idx + 450)

                context = text[start:end].strip()

                if len(context) > 100:
                    return context

        return ""

    def _clean_text(self, text: Any) -> str:
        """
        Textni tozalash - extra spaces, newlines, special chars
        """
        if not text:
            return ""

        text = str(text)

        # Multiple spaces -> single space
        text = re.sub(r'\s+', ' ', text)

        # Remove special chars (but keep basic punctuation)
        text = re.sub(r'[^\w\s\.\,\:\;\-\!\?\'\"\(\)А-Яа-яЁёЎўҚқҒғҲҳ]', ' ', text)

        # Trim
        text = text.strip()

        return text

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Textni paragrafga bo'lish

        Uses multiple strategies:
        - Double newlines
        - Sentence endings followed by space
        - Long sentences (>200 chars)
        """
        # Double newline bilan ajratish
        paragraphs = re.split(r'\n\n+', text)

        # Agar kamida 2 ta paragraph bo'lsa, qaytarish
        if len(paragraphs) >= 2:
            return [p.strip() for p in paragraphs if p.strip()]

        # Aks holda, sentence endings bilan ajratish
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Uzun sentencelarni birlashtirib paragraf qilish
        paragraphs = []
        current_para = ""

        for sentence in sentences:
            if len(current_para) + len(sentence) < self.max_chunk_length:
                current_para += " " + sentence
            else:
                if current_para:
                    paragraphs.append(current_para.strip())
                current_para = sentence

        if current_para:
            paragraphs.append(current_para.strip())

        return paragraphs

    def _detect_primary_language(self, text: str) -> str:
        """
        Primary language detection (simple heuristic)

        Returns: 'uz', 'ru', 'en', 'mixed'
        """
        if not text:
            return 'en'

        # Cyrillic detection
        cyrillic_count = len(re.findall(r'[А-Яа-яЁё]', text))
        latin_count = len(re.findall(r'[A-Za-z]', text))

        total_letters = cyrillic_count + latin_count

        if total_letters == 0:
            return 'mixed'

        cyrillic_ratio = cyrillic_count / total_letters

        if cyrillic_ratio > 0.7:
            # Mostly Cyrillic - Russian yoki Uzbek (Cyrillic)
            # Simple check: Russian specific letters
            if any(char in text for char in 'ыэъё'):
                return 'ru'
            return 'uz'
        elif cyrillic_ratio < 0.3:
            # Mostly Latin - English yoki Uzbek (Latin)
            # Uzbek specific: o', g', sh
            if "o'" in text or "g'" in text or 'sh' in text.lower():
                return 'uz'
            return 'en'
        else:
            return 'mixed'

    def create_full_text_for_backward_compatibility(self, issue_data: Dict[str, Any]) -> str:
        """
        Eski format uchun - barcha ma'lumotlarni bitta string ga birlashtirish

        Bu method faqat backward compatibility uchun. Yangi kod chunks'dan foydalanishi kerak.
        """
        parts = []

        if issue_data.get('summary'):
            parts.append(f"Summary: {issue_data['summary']}")

        if issue_data.get('description'):
            desc = str(issue_data['description'])
            # Juda uzun description'ni qisqartirish
            if len(desc) > 2000:
                desc = desc[:2000] + "..."
            parts.append(f"Description: {desc}")

        if issue_data.get('type'):
            parts.append(f"Type: {issue_data['type']}")

        if issue_data.get('status'):
            parts.append(f"Status: {issue_data['status']}")

        if issue_data.get('assignee'):
            parts.append(f"Assignee: {issue_data['assignee']}")

        if issue_data.get('priority'):
            parts.append(f"Priority: {issue_data['priority']}")

        if issue_data.get('components'):
            parts.append(f"Components: {issue_data['components']}")

        if issue_data.get('labels'):
            parts.append(f"Labels: {issue_data['labels']}")

        if issue_data.get('comments'):
            comments = str(issue_data['comments'])
            if len(comments) > 1000:
                comments = comments[:1000] + "..."
            parts.append(f"Comments: {comments}")

        if issue_data.get('return_reasons'):
            parts.append(f"Return Reasons: {issue_data['return_reasons']}")

        if issue_data.get('status_history'):
            history = str(issue_data['status_history'])
            if len(history) > 500:
                history = history[:500] + "..."
            parts.append(f"Status History: {history}")

        return "\n\n".join(parts)