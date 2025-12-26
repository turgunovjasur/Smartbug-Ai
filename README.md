# JIRA Bug Analyzer

AI-powered bug root cause analysis tizimi. Production buglarning asosiy sababini semantic search va Gemini AI yordamida topadi.

**Author:** Jasur Turgunov  
**Company:** Green White Solutions (SmartUpX)  
**Version:** 2.0.0

---

## ✨ Asosiy Imkoniyatlar

### 🔍 Smart Semantic Search
- **Multilingual Support**: O'zbek, Rus, Ingliz tillarida ishlaydi
- **Vector Database**: ChromaDB asosida tez qidiruv
- **Weighted Chunking**: Taskni semantic qismlarga bo'lib, har biriga vazn beradi
- **Root Cause Detection**: Bug sababini avtomatik aniqlaydi
- **Solution Extraction**: O'xshash tasklardan yechim topadi

### 🤖 AI Tahlil
- **Gemini 2.5 Flash**: So'nggi AI model
- **Context-Aware**: Task history, developer, sprint ma'lumotlarini hisobga oladi
- **Konkret Yechimlar**: Amaliy tavsiyalar beradi
- **Preventive Measures**: Kelajakda xatolarni oldini olish yo'llari

### 📈 Sprint Statistika
- **Developer Performance**: Har bir developer bo'yicha batafsil ma'lumot
- **Bug Trends**: Bug pattern'lar tahlili
- **Sprint Analysis**: Sprint samaradorligi
- **Return Analysis**: QA dan qaytgan tasklar
- **Timeline Tracking**: Task lifecycle kuzatuvi

### 🔗 GitHub Integratsiya
- **TZ-PR Checker**: Task TZ va kod mosligini tekshiradi
- **PR Analysis**: Pull Request tahlili
- **Code Review**: Kod sifati tekshiruvi
- **Auto Search**: JIRA'da link bo'lmasa GitHub'dan qidiradi

---

## 🚀 O'rnatish

### 1. Clone
```bash
git clone https://github.com/your-org/jira-bug-analyzer.git
cd jira-bug-analyzer
```

### 2. Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Setup

`.env` fayl yarating:
```bash
# JIRA
JIRA_SERVER=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-token

# GitHub
GITHUB_TOKEN=your-github-token
GITHUB_ORG=your-organization

# Gemini AI
GOOGLE_API_KEY=your-google-api-key

# Paths
DATA_DIR=./data
EXCEL_DIR=./data/excel_reports
VECTOR_DB_PATH=./data/vector_db

# Search
MIN_SIMILARITY=0.70
TOP_K_RESULTS=20
FINAL_TOP_N=5
```

### 5. Model Download
```bash
python 1_setup_embedding.py
```

### 6. Sprint Data Yuklash

Excel reportlarni `data/excel_reports/` ga joylashtiring:
```bash
python 2_load_sprints.py
```

---

## 💻 Ishga Tushirish
```bash
streamlit run app.py
```

Browser: `http://localhost:8501`

---

## 📁 Struktura
```
jira-bug-analyzer/
├── app.py                  # Main app
├── requirements.txt
├── .env
│
├── ui/                     # UI components
│   ├── bug_analyzer.py
│   ├── statistics.py
│   └── pages/
│       └── tz_pr_checker.py
│
├── utils/                  # Helpers
│   ├── embedding_helper.py
│   ├── vectordb_helper.py
│   ├── gemini_helper.py
│   └── chunking_helper.py
│
├── services/
│   └── tz_pr_service.py
│
└── data/
    ├── excel_reports/
    ├── vector_db/
    └── models/
```

---

## 🎯 Funksiyalar

### Bug Analyzer

1. Bug description kiriting
2. Tizim VectorDB'dan o'xshash tasklar qidiradi
3. Gemini AI tahlil qiladi
4. Root cause va yechim ko'rsatadi

### Sprint Statistics

- Umumiy ko'rsatkichlar
- Developer performance
- Bug analysis
- Return statistics
- Interactive charts

### TZ-PR Checker

1. Task key kiriting (DEV-1234)
2. JIRA'dan TZ olinadi
3. GitHub'dan PR topiladi
4. AI TZ-kod mosligini tekshiradi
5. Batafsil tahlil beradi

---

## 🔧 Sozlash

### Search Parameters

`.env`:
```bash
MIN_SIMILARITY=0.70    # Threshold
TOP_K_RESULTS=20       # Candidates
FINAL_TOP_N=5          # Final results
```

### Chunking Weights

`utils/chunking_helper.py`:
```python
weights = {
    'summary': 3.5,
    'root_cause': 3.0,
    'solution': 3.0,
    'description': 2.5,
}
```

---

## 📊 Performance

- **Search**: < 2s
- **AI Analysis**: 15-30s
- **Loading**: Incremental (faqat yangi fayllar)
- **Memory**: ~2-4 GB

---

## 🧪 Testing
```bash
python utils/test_chunking_system.py
```

---

## 👨‍💻 Author

**Jasur Turgunov**  
Automation QA Engineer  
Green White Solutions (SmartUp)

📧 tjasur224@gmail.com

---

## 📝 License

Private - Turgunon Jasur

---

## 🙏 Technologies

- **Claude AI** - Development assistance
- **Gemini AI** - Bug analysis
- **Sentence Transformers** - Embeddings
- **ChromaDB** - Vector database
- **Streamlit** - Web framework