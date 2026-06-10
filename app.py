import os
import re
import json
import math
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import pdfplumber
from collections import Counter

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ─── NLP Utilities ────────────────────────────────────────────────────────────

STOPWORDS = {
    'a','an','the','and','or','but','in','on','at','to','for','of','with',
    'by','from','is','are','was','were','be','been','being','have','has',
    'had','do','does','did','will','would','could','should','may','might',
    'shall','can','need','dare','ought','used','i','me','my','we','our',
    'you','your','he','his','she','her','it','its','they','their','this',
    'that','these','those','as','up','out','if','about','who','which','what',
    'there','when','where','how','all','each','both','few','more','most',
    'other','some','such','no','not','only','same','so','than','too','very',
    's','t','just','don','into','also','well','get','use','using','used',
    'including','within','across','through','between','during','while'
}

TECH_SKILLS = [
    # Programming Languages
    'python','java','javascript','typescript','c++','c#','c','ruby','go','rust',
    'scala','kotlin','swift','php','r','matlab','perl','bash','shell','powershell',
    # Web
    'html','css','react','angular','vue','nodejs','node.js','express','django',
    'flask','fastapi','spring','springboot','asp.net','laravel','rails','nextjs',
    'nuxt','gatsby','graphql','rest','restful','api','soap','webpack','vite',
    # Data & ML
    'machine learning','deep learning','nlp','natural language processing',
    'computer vision','tensorflow','pytorch','keras','scikit-learn','sklearn',
    'pandas','numpy','scipy','matplotlib','seaborn','plotly','tableau','powerbi',
    'data analysis','data science','data engineering','etl','feature engineering',
    'model training','model deployment','mlops','statistics','regression',
    'classification','clustering','neural network','transformer','bert','llm',
    # Cloud & DevOps
    'aws','azure','gcp','google cloud','docker','kubernetes','terraform','ansible',
    'jenkins','ci/cd','devops','git','github','gitlab','bitbucket','linux','unix',
    'microservices','serverless','lambda','ec2','s3','rds','dynamodb',
    # Databases
    'sql','mysql','postgresql','mongodb','redis','elasticsearch','cassandra',
    'oracle','sqlite','nosql','database','hadoop','spark','kafka','airflow',
    # Soft Skills
    'leadership','communication','teamwork','problem solving','critical thinking',
    'project management','agile','scrum','kanban','jira','collaboration',
    'time management','analytical','detail oriented','presentation','mentoring',
    # Other Tech
    'cybersecurity','blockchain','iot','embedded','mobile','android','ios',
    'testing','unit testing','integration testing','selenium','pytest','junit',
    'figma','adobe','ux','ui','product management','business analysis',
]

def tokenize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s\.\+#]', ' ', text)
    tokens = text.split()
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]

def extract_ngrams(text, n=2):
    tokens = tokenize(text)
    ngrams = []
    for i in range(len(tokens) - n + 1):
        ngrams.append(' '.join(tokens[i:i+n]))
    return ngrams

def build_vocabulary(texts):
    vocab = set()
    for text in texts:
        vocab.update(tokenize(text))
        vocab.update(extract_ngrams(text, 2))
    return sorted(vocab)

def compute_tf(tokens):
    count = Counter(tokens)
    total = len(tokens) if tokens else 1
    return {term: freq / total for term, freq in count.items()}

def compute_tfidf_vector(text, vocab, idf_scores):
    tokens = tokenize(text) + extract_ngrams(text, 2)
    tf = compute_tf(tokens)
    vector = {}
    for term in vocab:
        if term in tf and term in idf_scores:
            vector[term] = tf[term] * idf_scores[term]
        else:
            vector[term] = 0.0
    return vector

def compute_idf(texts, vocab):
    N = len(texts)
    idf = {}
    for term in vocab:
        doc_count = sum(1 for text in texts if term in (tokenize(text) + extract_ngrams(text, 2)))
        idf[term] = math.log((N + 1) / (doc_count + 1)) + 1
    return idf

def cosine_similarity(vec1, vec2):
    dot = sum(vec1.get(t, 0) * vec2.get(t, 0) for t in vec1)
    mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)

def extract_skills(text):
    text_lower = text.lower()
    found = set()
    # Single-word skills
    tokens = set(tokenize(text_lower))
    for skill in TECH_SKILLS:
        if ' ' not in skill and skill in tokens:
            found.add(skill)
    # Multi-word skills
    for skill in TECH_SKILLS:
        if ' ' in skill and skill in text_lower:
            found.add(skill)
    return found

def extract_text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def extract_sections(text):
    """Identify key resume sections."""
    sections = {
        'experience': '',
        'education': '',
        'skills': '',
        'summary': '',
        'projects': ''
    }
    section_patterns = {
        'experience': r'(work experience|professional experience|employment|experience)',
        'education': r'(education|academic|qualification)',
        'skills': r'(skills|technical skills|core competencies|competencies)',
        'summary': r'(summary|objective|profile|about)',
        'projects': r'(projects|portfolio|work samples)'
    }
    lines = text.split('\n')
    current_section = 'summary'
    for line in lines:
        ll = line.lower().strip()
        matched = False
        for sec, pattern in section_patterns.items():
            if re.search(pattern, ll) and len(ll) < 50:
                current_section = sec
                matched = True
                break
        if not matched:
            sections[current_section] += line + '\n'
    return sections

def generate_suggestions(resume_text, jd_text, missing_skills, match_score):
    suggestions = []

    # Score-based suggestions
    if match_score < 40:
        suggestions.append({
            'type': 'critical',
            'icon': '🚨',
            'title': 'Low ATS Match Score',
            'detail': 'Your resume matches less than 40% of the job requirements. Consider a significant rewrite targeting this specific role.'
        })
    elif match_score < 60:
        suggestions.append({
            'type': 'warning',
            'icon': '⚠️',
            'title': 'Moderate Match — Room for Improvement',
            'detail': 'Your score is between 40–60%. Focus on incorporating key missing skills and aligning your language with the JD.'
        })
    else:
        suggestions.append({
            'type': 'success',
            'icon': '✅',
            'title': 'Good ATS Match',
            'detail': 'Your resume scores above 60%. Minor tweaks to add missing keywords can push you above 80%.'
        })

    # Missing skills suggestion
    if missing_skills:
        top_missing = list(missing_skills)[:8]
        suggestions.append({
            'type': 'warning',
            'icon': '🔧',
            'title': 'Add Missing Skills',
            'detail': f'Include these skills if you have them: {", ".join(top_missing)}. Add them in your Skills section or weave them into bullet points.'
        })

    # Keyword density
    resume_tokens = tokenize(resume_text)
    jd_tokens = tokenize(jd_text)
    jd_unique = set(jd_tokens) - set(resume_tokens)
    if len(jd_unique) > 20:
        suggestions.append({
            'type': 'info',
            'icon': '📝',
            'title': 'Improve Keyword Alignment',
            'detail': f'The job description uses {len(jd_unique)} keywords not found in your resume. Mirror the JD language — if the JD says "cross-functional collaboration," use that exact phrase.'
        })

    # Resume length
    word_count = len(resume_text.split())
    if word_count < 200:
        suggestions.append({
            'type': 'warning',
            'icon': '📄',
            'title': 'Resume Too Short',
            'detail': f'Your resume has only ~{word_count} words. Aim for 400–700 words to give ATS systems enough content to evaluate.'
        })
    elif word_count > 1000:
        suggestions.append({
            'type': 'info',
            'icon': '✂️',
            'title': 'Consider Condensing Your Resume',
            'detail': f'Your resume is ~{word_count} words. For most roles, 1–2 pages is ideal. Remove outdated or irrelevant experience.'
        })

    # Action verbs
    action_verbs = ['developed','built','designed','led','managed','implemented','optimized',
                    'delivered','created','launched','improved','reduced','increased','achieved']
    found_verbs = [v for v in action_verbs if v in resume_text.lower()]
    if len(found_verbs) < 4:
        suggestions.append({
            'type': 'info',
            'icon': '💪',
            'title': 'Use Strong Action Verbs',
            'detail': 'Start bullet points with strong verbs like: Developed, Optimized, Led, Delivered, Reduced, Increased. This improves readability and ATS parsing.'
        })

    # Quantifiable achievements
    numbers_found = re.findall(r'\b\d+[%x]?\b', resume_text)
    if len(numbers_found) < 3:
        suggestions.append({
            'type': 'info',
            'icon': '📊',
            'title': 'Quantify Your Achievements',
            'detail': 'Add measurable results to your bullets. E.g., "Reduced load time by 40%" or "Managed a team of 8 engineers." Numbers stand out to both ATS and hiring managers.'
        })

    # Contact info / sections
    if not re.search(r'\b[\w._%+-]+@[\w.-]+\.[a-z]{2,}\b', resume_text, re.I):
        suggestions.append({
            'type': 'critical',
            'icon': '📧',
            'title': 'Add Contact Information',
            'detail': 'No email address detected. Ensure your resume includes email, phone, LinkedIn, and location at the top.'
        })

    return suggestions

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Handle resume
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume uploaded'}), 400

        resume_file = request.files['resume']
        jd_text = request.form.get('job_description', '').strip()

        if not jd_text:
            return jsonify({'error': 'No job description provided'}), 400

        if resume_file.filename == '':
            return jsonify({'error': 'No resume selected'}), 400

        if not resume_file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF resumes are supported'}), 400

        filename = secure_filename(resume_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        resume_file.save(filepath)

        # Extract text
        resume_text = extract_text_from_pdf(filepath)
        if not resume_text:
            return jsonify({'error': 'Could not extract text from PDF. Ensure it is not a scanned image.'}), 400

        # Build TF-IDF
        vocab = build_vocabulary([resume_text, jd_text])
        idf = compute_idf([resume_text, jd_text], vocab)
        resume_vec = compute_tfidf_vector(resume_text, vocab, idf)
        jd_vec = compute_tfidf_vector(jd_text, vocab, idf)

        # Component 1: Cosine similarity on TF-IDF vectors
        cos_score = cosine_similarity(resume_vec, jd_vec)

        # Component 2: Skill overlap ratio (computed after skill extraction)
        # (used below after skills are extracted)

        # Component 3: Raw keyword overlap ratio
        resume_kw = set(tokenize(resume_text))
        jd_kw = set(tokenize(jd_text))
        kw_overlap_ratio = len(resume_kw & jd_kw) / max(len(jd_kw), 1)

        # Skill matching
        resume_skills = extract_skills(resume_text)
        jd_skills = extract_skills(jd_text)

        # Combined ATS score: 40% cosine TF-IDF, 35% skill coverage, 25% keyword overlap
        skill_ratio = len(resume_skills & jd_skills) / max(len(jd_skills), 1)
        ats_score = round(min(100, (cos_score * 0.40 + skill_ratio * 0.35 + kw_overlap_ratio * 0.25) * 100), 1)
        matching_skills = sorted(resume_skills & jd_skills)
        missing_skills = sorted(jd_skills - resume_skills)
        extra_skills = sorted(resume_skills - jd_skills)

        # Keyword overlap
        resume_tokens = set(tokenize(resume_text))
        jd_tokens = set(tokenize(jd_text))
        keyword_overlap = sorted(resume_tokens & jd_tokens - STOPWORDS)[:30]
        keyword_missing = sorted(jd_tokens - resume_tokens - STOPWORDS)[:30]

        # Sections
        sections = extract_sections(resume_text)
        section_present = {k: bool(v.strip()) for k, v in sections.items()}

        # Suggestions
        suggestions = generate_suggestions(resume_text, jd_text, set(missing_skills), ats_score)

        # Word counts
        resume_words = len(resume_text.split())
        jd_words = len(jd_text.split())

        # Clean up uploaded file
        os.remove(filepath)

        return jsonify({
            'ats_score': ats_score,
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'extra_skills': extra_skills[:15],
            'keyword_overlap': keyword_overlap,
            'keyword_missing': keyword_missing,
            'suggestions': suggestions,
            'stats': {
                'resume_words': resume_words,
                'jd_words': jd_words,
                'total_jd_skills': len(jd_skills),
                'matched_skills_count': len(matching_skills),
                'missing_skills_count': len(missing_skills),
                'sections': section_present
            }
        })

    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
