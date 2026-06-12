# ⚡ ResumeIQ — AI Resume Analyzer
🔗 **[Live Demo](https://resume-analyzer-dbyc.onrender.com)**

A full-stack AI-powered Resume Analyzer built with **Python + Flask**, using **TF-IDF vectorization** and **Cosine Similarity** to calculate an ATS match score between a resume and job description — no external AI APIs required.

---

## 🚀 Features

| Feature | Details |
|---|---|
| 📄 PDF Parsing | Extracts text from multi-page PDFs using `pdfplumber` |
| 🧮 TF-IDF Vectorization | Weighs term importance across both documents |
| 📐 Cosine Similarity | Measures semantic alignment for ATS scoring |
| ✅ Matching Skills | 200+ tech/soft skills matched against the JD |
| ❌ Missing Skills | Skills in the JD but absent from the resume |
| 💡 AI Suggestions | Rule-based + NLP suggestions to improve the resume |
| 📊 Score Dashboard | Animated ring chart, stat cards, and breakdown bars |
| 🔑 Keyword Analysis | Overlapping and missing keywords between both documents |
| 📋 Section Detection | Detects Experience, Education, Skills, Summary, Projects |
| 📱 Responsive UI | Works on desktop, tablet, and mobile |

---

## 🛠 Tech Stack

- **Backend:** Python 3.10+, Flask 3
- **NLP:** TF-IDF (custom implementation), Cosine Similarity, N-grams
- **PDF Parsing:** pdfplumber
- **Frontend:** Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Fonts:** Inter (Google Fonts)

---

## 📂 Project Structure

```
resume_analyzer/
├── app.py                  # Flask app + NLP logic
├── requirements.txt        # Python dependencies
├── README.md
├── templates/
│   └── index.html          # Single-page application
└── static/
    ├── css/
    │   └── style.css       # Dark-mode responsive styles
    ├── js/
    │   └── main.js         # Frontend logic, animations
    └── uploads/            # Temp upload dir (auto-created)
```

---

## ⚙️ Installation & Setup

### 1. Clone / download the project

```bash
git clone https://github.com/yourname/resume-analyzer.git
cd resume-analyzer
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 🎯 How It Works

### 1. PDF Text Extraction
`pdfplumber` parses the uploaded resume PDF page-by-page, extracting raw text while preserving structure.

### 2. Tokenization & Preprocessing
- Lowercases text
- Removes punctuation (preserving `+`, `#`, `.` for tech terms)
- Filters stopwords (custom list of ~100 common English words)
- Extracts both unigrams and bigrams

### 3. TF-IDF Vectorization
For each term in the shared vocabulary:
- **TF (Term Frequency):** `count(term) / total_terms`
- **IDF (Inverse Document Frequency):** `log((N+1) / (df+1)) + 1` (smoothed)
- **TF-IDF score:** `TF × IDF`

### 4. Cosine Similarity
```
similarity = (A · B) / (|A| × |B|)
```
The dot product of the TF-IDF vectors divided by the product of their magnitudes. Scaled and capped to produce a 0–100 ATS score.

### 5. Skill Matching
A curated list of 200+ skills (programming languages, frameworks, cloud platforms, soft skills) is matched against both documents using exact token matching and multi-word phrase search.

### 6. Suggestions Engine
Generates contextual suggestions based on:
- Score thresholds
- Missing skill count
- Keyword density gaps
- Resume word count
- Action verb usage
- Quantifiable achievements
- Contact info presence

---

## 📈 ATS Score Interpretation

| Score | Grade | Meaning |
|---|---|---|
| 80–100 | Excellent 🎯 | Strong match, likely to pass ATS |
| 65–79 | Good 👍 | Solid match, minor tweaks needed |
| 50–64 | Fair ⚠️ | Moderate match, keyword work needed |
| 35–49 | Weak 🔶 | Low match, significant tailoring needed |
| 0–34 | Poor 🚨 | Very low match, major rewrite recommended |

---

## 🔒 Privacy

- Uploaded PDFs are saved temporarily, analyzed, and **immediately deleted** after processing.
- No data is stored, logged, or sent to any external service.
- All NLP processing happens locally on your machine.

---

## 🧩 Extending the Project

- **Add authentication** with Flask-Login for multi-user support
- **Store history** with SQLite + SQLAlchemy
- **Export report** as PDF using ReportLab
- **Add spaCy NER** for better skill extraction
- **Deploy** to Render, Railway, or Heroku with a `Procfile`

---

## 📄 License

MIT License — free to use, modify, and distribute.
