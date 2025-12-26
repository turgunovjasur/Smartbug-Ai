import google.generativeai as genai
import os
from dotenv import load_dotenv
import time

load_dotenv()


class GeminiHelper:
    def __init__(self):
        api_key = os.getenv('GOOGLE_API_KEY')
        model_name = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

        self.request_count = 0
        self.last_request_time = 0

        print(f"Gemini AI tayyor: {model_name}")

    def _rate_limit(self):
        """Rate limiting: max 10 req/min"""
        min_interval = 6  # 60/10 = 6 sekund

        elapsed = time.time() - self.last_request_time
        if elapsed < min_interval:
            wait_time = min_interval - elapsed
            print(f"Kutish: {wait_time:.1f} sekund...")
            time.sleep(wait_time)

        self.last_request_time = time.time()
        self.request_count += 1

    def analyze(self, prompt):
        """Gemini bilan tahlil"""
        self._rate_limit()

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Xatolik: {str(e)}"