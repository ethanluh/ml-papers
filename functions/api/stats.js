import { decodeRow } from "./_shared.js";

export async function onRequestGet(context) {
  const { env } = context;

  const total = (
    await env.DB.prepare("SELECT COUNT(*) as n FROM papers").first()
  ).n;

  const { results: byTask } = await env.DB.prepare(
    "SELECT task, COUNT(*) as n FROM papers GROUP BY task ORDER BY n DESC"
  ).all();

  const { results: byDate } = await env.DB.prepare(
    "SELECT published, COUNT(*) as n FROM papers GROUP BY published ORDER BY published DESC LIMIT 14"
  ).all();

  const { results: trendingRows } = await env.DB.prepare(
    "SELECT * FROM papers WHERE published >= date('now', '-14 days') ORDER BY published DESC LIMIT 12"
  ).all();

  const trending = trendingRows
    .map(decodeRow)
    .sort((a, b) => b.velocity - a.velocity)
    .slice(0, 6);

  return Response.json({
    total,
    by_task: byTask,
    by_date: byDate,
    trending,
  });
}
