# AI Resume Analyzer

A full-stack AI Resume Analyzer built with **Python + Flask** and a modern responsive frontend (**HTML/CSS/JavaScript**).
It compares a PDF resume against a job description using **TF-IDF + cosine similarity** and provides ATS insights.

## Features

- Upload resume in **PDF** format
- Paste or upload job description (`.txt`)
- Extract text from PDF
- ATS match score out of **100**
- Matching skills and missing skills analysis
- Suggestions to improve resume relevance
- Responsive dashboard-style UI with ATS score card

## Project Structure

```text
Resume-analyzer/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── css/
    │   └── styles.css
    └── js/
        └── app.js
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the App

```bash
python app.py
```

Open: `http://127.0.0.1:5000`

## How Scoring Works

1. Resume PDF text is extracted using `PyPDF2`.
2. Resume text and job description are vectorized with `TfidfVectorizer`.
3. Cosine similarity is computed and scaled to a score out of 100.
4. Skill overlap is used to show matching and missing skills.

## Notes

- Resume uploads are limited to 5 MB.
- Use text-based PDFs for best extraction results.
- This is a keyword + similarity based analyzer, not a replacement for human review.
