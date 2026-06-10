/* ── File Upload Handling ── */
const resumeInput = document.getElementById('resumeInput');
const resumeInfo  = document.getElementById('resumeInfo');
const resumeName  = document.getElementById('resumeName');
const resumeZone  = document.getElementById('resumeDropZone');
const jdInput     = document.getElementById('jdInput');
const jdCount     = document.getElementById('jdCount');

resumeInput.addEventListener('change', () => {
  if (resumeInput.files[0]) setFile(resumeInput.files[0]);
});

jdInput.addEventListener('input', () => {
  jdCount.textContent = jdInput.value.length;
});

// Drag & Drop
['dragenter','dragover'].forEach(e => {
  resumeZone.addEventListener(e, ev => { ev.preventDefault(); resumeZone.classList.add('drag-over'); });
});
['dragleave','drop'].forEach(e => {
  resumeZone.addEventListener(e, ev => { ev.preventDefault(); resumeZone.classList.remove('drag-over'); });
});
resumeZone.addEventListener('drop', ev => {
  const file = ev.dataTransfer.files[0];
  if (file && file.type === 'application/pdf') {
    const dt = new DataTransfer();
    dt.items.add(file);
    resumeInput.files = dt.files;
    setFile(file);
  } else {
    showToast('Please drop a PDF file.', 'error');
  }
});

function setFile(file) {
  resumeName.textContent = file.name;
  resumeInfo.style.display = 'block';
  resumeZone.classList.add('has-file');
}

/* ── Main Analysis ── */
async function analyzeResume() {
  const file = resumeInput.files[0];
  const jd   = jdInput.value.trim();

  if (!file) { showToast('Please upload a resume PDF.', 'error'); return; }
  if (!jd)   { showToast('Please paste a job description.', 'error'); return; }
  if (jd.length < 50) { showToast('Job description seems too short. Please paste the full JD.', 'error'); return; }

  showLoading();

  const formData = new FormData();
  formData.append('resume', file);
  formData.append('job_description', jd);

  try {
    const res  = await fetch('/analyze', { method: 'POST', body: formData });
    const data = await res.json();
    hideLoading();

    if (!res.ok || data.error) {
      showToast(data.error || 'Analysis failed. Please try again.', 'error');
      return;
    }

    renderDashboard(data);
  } catch (err) {
    hideLoading();
    showToast('Network error. Is the server running?', 'error');
  }
}

/* ── Loading Steps ── */
let loadingTimer;
function showLoading() {
  document.getElementById('loadingOverlay').style.display = 'flex';
  document.getElementById('analyzeBtn').disabled = true;

  const steps = ['ls1','ls2','ls3','ls4','ls5'];
  let i = 0;
  steps.forEach(id => document.getElementById(id).className = 'lstep');

  loadingTimer = setInterval(() => {
    if (i > 0) document.getElementById(steps[i-1]).className = 'lstep done';
    if (i < steps.length) {
      document.getElementById(steps[i]).className = 'lstep active';
      i++;
    } else {
      clearInterval(loadingTimer);
    }
  }, 500);
}

function hideLoading() {
  clearInterval(loadingTimer);
  document.getElementById('loadingOverlay').style.display = 'none';
  document.getElementById('analyzeBtn').disabled = false;
}

/* ── Render Dashboard ── */
function renderDashboard(data) {
  const { ats_score, matching_skills, missing_skills, extra_skills,
          keyword_overlap, keyword_missing, suggestions, stats } = data;

  // Scroll
  document.getElementById('upload').style.display = 'none';
  const dash = document.getElementById('dashboard');
  dash.style.display = 'block';
  setTimeout(() => dash.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);

  // ATS Score Ring
  const circumference = 327;
  const offset = circumference - (ats_score / 100) * circumference;
  const ring   = document.getElementById('ringFill');
  setTimeout(() => {
    ring.style.strokeDashoffset = offset;
    ring.style.stroke = scoreColor(ats_score);
  }, 200);

  // Animate score number
  animateNumber('scoreNum', 0, ats_score, 1200);

  // Grade
  const [grade, desc] = scoreGrade(ats_score);
  document.getElementById('scoreGrade').textContent = grade;
  document.getElementById('scoreGrade').style.color = scoreColor(ats_score);
  document.getElementById('scoreDesc').textContent  = desc;

  // Stats
  document.getElementById('statMatched').textContent = stats.matched_skills_count;
  document.getElementById('statMissing').textContent  = stats.missing_skills_count;
  document.getElementById('statJDSkills').textContent = stats.total_jd_skills;
  document.getElementById('statWords').textContent    = stats.resume_words;

  // Skills
  renderTags('matchingSkills', matching_skills, 'tag-green');
  renderTags('missingSkills',  missing_skills,  'tag-red');
  renderTags('extraSkills',    extra_skills,    'tag-gray');
  document.getElementById('matchCount').textContent = matching_skills.length;
  document.getElementById('missCount').textContent  = missing_skills.length;
  document.getElementById('extraCount').textContent = extra_skills.length;

  // Keywords
  renderKwTags('kwOverlap', keyword_overlap.slice(0, 20));
  renderKwTags('kwMissing', keyword_missing.slice(0, 20));

  // Sections
  renderSections(stats.sections);

  // Suggestions
  renderSuggestions(suggestions);

  // Score Bars
  const skillPct = stats.total_jd_skills > 0
    ? Math.round((stats.matched_skills_count / stats.total_jd_skills) * 100) : 0;
  const kwPct = keyword_overlap.length > 0
    ? Math.min(100, Math.round((keyword_overlap.length / (keyword_overlap.length + keyword_missing.length)) * 100)) : 0;

  setTimeout(() => {
    setBar('bbSkill', skillPct);  document.getElementById('bbSkillVal').textContent  = skillPct + '%';
    setBar('bbKw',    kwPct);     document.getElementById('bbKwVal').textContent     = kwPct + '%';
    setBar('bbAts',   ats_score); document.getElementById('bbAtsVal').textContent    = ats_score + '%';
  }, 400);
}

function renderTags(containerId, items, cls) {
  const el = document.getElementById(containerId);
  if (!items || items.length === 0) {
    el.innerHTML = `<span class="tag-empty">None found</span>`;
    return;
  }
  el.innerHTML = items.map(s =>
    `<span class="skill-tag ${cls}">${capitalize(s)}</span>`
  ).join('');
}

function renderKwTags(containerId, items) {
  const el = document.getElementById(containerId);
  el.innerHTML = items.map(k => `<span class="kw-tag">${k}</span>`).join('') || '<span class="tag-empty">—</span>';
}

function renderSections(sections) {
  const grid = document.getElementById('sectionsGrid');
  const labels = { experience: '💼 Experience', education: '🎓 Education',
                   skills: '⚡ Skills', summary: '📋 Summary', projects: '🛠 Projects' };
  grid.innerHTML = Object.entries(sections).map(([k, v]) =>
    `<span class="section-chip ${v ? 'sec-present' : 'sec-missing'}">
      ${v ? '✓' : '✗'} ${labels[k] || k}
    </span>`
  ).join('');
}

function renderSuggestions(suggestions) {
  const list = document.getElementById('suggestionsList');
  list.innerHTML = suggestions.map(s =>
    `<div class="suggestion-item sug-${s.type}">
      <div class="sug-icon">${s.icon}</div>
      <div class="sug-body">
        <h4>${s.title}</h4>
        <p>${s.detail}</p>
      </div>
    </div>`
  ).join('');
}

/* ── Helpers ── */
function scoreColor(score) {
  if (score >= 75) return '#22c55e';
  if (score >= 55) return '#f59e0b';
  if (score >= 35) return '#f97316';
  return '#ef4444';
}

function scoreGrade(score) {
  if (score >= 80) return ['Excellent 🎯', 'Strong ATS match — you\'re likely to pass automated screening.'];
  if (score >= 65) return ['Good 👍', 'Solid match. A few more keywords will maximize your chances.'];
  if (score >= 50) return ['Fair ⚠️', 'Moderate match. Focus on the missing skills and keywords below.'];
  if (score >= 35) return ['Weak 🔶', 'Low match. Significant keyword alignment needed for this role.'];
  return ['Poor 🚨', 'Very low match. Consider heavily tailoring this resume for the role.'];
}

function animateNumber(id, from, to, duration) {
  const el    = document.getElementById(id);
  const start = performance.now();
  const range = to - from;
  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = (from + range * ease).toFixed(1);
    if (progress < 1) requestAnimationFrame(step);
    else el.textContent = to;
  }
  requestAnimationFrame(step);
}

function setBar(id, pct) {
  document.getElementById(id).style.width = Math.min(100, pct) + '%';
}

function capitalize(str) {
  return str.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function resetAnalysis() {
  document.getElementById('dashboard').style.display = 'none';
  document.getElementById('upload').style.display = 'block';
  resumeInput.value = '';
  jdInput.value = '';
  jdCount.textContent = '0';
  resumeInfo.style.display = 'none';
  resumeZone.classList.remove('has-file');
  document.getElementById('ringFill').style.strokeDashoffset = 327;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ── Toast Notifications ── */
function showToast(msg, type = 'info') {
  let toast = document.getElementById('toastEl');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toastEl';
    toast.style.cssText = `
      position:fixed; bottom:28px; right:28px; z-index:9999;
      padding:14px 22px; border-radius:12px; font-size:14px; font-weight:600;
      max-width:340px; box-shadow:0 8px 30px rgba(0,0,0,.4);
      transition: opacity .3s, transform .3s;
    `;
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.background = type === 'error' ? '#ef4444' : '#6c63ff';
  toast.style.color = '#fff';
  toast.style.opacity = '1';
  toast.style.transform = 'translateY(0)';
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(8px)';
  }, 3500);
}
