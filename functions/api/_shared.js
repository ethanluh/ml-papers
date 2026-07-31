// Shared helpers for the papers/stats/ingest Pages Functions.

export function computeVelocity(published) {
  const pub = new Date(`${published}T00:00:00Z`);
  if (isNaN(pub.getTime())) return 0.0;

  const ageDays = Math.floor((Date.now() - pub.getTime()) / 86400000);
  const score = Math.max(0, (14 - Math.min(ageDays, 14)) / 14);
  return Math.round(score * 1000) / 1000;
}

export function normalizeSearch(text) {
  return text.replace(/"/g, " ").trim();
}

export function decodeRow(row) {
  return {
    ...row,
    authors: JSON.parse(row.authors),
    categories: JSON.parse(row.categories),
    methods: JSON.parse(row.methods || "[]"),
    velocity: computeVelocity(row.published),
  };
}
