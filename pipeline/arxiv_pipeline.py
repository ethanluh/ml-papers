"""
arXiv ML paper summarization pipeline using Groq (llama-3.3-70b-versatile).
Usage:
    pip install groq requests
    export GROQ_API_KEY=your_key_here
    python arxiv_pipeline.py
"""

import os
import json
import time
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from groq import Groq

# ── Config ────────────────────────────────────────────────────────────────────

CATEGORIES = ["cs.LG", "stat.ML", "cs.AI"]
MAX_PAPERS  = 20          # keep low for testing; bump to 200 for prod
MODEL       = "llama-3.3-70b-versatile"
SLEEP_SEC   = 2.5         # stay under 30 RPM (Groq free tier)

client = Groq(api_key=os.environ["GROQ_API_KEY"])

# ── arXiv fetch ───────────────────────────────────────────────────────────────

ARXIV_NS = "http://www.w3.org/2005/Atom"

def fetch_arxiv_papers(categories: list[str], max_results: int) -> list[dict]:
    query = "+OR+".join(f"cat:{c}" for c in categories)
    url = (
        f"https://export.arxiv.org/api/query"
        f"?search_query={query}"
        f"&sortBy=submittedDate&sortOrder=descending"
        f"&max_results={max_results}"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    papers = []

    for entry in root.findall(f"{{{ARXIV_NS}}}entry"):
        arxiv_id = entry.find(f"{{{ARXIV_NS}}}id").text.strip()
        title    = entry.find(f"{{{ARXIV_NS}}}title").text.strip().replace("\n", " ")
        abstract = entry.find(f"{{{ARXIV_NS}}}summary").text.strip().replace("\n", " ")
        authors  = [
            a.find(f"{{{ARXIV_NS}}}name").text
            for a in entry.findall(f"{{{ARXIV_NS}}}author")
        ]
        published = entry.find(f"{{{ARXIV_NS}}}published").text[:10]
        categories_raw = [
            t.attrib.get("term", "")
            for t in entry.findall(f"{{{ARXIV_NS}}}category")
        ]

        papers.append({
            "id":         arxiv_id,
            "title":      title,
            "abstract":   abstract,
            "authors":    authors[:5],          # cap for display
            "published":  published,
            "categories": categories_raw,
        })

    return papers

# ── Groq summarization ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a machine learning research assistant.
Given a paper title and abstract, return ONLY valid JSON (no markdown, no preamble) with:
{
  "summary":    "2-sentence plain-English summary anyone can understand",
  "methods":    ["keyword1", "keyword2"],   // 3-5 ML technique keywords
  "task":       "one of: classification|generation|reasoning|optimization|representation|other",
  "difficulty": "beginner|intermediate|advanced",
  "tldr":       "one punchy sentence, max 15 words"
}"""

def summarize_paper(title: str, abstract: str) -> dict:
    prompt = f"Title: {title}\n\nAbstract: {abstract}"
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.2,
        max_tokens=300,
    )
    raw = response.choices[0].message.content.strip()
    # strip accidental markdown fences
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(raw)

# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline():
    print(f"[{datetime.now().isoformat()}] Fetching {MAX_PAPERS} papers from arXiv...")
    papers = fetch_arxiv_papers(CATEGORIES, MAX_PAPERS)
    print(f"  → Got {len(papers)} papers")

    results = []
    failed  = []

    for i, paper in enumerate(papers):
        print(f"  [{i+1}/{len(papers)}] {paper['title'][:70]}...")
        try:
            summary = summarize_paper(paper["title"], paper["abstract"])
            results.append({**paper, "groq": summary})
        except json.JSONDecodeError as e:
            print(f"    ✗ JSON parse error: {e}")
            failed.append(paper["id"])
        except Exception as e:
            print(f"    ✗ Error: {e}")
            failed.append(paper["id"])

        if i < len(papers) - 1:
            time.sleep(SLEEP_SEC)   # rate limit

    # ── Output ────────────────────────────────────────────────────────────────
    out_path = f"arxiv_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone. {len(results)} succeeded, {len(failed)} failed.")
    print(f"Output: {out_path}")

    # Print a sample
    if results:
        r = results[0]
        print("\n── Sample result ────────────────────────────────────")
        print(f"Title:  {r['title']}")
        print(f"TL;DR:  {r['groq']['tldr']}")
        print(f"Summary: {r['groq']['summary']}")
        print(f"Task:   {r['groq']['task']}")
        print(f"Methods: {', '.join(r['groq']['methods'])}")

    return results

if __name__ == "__main__":
    run_pipeline()