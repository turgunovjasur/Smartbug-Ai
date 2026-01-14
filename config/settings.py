# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Loyiha sozlamalari"""

    # ==================== JIRA ====================
    JIRA_SERVER = os.getenv('JIRA_SERVER', 'https://smartupx.atlassian.net')
    JIRA_EMAIL = os.getenv('JIRA_EMAIL')
    JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

    # JIRA Custom Fields
    STORY_POINTS_FIELD = 'customfield_10016'
    SPRINT_FIELD = 'customfield_10020'
    PR_FIELD = 'customfield_10000'  # Development panel

    # ==================== GitHub ====================
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
    GITHUB_API_URL = 'https://api.github.com'
    GITHUB_ORG = os.getenv('GITHUB_ORG', 'greenwhite')

    # ==================== Gemini AI ====================
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

    # ==================== Embedding ====================
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'intfloat/multilingual-e5-large')
    MODELS_DIR = os.getenv('MODELS_DIR', './models')

    # ==================== Paths ====================
    DATA_DIR = os.getenv('DATA_DIR', './data')
    EXCEL_DIR = os.getenv('EXCEL_DIR', './data/excel_reports')
    VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', './data/vector_db')
    CACHE_DIR = os.getenv('CACHE_DIR', './data/cache')

    # ==================== Search Parameters ====================
    MIN_SIMILARITY = float(os.getenv('MIN_SIMILARITY', 0.70))
    TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', 20))
    FINAL_TOP_N = int(os.getenv('FINAL_TOP_N', 5))

    # ==================== Status Constants ====================
    TESTING_STATUSES = ['TESTING', 'Ready to Test', 'NEED CLARIFICATION/RETURN TEST']
    DONE_STATUSES = ['CLOSED', 'Closed', 'Done', 'Resolved']
    RETURN_STATUS = 'NEED CLARIFICATION/RETURN TEST'

    @classmethod
    def validate(cls):
        """Sozlamalar to'g'riligini tekshirish"""
        errors = []

        if not cls.JIRA_EMAIL:
            errors.append("JIRA_EMAIL o'rnatilmagan")
        if not cls.JIRA_API_TOKEN:
            errors.append("JIRA_API_TOKEN o'rnatilmagan")
        if not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY o'rnatilmagan")

        # GitHub token ixtiyoriy, lekin TZ-PR uchun kerak
        if not cls.GITHUB_TOKEN:
            print("⚠️ GITHUB_TOKEN o'rnatilmagan - TZ-PR Moslik ishlamaydi")

        if errors:
            raise ValueError(f"Sozlamalar xatosi: {', '.join(errors)}")

        return True

    @classmethod
    def get_status(cls):
        """Sozlamalar holatini ko'rsatish"""
        return {
            'jira': bool(cls.JIRA_EMAIL and cls.JIRA_API_TOKEN),
            'github': bool(cls.GITHUB_TOKEN),
            'gemini': bool(cls.GOOGLE_API_KEY),
            'vectordb': os.path.exists(cls.VECTOR_DB_PATH) if cls.VECTOR_DB_PATH else False
        }


# Singleton instance
settings = Settings()