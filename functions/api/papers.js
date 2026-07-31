import { decodeRow, normalizeSearch } from "./_shared.js";

export async function onRequestGet(context) {
  const { env, request } = context;
  const url = new URL(request.url);
  const params = url.searchParams;

  const task = params.get("task");
  const difficulty = params.get("difficulty");
  const search = params.get("search");
  const limit = Math.min(parseInt(params.get("limit") || "50", 10), 200);
  const offset = parseInt(params.get("offset") || "0", 10);

  let query;
  const bind = [];

  if (search) {
    query = "SELECT p.* FROM papers p JOIN papers_fts f ON f.id = p.id WHERE f MATCH ?1";
    bind.push(normalizeSearch(search));
  } else {
    query = "SELECT * FROM papers WHERE 1=1";
  }

  if (task) {
    bind.push(task);
    query += ` AND task = ?${bind.length}`;
  }
  if (difficulty) {
    bind.push(difficulty);
    query += ` AND difficulty = ?${bind.length}`;
  }

  bind.push(limit, offset);
  query += ` ORDER BY published DESC LIMIT ?${bind.length - 1} OFFSET ?${bind.length}`;

  const { results } = await env.DB.prepare(query).bind(...bind).all();
  return Response.json(results.map(decodeRow));
}
