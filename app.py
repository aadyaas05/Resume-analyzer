from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from flask import Flask, jsonify, render_template, request
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB

SKILLS = {
    "python",
    "flask",
    "django",
    "fastapi",
    "javascript",
    "typescript",
    "react",
    "node.js",
    "node",
    "html",
    "css",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "git",
    "github",
    "ci/cd",
    "machine learning",
    "nlp",
    "data analysis",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "rest api",
    "microservices",
    "linux",
    "testing",
}


@app.route("/")
def index() -> str:
    return render_template("index.html")


def extract_pdf_text(pdf_file) -> str:
    reader = PdfReader(pdf_file)
    extracted = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(extracted).strip()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def detect_skills(source_text: str, catalog: Iterable[str]) -> set[str]:
    normalized = normalize_text(source_text)
    found = {skill for skill in catalog if skill in normalized}
    return found


def ats_score(resume_text: str, job_text: str) -> int:
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([resume_text, job_text])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    return int(round(max(0.0, min(similarity, 1.0)) * 100))


def generate_suggestions(score: int, missing: list[str]) -> list[str]:
    suggestions: list[str] = []

    if missing:
        suggestions.append(
            "Add these missing skills to your resume where relevant: "
            + ", ".join(missing[:8])
            + "."
        )
    if score < 60:
        suggestions.append("Customize your resume summary to directly match the job description keywords.")
        suggestions.append("Add measurable achievements using numbers to improve ATS relevance and recruiter impact.")
    elif score < 80:
        suggestions.append("Strengthen project bullets by emphasizing tools and responsibilities that match this role.")
    else:
        suggestions.append("Great alignment. Fine-tune phrasing to mirror role-specific terminology for an even better match.")

    if not suggestions:
        suggestions.append("Your resume already aligns well. Keep tailoring for each role.")

    return suggestions


@app.post("/analyze")
def analyze():
    resume_file = request.files.get("resume")
    if not resume_file or not resume_file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Please upload a valid resume in PDF format."}), 400

    job_description_text = (request.form.get("job_description") or "").strip()
    jd_file = request.files.get("job_description_file")

    if jd_file and jd_file.filename:
        suffix = Path(jd_file.filename).suffix.lower()
        if suffix != ".txt":
            return jsonify({"error": "Job description file must be a .txt file."}), 400
        job_description_text = jd_file.read().decode("utf-8", errors="ignore").strip()

    if not job_description_text:
        return jsonify({"error": "Please provide a job description using text input or upload a .txt file."}), 400

    try:
        resume_text = extract_pdf_text(resume_file)
    except Exception:
        return jsonify({"error": "Unable to read the PDF. Please upload a text-based PDF file."}), 400

    if not resume_text:
        return jsonify({"error": "No extractable text found in the uploaded resume PDF."}), 400

    score = ats_score(resume_text, job_description_text)
    resume_skills = detect_skills(resume_text, SKILLS)
    jd_skills = detect_skills(job_description_text, SKILLS)

    matching_skills = sorted(resume_skills & jd_skills)
    missing_skills = sorted(jd_skills - resume_skills)

    response = {
        "ats_score": score,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "suggestions": generate_suggestions(score, missing_skills),
    }

    return jsonify(response)


if __name__ == "__main__":
    app.run()
