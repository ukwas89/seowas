# streamlit_app.py (updated with heading clustering)
# -------------------------------------------------------------
# Same as before, but competitor headings are now deduplicated
# and clustered with fuzzy matching so the content brief is cleaner.
# -------------------------------------------------------------

import io
import json
import re
import time
from datetime import datetime
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup
import streamlit as st
from difflib import SequenceMatcher

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(
    page_title="SEO SERP Analyzer & Content Brief",
    page_icon="📈",
    layout="wide",
)

st.title("📈 SEO SERP Analyzer & Content Brief")
st.caption("Search a keyword via SerpAPI, analyze SERP & PAA, crawl competitor headings, and generate a clustered SEO content brief.")

SERP_API_ENDPOINT = "https://serpapi.com/search.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}

# ----------------------------
# INTENT RULES
# ----------------------------
INTENT_RULES = [
    {"label": "Transactional", "match": [r"\bbuy\b", r"price|pricing|cost", r"coupon|deal|discount", r"\bbest\b", r"\bvs\b"]},
    {"label": "Commercial", "match": [r"\bbest\b", r"\btop\b", r"review|compare", r"alternatives?", r"software|tools?"]},
    {"label": "Informational", "match": [r"what|how|why|guide|tutorial|examples?|learn|definition"]},
    {"label": "Navigational", "match": [r"login|dashboard|official|homepage|site|download"]},
]

# ----------------------------
# UTILS
# ----------------------------
def dedupe(seq: List[str]) -> List[str]:
    seen, out = set(), []
    for x in seq:
        if x and x not in seen:
            out.append(x)
            seen.add(x)
    return out

@st.cache_data(show_spinner=False, ttl=3600)
def get_serp(keyword: str, api_key: str, hl: str = "en", gl: str = "us", num: int = 10) -> Dict:
    params = {"engine": "google", "q": keyword, "num": num, "hl": hl, "gl": gl, "api_key": api_key}
    r = requests.get(SERP_API_ENDPOINT, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def infer_intent(texts: List[str]) -> Tuple[str, Dict[str, int]]:
    scores = {"Informational": 0, "Commercial": 0, "Transactional": 0, "Navigational": 0}
    for t in texts:
        if not t:
            continue
        for rule in INTENT_RULES:
            for pattern in rule["match"]:
                if re.search(pattern, t, flags=re.I):
                    scores[rule["label"]] += 1
    label = max(scores.items(), key=lambda kv: kv[1])[0]
    return label, scores

def extract_headings_from_html(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    headings = []
    for level in ["h1","h2","h3","h4","h5","h6"]:
        for tag in soup.find_all(level):
            text = " ".join(tag.get_text(" ", strip=True).split())
            if text:
                headings.append({"level": int(level[1]), "title": text})
    return headings[:600]

@st.cache_data(show_spinner=False, ttl=3600)
def crawl_url(url: str) -> List[Dict]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.ok and resp.text:
            return extract_headings_from_html(resp.text)
    except requests.RequestException:
        pass
    return []

# ----------------------------
# HEADING CLUSTERING
# ----------------------------
def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def cluster_headings(all_headings: List[str], threshold: float = 0.75) -> List[str]:
    clusters: List[List[str]] = []
    for h in all_headings:
        placed = False
        for cluster in clusters:
            if similar(h, cluster[0]) >= threshold:
                cluster.append(h)
                placed = True
                break
        if not placed:
            clusters.append([h])
    # use first heading as representative
    return [cluster[0] for cluster in clusters]

# ----------------------------
# CONTENT BRIEF BUILDER
# ----------------------------
def build_outline(keyword: str, paa: List[str], pasf: List[str], competitor_headings: List[Dict], intent_label: str) -> Dict:
    title_suffix = {
        "Informational": "Complete Guide",
        "Commercial": "Top Picks, Comparisons & FAQs",
        "Transactional": "Pricing, Options & How to Choose",
        "Navigational": "Everything You Need to Know",
    }.get(intent_label, "Complete Guide")

    title = f"{keyword}: {title_suffix}"
    meta = f"Actionable, up-to-date guide to {keyword}. Covers key questions, comparisons, and tips to match user intent."

    outline = [{"level": 1, "title": title}]

    # Gather all competitor headings and cluster them
    all_heads = [h["title"] for comp in competitor_headings for h in comp.get("headings", [])]
    clustered = cluster_headings(all_heads, threshold=0.72)

    if clustered:
        outline.append({"level": 2, "title": "Competitor Heading Themes"})
        for h in clustered:
            outline.append({"level": 3, "title": h})

    if paa:
        outline.append({"level": 2, "title": "People Also Ask"})
        for q in paa[:15]:
            outline.append({"level": 3, "title": q})

    if pasf:
        outline.append({"level": 2, "title": "People Also Search For"})
        for t in pasf[:15]:
            outline.append({"level": 3, "title": t})

    outline.append({"level": 2, "title": "Conclusion"})
    outline.append({"level": 3, "title": f"Key takeaways about {keyword}"})

    return {"title": title, "meta": meta, "outline": outline}

def outline_to_markdown(brief: Dict) -> str:
    md = f"# {brief['title']}\n\n> {brief['meta']}\n\n"
    for item in brief["outline"]:
        md += f"{'#' * item['level']} {item['title']}\n\n"
    return md

# ----------------------------
# SIDEBAR
# ----------------------------
with st.sidebar:
    st.header("Settings")
    default_key = st.secrets.get("SERPAPI_KEY", "") if hasattr(st, "secrets") else ""
    api_key = st.text_input("SerpAPI Key", type="password", value=default_key)
    keyword = st.text_input("Keyword", placeholder="e.g., best project management software")
    col1, col2 = st.columns(2)
    with col1: hl = st.text_input("hl (language)", value="en")
    with col2: gl = st.text_input("gl (country)", value="us")
    run_btn = st.button("Run Analysis", type="primary")

# ----------------------------
# MAIN
# ----------------------------
if run_btn:
    if not api_key: st.error("Please provide a SerpAPI key."); st.stop()
    if not keyword: st.error("Please enter a keyword."); st.stop()

    with st.spinner("Fetching SERP…"):
        serp = get_serp(keyword, api_key, hl=hl, gl=gl, num=10)

    organic = [{"title": o.get("title"), "snippet": o.get("snippet"), "link": o.get("link")}
               for o in (serp.get("organic_results") or [])[:10]]

    paa = dedupe([q.get("question") or q.get("title") for q in (serp.get("related_questions") or [])])
    pasf = dedupe([item.get("query") or item.get("title") for item in (serp.get("related_searches") or [])])

    st.subheader("Top 10 Organic Results")
    st.dataframe([{"#": i+1, **o} for i,o in enumerate(organic)], use_container_width=True, hide_index=True)

    if paa: st.subheader("People Also Ask"); st.write("\n".join([f"• {q}" for q in paa]))
    if pasf: st.subheader("People Also Search For"); st.write("\n".join([f"• {t}" for t in pasf]))

    texts = [keyword] + [x["title"] for x in organic] + paa + pasf
    intent_label, scores = infer_intent(texts)
    st.subheader("Intent"); st.write(f"**Dominant Intent:** {intent_label}")

    st.subheader("Crawling Competitor Pages")
    comp_results = []
    progress = st.progress(0)
    for i, item in enumerate(organic, 1):
        url = item.get("link")
        heads = crawl_url(url) if url else []
        comp_results.append({"url": url, "headings": heads})
        progress.progress(i/len(organic))

    brief = build_outline(keyword, paa, pasf, comp_results, intent_label)

    st.subheader("Content Brief (Clustered Outline)")
    md_preview = io.StringIO()
    for item in brief["outline"]:
        md_preview.write(f"{'#'*item['level']} {item['title']}\n\n")
    st.code(md_preview.getvalue(), language="markdown")

    st.download_button("⬇️ Download Markdown", data=outline_to_markdown(brief),
                       file_name=f"{re.sub(r'[^a-zA-Z0-9_-]+','-',keyword)}-brief.md")
    st.download_button("⬇️ Download JSON", data=json.dumps(brief, indent=2),
                       file_name=f"{re.sub(r'[^a-zA-Z0-9_-]+','-',keyword)}-brief.json")
