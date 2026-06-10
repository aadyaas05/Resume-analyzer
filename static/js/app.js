const form = document.getElementById("analyzer-form");
const resultsCard = document.getElementById("results-card");
const scoreRing = document.getElementById("score-ring");
const scoreValue = document.getElementById("score-value");
const matchingSkills = document.getElementById("matching-skills");
const missingSkills = document.getElementById("missing-skills");
const suggestions = document.getElementById("suggestions");

const renderChips = (target, items, cssClass, emptyText) => {
  target.innerHTML = "";
  if (!items.length) {
    const span = document.createElement("span");
    span.className = `chip ${cssClass}`;
    span.textContent = emptyText;
    target.appendChild(span);
    return;
  }

  items.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = `chip ${cssClass}`;
    chip.textContent = item;
    target.appendChild(chip);
  });
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const formData = new FormData(form);

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body: formData,
    });

    const payload = await response.json();
    if (!response.ok) {
      alert(payload.error || "Analysis failed.");
      return;
    }

    const score = payload.ats_score || 0;
    scoreValue.textContent = String(score);
    scoreRing.style.setProperty("--progress", `${score}%`);

    renderChips(matchingSkills, payload.matching_skills || [], "good", "No matching skills found yet");
    renderChips(missingSkills, payload.missing_skills || [], "bad", "No key skills missing");

    suggestions.innerHTML = "";
    (payload.suggestions || []).forEach((tip) => {
      const li = document.createElement("li");
      li.textContent = tip;
      suggestions.appendChild(li);
    });

    resultsCard.hidden = false;
    resultsCard.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    alert("Could not analyze resume. Please try again.");
  }
});
