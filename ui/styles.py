# ui/styles.py

CUSTOM_CSS = """
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    /* Root Variables */
    :root {
        --bg-primary: #0d1117;
        --bg-secondary: #161b22;
        --bg-tertiary: #21262d;
        --bg-card: #1c2128;
        --text-primary: #e6edf3;
        --text-secondary: #8b949e;
        --text-muted: #6e7681;
        --accent-blue: #58a6ff;
        --accent-green: #3fb950;
        --accent-orange: #d29922;
        --accent-red: #f85149;
        --accent-purple: #a371f7;
        --border-color: #30363d;
        --gradient-1: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --gradient-2: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --gradient-3: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }

    /* Main App Styling */
    .stApp {
        background: var(--bg-primary);
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Hide Streamlit Branding */
    #MainMenu, footer, header {visibility: hidden;}
    .stDeployButton {display: none;}

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: var(--text-primary);
    }

    /* Custom Header */
    .main-header {
        background: linear-gradient(135deg, rgba(88, 166, 255, 0.1) 0%, rgba(163, 113, 247, 0.1) 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
    }

    .main-header h1 {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-weight: 700;
        font-size: 2.5rem;
        background: linear-gradient(135deg, #58a6ff 0%, #a371f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .main-header p {
        color: var(--text-secondary);
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }

    .main-header .author {
        color: var(--text-muted);
        font-size: 0.9rem;
        margin-top: 0.5rem;
        font-style: italic;
    }

    /* Card Styling */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        border-color: var(--accent-blue);
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(88, 166, 255, 0.15);
    }

    .metric-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .metric-label {
        color: var(--text-secondary);
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Task Card */
    .task-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid var(--accent-blue);
    }

    .task-card.high-similarity {
        border-left-color: var(--accent-green);
    }

    .task-card.medium-similarity {
        border-left-color: var(--accent-orange);
    }

    .task-key {
        font-family: 'JetBrains Mono', monospace;
        color: var(--accent-blue);
        font-weight: 600;
        font-size: 1.1rem;
    }

    .similarity-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 1rem;
    }

    .similarity-high {
        background: rgba(63, 185, 80, 0.2);
        color: var(--accent-green);
    }

    .similarity-medium {
        background: rgba(210, 153, 34, 0.2);
        color: var(--accent-orange);
    }

    /* AI Analysis Box */
    .ai-analysis {
        background: linear-gradient(135deg, rgba(88, 166, 255, 0.05) 0%, rgba(163, 113, 247, 0.05) 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
    }

    .ai-analysis-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
    }

    .ai-analysis-header h3 {
        color: var(--text-primary);
        margin: 0;
        font-weight: 600;
    }

    /* Modern Loading Animation */
    .modern-loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 3rem;
        gap: 1.5rem;
    }

    .pulse-animation {
        width: 80px;
        height: 80px;
        position: relative;
    }

    .pulse-ring {
        position: absolute;
        width: 100%;
        height: 100%;
        border: 3px solid var(--accent-blue);
        border-radius: 50%;
        animation: pulse-ring 1.5s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
    }

    .pulse-ring:nth-child(2) {
        animation-delay: 0.5s;
    }

    .pulse-ring:nth-child(3) {
        animation-delay: 1s;
    }

    .pulse-core {
        position: absolute;
        width: 40%;
        height: 40%;
        top: 30%;
        left: 30%;
        background: linear-gradient(135deg, #58a6ff 0%, #a371f7 100%);
        border-radius: 50%;
        animation: pulse-core 1.5s ease-in-out infinite;
    }

    @keyframes pulse-ring {
        0% {
            transform: scale(0.5);
            opacity: 1;
        }
        100% {
            transform: scale(1.3);
            opacity: 0;
        }
    }

    @keyframes pulse-core {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.2);
        }
    }

    .loading-text {
        color: var(--text-primary);
        font-size: 1.1rem;
        font-weight: 500;
        animation: fade-in-out 2s ease-in-out infinite;
    }

    .loading-subtext {
        color: var(--text-secondary);
        font-size: 0.9rem;
    }

    @keyframes fade-in-out {
        0%, 100% {
            opacity: 0.5;
        }
        50% {
            opacity: 1;
        }
    }

    /* Text Area Styling */
    .stTextArea textarea {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9rem !important;
        padding: 1rem !important;
    }

    .stTextArea textarea:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.1) !important;
    }

    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #58a6ff 0%, #a371f7 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(88, 166, 255, 0.3) !important;
    }

    /* Slider Styling */
    .stSlider > div > div {
        background: var(--bg-tertiary) !important;
    }

    .stSlider [data-baseweb="slider"] {
        background: var(--accent-blue) !important;
    }

    /* Select Box */
    .stSelectbox > div > div {
        background: var(--bg-tertiary) !important;
        border-color: var(--border-color) !important;
        color: var(--text-primary) !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-secondary);
        border-radius: 10px;
        padding: 0.5rem;
        gap: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 8px;
        color: var(--text-secondary);
        padding: 0.75rem 1.5rem;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-primary);
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-secondary);
    }

    /* Plotly Chart Container */
    .js-plotly-plot {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Divider */
    hr {
        border-color: var(--border-color);
        margin: 2rem 0;
    }

    /* Code Block */
    code {
        font-family: 'JetBrains Mono', monospace;
        background: var(--bg-tertiary);
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        color: var(--accent-blue);
    }

    /* Info/Warning/Success boxes */
    .stAlert {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }

    /* Search Results Info */
    .results-info {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
    }

    .results-info-icon {
        font-size: 1.5rem;
    }

    .results-info-text {
        flex: 1;
    }

    .results-info-title {
        color: var(--text-primary);
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    .results-info-subtitle {
        color: var(--text-secondary);
        font-size: 0.9rem;
    }
</style>
"""

# Plotly chart colors
CHART_COLORS = {
    'primary': '#58a6ff',
    'secondary': '#a371f7',
    'success': '#3fb950',
    'warning': '#d29922',
    'danger': '#f85149',
    'bg': '#0d1117',
    'card': '#1c2128',
    'border': '#30363d',
    'text': '#e6edf3',
    'text_secondary': '#8b949e'
}

COLOR_PALETTE = ['#58a6ff', '#a371f7', '#3fb950', '#d29922', '#f85149', '#79c0ff', '#d2a8ff', '#7ee787']