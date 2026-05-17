/**
 * arXiv ML Dashboard Frontend
 * Fetches papers from API and provides interactive filtering and search
 */

const API_BASE = "http://localhost:8000";
let allPapers = [];
let selectedTasks = new Set();

// ── Initialization ──────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  loadStats();
  loadPapers();
});

function setupEventListeners() {
  // Search
  const searchInput = document.getElementById("search-input");
  searchInput?.addEventListener("input", debounce(filterAndRender, 200));

  // Task filter chips - delegated from container
  document.querySelector("#task-chips")?.addEventListener("click", (e) => {
    if (e.target.classList.contains("chip")) {
      const task = e.target.dataset.task;
      if (task !== undefined) {
        selectedTasks.has(task) ? selectedTasks.delete(task) : selectedTasks.add(task);
        e.target.classList.toggle("active");
        filterAndRender();
      }
    }
  });
}

// ── API Calls ──────────────────────────────────────────────────────────────

async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/api/stats`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    // Update header stats
    const statElement = document.querySelector("#stat-total");
    if (statElement) statElement.textContent = data.total;

    // Populate task filter chips
    const filterGroup = document.querySelector("#task-chips");
    if (filterGroup) {
      const tasksHtml = data.by_task
        .filter((t) => t.task)
        .map(
          (t) =>
            `<button class="chip" data-task="${t.task}">${t.task} <span style="color: var(--muted);">(${t.n})</span></button>`
        )
        .join("");
      filterGroup.innerHTML = '<button class="chip active" data-task="">All</button>' + tasksHtml;
    }

    // Display sidebar task breakdown
    renderTaskBar(data.by_task);
  } catch (err) {
    console.error("Failed to load stats:", err);
  }
}

async function loadPapers() {
  try {
    const res = await fetch(`${API_BASE}/api/papers?limit=100`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    allPapers = await res.json();
    filterAndRender();
  } catch (err) {
    console.error("Failed to load papers:", err);
    showError("Failed to load papers. Is the backend running on " + API_BASE + "?");
  }
}

// ── Filtering & Rendering ──────────────────────────────────────────────────

function filterAndRender() {
  const searchTerm = document.getElementById("search-input")?.value.toLowerCase() || "";
  const container = document.querySelector("section");

  const filtered = allPapers.filter((paper) => {
    // Text search
    const matchesSearch =
      !searchTerm ||
      paper.title.toLowerCase().includes(searchTerm) ||
      paper.abstract.toLowerCase().includes(searchTerm) ||
      paper.summary?.toLowerCase().includes(searchTerm);

    // Task filter
    const matchesTask = selectedTasks.size === 0 || (paper.task && selectedTasks.has(paper.task));

    return matchesSearch && matchesTask;
  });

  if (container) {
    container.innerHTML =
      filtered.length === 0
        ? '<div style="padding: 2rem; color: var(--dim); text-align: center;">No papers found</div>'
        : filtered.map(renderPaper).join("");
  }
}

function renderPaper(paper) {
  const taskColor = getTaskColor(paper.task);
  const authorList = paper.authors.slice(0, 3).join(", ") + (paper.authors.length > 3 ? " +" : "");

  return `
    <article class="paper-card">
      <div class="paper-meta">
        ${paper.task ? `<span class="tag task-tag" style="color: ${taskColor};">${paper.task}</span>` : ""}
        ${paper.difficulty ? `<span class="tag diff-tag">${paper.difficulty}</span>` : ""}
      </div>
      <h2>${escapeHtml(paper.title)}</h2>
      <p class="authors">${escapeHtml(authorList)}</p>
      ${paper.summary ? `<p class="summary"><strong>Summary:</strong> ${escapeHtml(paper.summary)}</p>` : ""}
      <p class="abstract">${escapeHtml(paper.abstract.substring(0, 250))}...</p>
      <div class="paper-footer">
        <time>${new Date(paper.published).toLocaleDateString()}</time>
        <a href="https://arxiv.org/abs/${paper.id}" target="_blank" rel="noopener">View on arXiv ↗</a>
      </div>
    </article>
  `;
}

function renderTaskBar(byTask) {
  const bar = document.getElementById("task-bar");
  if (!bar) return;

  bar.innerHTML = byTask
    .filter((t) => t.task)
    .map(({ task, n }) => {
      const color = getTaskColor(task);
      return `
        <div class="task-row" style="cursor: pointer;" data-task="${task}">
          <span class="task-dot" style="background: ${color};"></span>
          <span class="task-name">${task}</span>
          <span class="task-count">${n}</span>
        </div>
      `;
    })
    .join("");

  // Add click listeners to task rows
  bar.querySelectorAll(".task-row").forEach((row) => {
    row.addEventListener("click", () => {
      const task = row.dataset.task;
      const chip = document.querySelector(`#task-chips [data-task="${task}"]`);
      if (chip) chip.click();
    });
  });
}

function getTaskColor(task) {
  const colors = {
    classification: "#c8ff00",
    generation: "#ff9f40",
    reasoning: "#4af",
    optimization: "#c084fc",
    representation: "#fb7185",
  };
  return colors[task?.toLowerCase()] || "#888";
}

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function showError(msg) {
  const container = document.querySelector("section");
  if (container) {
    container.innerHTML = `<div style="padding: 2rem; color: var(--red); text-align: center;">${escapeHtml(msg)}</div>`;
  }
}

// ── Utilities ──────────────────────────────────────────────────────────────

function debounce(fn, delay) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), delay);
  };
}
