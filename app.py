# streamlit_app.py (with adjustable heading clustering threshold)
# -----------------------------------------------------------------
# Added a sidebar slider to adjust heading clustering similarity.
# -----------------------------------------------------------------

import io
import json
import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup
import streamlit as st

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(
    page_title="SEO SERP Analyzer & Content Brief",
    page_icon="📈",
    layout="wide",
)

st.title("📈 SEO SERP Analyzer & Content Brief")
st.caption("Analyze SERP & competitors, cluster headings, and build an SEO content brief.")

SERP_API_ENDPOINT = "https://serpapi.com/search.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}

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
    return [cluster[0] for cluster in clusters]

# ----------------------------
# CONTENT BRIEF BUILDER
# ----------------------------
def build_outline(keyword: str, paa: List[str], pasf: List[str], competitor_headings: List[Dict], threshold: float) -> Dict:
    outline = [{"level": 1, "title": f"{keyword}: Complete Guide"}]

    # Gather competitor headings and cluster them
    all_heads = [h["title"] for comp in competitor_headings for h in comp.get("headings", [])]
    clustered = cluster_headings(all_heads, threshold)

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

    return {"title": f"{keyword}: Content Brief", "outline": outline}

def outline_to_markdown(brief: Dict) -> str:
    md = f"# {brief['title']}\n\n"
    for item in brief["outline"]:
        md += f"{'#' * item['level']} {item['title']}\n\n"
    return md

# ----------------------------
# SIDEBAR
# ----------------------------
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("SerpAPI Key", type="password", value=st.secrets.get("SERPAPI_KEY", ""))
    keyword = st.text_input("Keyword", placeholder="e.g., best project management software")
    col1, col2 = st.columns(2)
    with col1: hl = st.text_input("hl (language)", value="en")
    with col2: gl = st.text_input("gl (country)", value="us")
    threshold = st.slider("Heading Cluster Threshold", min_value=0.5, max_value=0.95, value=0.75, step=0.01)
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

    st.subheader("Crawling Competitor Pages")
    comp_results = []
    progress = st.progress(0)
    for i, item in enumerate(organic, 1):
        url = item.get("link")
        heads = crawl_url(url) if url else []
        comp_results.append({"url": url, "headings": heads})
        progress.progress(i/len(organic))

    brief = build_outline(keyword, paa, pasf, comp_results, threshold)

    st.subheader("Content Brief (Clustered Outline)")
    st.code(outline_to_markdown(brief), language="markdown")

    st.download_button("⬇️ Download Markdown", data=outline_to_markdown(brief),
                       file_name=f"{re.sub(r'[^a-zA-Z0-9_-]+','-',keyword)}-brief.md")
    st.download_button("⬇️ Download JSON", data=json.dumps(brief, indent=2),
                       file_name=f"{re.sub(r'[^a-zA-Z0-9_-]+','-',keyword)}-brief.json")
