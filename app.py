# streamlit_app.py
# -------------------------------------------------------------
# SEO SERP Analyzer & Content Brief — Streamlit app
#
# Features
# 1) Query Google via SerpAPI for a given keyword (top 10 + PAA + PASF)
# 2) Analyze current SERP & infer dominant intent
# 3) Crawl each ranking page and extract H1–H6
# 4) Compile a data-driven, SEO-optimized content brief outline
# 5) Export brief as Markdown or JSON
#
# Deployment
# - Add your SerpAPI key to Streamlit Secrets (recommended):
#   In Streamlit Cloud, set a secret named SERPAPI_KEY.
#   Locally, create .streamlit/secrets.toml with: SERPAPI_KEY = "YOUR_KEY"
#
# - Run locally:  streamlit run streamlit_app.py
# - Required packages (see bottom of file for requirements list)
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

# ----------------------------
# UI CONFIG
# ----------------------------
st.set_page_config(
    page_title="SEO SERP Analyzer & Content Brief",
    page_icon="📈",
    layout="wide",
)

st.title("📈 SEO SERP Analyzer & Content Brief")
st.caption(
    "Search a keyword via SerpAPI, analyze the SERP & PAA, crawl competitor headings, and generate a data-driven content brief."
)

# ----------------------------
# HELPERS & CONSTANTS
# ----------------------------
SERP_API_ENDPOINT = "https://serpapi.com/search.json"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

INTENT_RULES = [
    {"label": "Transactional", "match": [r"\bbuy\b", r"price|pricing|cost", r"coupon|deal|discount", r"\bbest\b", r"\bvs\b"]},
    {"label": "Commercial", "match": [r"\bbest\b", r"\btop\b", r"review|compare", r"alternatives?", r"software|tools?"]},
    {"label": "Informational", "match": [r"what|how|why|guide|tutorial|examples?|learn|definition"]},
    {"label": "Navigational", "match": [r"login|dashboard|official|homepage|site|download"]},
]

HEADERS = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}


def dedupe(seq: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in seq:
        if x and x not in seen:
            out.append(x)
            seen.add(x)
    return out


@st.cache_data(show_spinner=False, ttl=3600)
def get_serp(keyword: str, api_key: str, hl: str = "en", gl: str = "us", num: int = 10) -> Dict:
    """Fetch Google SERP via SerpAPI."""
    params = {
        "engine": "google",
        "q": keyword,
        "num": num,
        "hl": hl,
        "gl": gl,
        "api_key": api_key,
    }
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
    # Pick highest
    label = max(scores.items(), key=lambda kv: kv[1])[0]
    return label, scores


def extract_headings_from_html(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    headings = []
    for level in ["h1", "h2", "h3", "h4", "h5", "h6"]:
        for tag in soup.find_all(level):
            text = " ".join(tag.get_text(" ", strip=True).split())
            if text:
                headings.append({"level": int(level[1]), "title": text})
    return headings[:600]


@st.cache_data(show_spinner=False, ttl=3600)
def crawl_url(url: str) -> List[Dict]:
    """Fetch a page and extract H1–H6 headings. Resilient to common issues."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        if resp.status_code >= 400:
            alt_headers = HEADERS.copy()
            alt_headers["User-Agent"] = USER_AGENT.replace("Chrome/124", "Chrome/120")
            resp = requests.get(url, headers=alt_headers, timeout=20)
        if resp.ok and resp.text:
            return extract_headings_from_html(resp.text)
    except requests.RequestException:
        pass

    # Fallback: Jina Reader
    try:
        reader_url = f"https://r.jina.ai/http/{url}"
        r = requests.get(reader_url, headers={"User-Agent": USER_AGENT}, timeout=20)
        if r.ok and r.text:
            lines = r.text.split("\n")
            heads = []
            for line in lines:
                m = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
                if m:
                    level = len(m.group(1))
                    title = m.group(2).strip().strip("# ")
                    heads.append({"level": level, "title": title})
            if heads:
                return heads[:600]
    except requests.RequestException:
        pass

    return []


def build_outline(keyword: str, paa: List[str], pasf: List[str], competitor_headings: List[Dict], intent_label: str) -> Dict:
    # Title & Meta
    title_suffix = {
        "Informational": "Complete Guide",
        "Commercial": "Top Picks, Comparisons & FAQs",
        "Transactional": "Pricing, Options & How to Choose",
        "Navigational": "Everything You Need to Know",
    }.get(intent_label, "Complete Guide")

    title = f"{keyword}: {title_suffix}"
    meta = f"Actionable, up-to-date guide to {keyword}. Covers key questions, comparisons, and tips to match user intent."

    outline = [{"level": 1, "title": title}]

    # Add competitor headings (H1–H6)
    for comp in competitor_headings:
        url = comp.get("url")
        heads = comp.get("headings", [])
        if heads:
            outline.append({"level": 2, "title": f"Competitor Outline from {url}"})
            for h in heads:
                outline.append({"level": min(h.get("level", 2) + 1, 6), "title": h.get("title", "")})

    # Add People Also Ask
    if paa:
        outline.append({"level": 2, "title": "People Also Ask"})
        for q in paa[:15]:
            outline.append({"level": 3, "title": q})

    # Add People Also Search For
    if pasf:
        outline.append({"level": 2, "title": "People Also Search For"})
        for term in pasf[:15]:
            outline.append({"level": 3, "title": term})

    outline.append({"level": 2, "title": "Conclusion"})
    outline.append({"level": 3, "title": f"Key takeaways about {keyword}"})

    return {"title": title, "meta": meta, "outline": outline}


def outline_to_markdown(brief: Dict) -> str:
    md = f"# {brief['title']}\n\n> {brief['meta']}\n\n"
    for item in brief["outline"]:
        md += f"{'#' * item['level']} {item['title']}\n\n"
    return md


# ----------------------------
# SIDEBAR CONTROLS
# ----------------------------
with st.sidebar:
    st.header("Settings")

    default_key = st.secrets.get("SERPAPI_KEY", "") if hasattr(st, "secrets") else ""
    api_key = st.text_input("SerpAPI Key", type="password", value=default_key)

    keyword = st.text_input("Keyword", placeholder="e.g., best project management software")

    col1, col2 = st.columns(2)
    with col1:
        hl = st.text_input("hl (language)", value="en")
    with col2:
        gl = st.text_input("gl (country)", value="us")

    run_btn = st.button("Run Analysis", type="primary")

    st.markdown("---")
    st.caption("For production: add SERPAPI_KEY in secrets. Crawling is server-side here.")

# ----------------------------
# MAIN WORKFLOW
# ----------------------------
if run_btn:
    if not api_key:
        st.error("Please provide a SerpAPI key (in sidebar).")
        st.stop()
    if not keyword:
        st.error("Please enter a keyword.")
        st.stop()

    with st.spinner("Fetching SERP from SerpAPI…"):
        try:
            serp = get_serp(keyword, api_key, hl=hl, gl=gl, num=10)
        except requests.HTTPError as e:
            st.error(f"SerpAPI error: {e}")
            st.stop()
        except Exception as e:
            st.error(f"Unexpected error calling SerpAPI: {e}")
            st.stop()

    organic = [
        {"title": o.get("title"), "snippet": o.get("snippet") or " ".join(o.get("snippet_highlighted_words", []) or []), "link": o.get("link")}
        for o in (serp.get("organic_results") or [])[:10]
    ]

    paa_candidates = []
    for k in ("related_questions", "people_also_ask"):
        for q in (serp.get(k) or []):
            qtext = q.get("question") or q.get("title")
            if qtext:
                paa_candidates.append(qtext)
    paa = dedupe(paa_candidates)

    pasf_candidates = []
    for k in ("related_searches", "people_also_search_for"):
        for item in (serp.get(k) or []):
            term = item.get("query") or item.get("title")
            if term:
                pasf_candidates.append(term)
    pasf = dedupe(pasf_candidates)

    st.subheader("Top 10 Organic Results")
    if organic:
        st.dataframe([{"#": i + 1, **o} for i, o in enumerate(organic)], use_container_width=True, hide_index=True)
    else:
        st.info("No organic results were returned by SerpAPI.")

    if paa:
        st.subheader("People Also Ask (PAA)")
        st.write("\n".join([f"• {q}" for q in paa]))

    if pasf:
        st.subheader("People Also Search For (PASF)")
        st.write("\n".join([f"• {t}" for t in pasf]))

    texts = [keyword] + [x["title"] for x in organic if x.get("title")] + [x.get("snippet", "") for x in organic] + paa + pasf
    intent_label, scores = infer_intent(texts)

    st.subheader("Intent (heuristic)")
    cols = st.columns(4)
    for i, name in enumerate(["Informational", "Commercial", "Transactional", "Navigational"]):
        cols[i].metric(name, scores.get(name, 0))
    st.markdown(f"**Dominant Intent:** {intent_label}")

    st.subheader("Crawling Competitor Pages (H1–H6)")
    comp_results = []
    progress = st.progress(0)
    status = st.empty()
    total = len(organic)
    for i, item in enumerate(organic, start=1):
        url = item.get("link")
        status.write(f"Fetching: {url}")
        heads = crawl_url(url) if url else []
        comp_results.append({"url": url, "headings": heads})
        progress.progress(i / max(total, 1))
        time.sleep(0.1)
    status.write("Done.")

    for comp in comp_results:
        with st.expander(f"{comp['url']}  —  {len(comp['headings'])} headings"):
            if comp["headings"]:
                st.dataframe(comp["headings"], use_container_width=True, hide_index=True)
            else:
                st.write("No headings found or page blocked crawling.")

    brief = build_outline(keyword, paa, pasf, comp_results, intent_label)

    st.subheader("Content Brief (Outline)")
    st.markdown(f"### {brief['title']}")
    st.markdown(f"> {brief['meta']}")

    md_preview = io.StringIO()
    for item in brief["outline"]:
        md_preview.write(f"{'#' * item['level']} {item['title']}\n\n")
    st.code(md_preview.getvalue(), language="markdown")

    md = outline_to_markdown(brief)
    payload = {
        "keyword": keyword,
        "intent": {"label": intent_label, "scores": scores},
        "results": organic,
        "paa": paa,
        "pasf": pasf,
        "competitor_headings": comp_results,
        "brief": brief,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }

    st.download_button(
        "⬇️ Download Markdown",
        data=md,
        file_name=f"{re.sub(r'[^a-zA-Z0-9_-]+', '-', keyword.strip())}-brief.md",
        mime="text/markdown",
    )
    st.download_button(
        "⬇️ Download JSON",
        data=json.dumps(payload, indent=2),
        file_name=f"{re.sub(r'[^a-zA-Z0-9_-]+', '-', keyword.strip())}-brief.json",
        mime="application/json",
    )

    st.success("Brief generated with H1–H6, PAA, and PASF.")

# -------------------------------------------------------------
# requirements.txt
# -------------------------------------------------------------
# streamlit
# requests
# beautifulsoup4
