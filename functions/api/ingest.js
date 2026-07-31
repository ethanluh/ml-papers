// Authenticated write endpoint for the daily GitHub Actions ingestion job.
// Accepts the JSON array produced by pipeline/arxiv_pipeline.py's run_pipeline(),
// and upserts each paper into D1 using bound prepared statements (no SQL-string
// escaping, unlike a wrangler d1 execute --file approach).

function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return result === 0;
}

export async function onRequestPost(context) {
  const { env, request } = context;

  const token = request.headers.get("X-Ingest-Token") || "";
  if (!env.INGEST_TOKEN || !timingSafeEqual(token, env.INGEST_TOKEN)) {
    return new Response("Unauthorized", { status: 401 });
  }

  let papers;
  try {
    papers = await request.json();
  } catch {
    return new Response("Invalid JSON body", { status: 400 });
  }
  if (!Array.isArray(papers)) {
    return new Response("Expected a JSON array of papers", { status: 400 });
  }

  const now = new Date().toISOString();
  const statements = [];

  for (const paper of papers) {
    const groq = paper.groq || {};
    const authors = JSON.stringify(paper.authors || []);
    const categories = JSON.stringify(paper.categories || []);
    const methods = JSON.stringify(groq.methods || []);

    statements.push(
      env.DB.prepare(
        `INSERT INTO papers
            (id, title, abstract, authors, published, categories,
             summary, tldr, task, difficulty, methods, inserted_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)
         ON CONFLICT(id) DO UPDATE SET
            title       = excluded.title,
            abstract    = excluded.abstract,
            authors     = excluded.authors,
            published   = excluded.published,
            categories  = excluded.categories,
            summary     = excluded.summary,
            tldr        = excluded.tldr,
            task        = excluded.task,
            difficulty  = excluded.difficulty,
            methods     = excluded.methods,
            inserted_at = excluded.inserted_at`
      ).bind(
        paper.id,
        paper.title,
        paper.abstract,
        authors,
        paper.published,
        categories,
        groq.summary ?? null,
        groq.tldr ?? null,
        groq.task ?? null,
        groq.difficulty ?? null,
        methods,
        now
      )
    );

    statements.push(
      env.DB.prepare("DELETE FROM papers_fts WHERE id = ?1").bind(paper.id)
    );

    statements.push(
      env.DB.prepare(
        `INSERT INTO papers_fts (id, title, abstract, summary, tldr)
         VALUES (?1, ?2, ?3, ?4, ?5)`
      ).bind(paper.id, paper.title, paper.abstract, groq.summary ?? null, groq.tldr ?? null)
    );
  }

  if (statements.length > 0) {
    await env.DB.batch(statements);
  }

  return Response.json({ stored: papers.length });
}
