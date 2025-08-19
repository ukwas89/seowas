import streamlit as st
import sys
import importlib
import json
import re
import time
from collections import Counter
from urllib.parse import urlparse

# Check for required packages and install if missing
required_packages = {
    'bs4': 'beautifulsoup4',
    'requests': 'requests',
    'pandas': 'pandas'
}

missing_packages = []

for import_name, package_name in required_packages.items():
    try:
        importlib.import_module(import_name)
    except ImportError:
        missing_packages.append(package_name)

if missing_packages:
    st.error(f"The following packages are required but not installed: {', '.join(missing_packages)}")
    st.error("Please install them using pip:")
    for package in missing_packages:
        st.code(f"pip install {package}")
    st.stop()

# Now import the required packages
from bs4 import BeautifulSoup
import requests
import pandas as pd

# Set page configuration
st.set_page_config(
    page_title="SEO Content Brief Generator",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .intent-card {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .outline-card {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .faq-card {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .keyword-highlight {
        background-color: #FFEB3B;
        padding: 0.2rem 0.4rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class SEOContentBriefGenerator:
    def __init__(self, serpapi_key):
        self.serpapi_key = serpapi_key
        self.serp_results = None
        self.competitor_headings = {}
        
    def collect_serp_data(self, keyword, location="us", gl="us", hl="en"):
        params = {
            "engine": "google",
            "q": keyword,
            "location": location,
            "gl": gl,
            "hl": hl,
            "api_key": self.serpapi_key,
            "num": 10
        }
        
        try:
            response = requests.get("https://serpapi.com/search", params=params)
            response.raise_for_status()
            search = response.json()
            self.serp_results = search
            
            organic_results = search.get("organic_results", [])[:10]
            
            paa_questions = []
            related_questions = search.get("related_questions", [])
            for question in related_questions:
                paa_questions.append(question.get("question", ""))
            
            serp_data = {
                "keyword": keyword,
                "organic_results": [],
                "paa_questions": paa_questions
            }
            
            for result in organic_results:
                serp_data["organic_results"].append({
                    "title": result.get("title", ""),
                    "meta_description": result.get("snippet", ""),
                    "url": result.get("link", ""),
                    "position": result.get("position", 0)
                })
            
            return serp_data
            
        except Exception as e:
            st.error(f"Error collecting SERP data: {e}")
            return None
    
    def analyze_search_intent(self, serp_data):
        if not serp_data:
            return None
            
        intent_keywords = {
            "informational": ["how to", "what is", "why", "guide", "tutorial", "ways to", "tips", "learn"],
            "commercial": ["best", "review", "comparison", "vs", "top", "rating", "buy"],
            "transactional": ["buy", "purchase", "order", "deal", "discount", "cheap", "price"],
            "navigational": ["login", "signin", "official", "website", "app", "download"]
        }
        
        intent_scores = {intent: 0 for intent in intent_keywords}
        
        for result in serp_data["organic_results"]:
            text_to_analyze = (result["title"] + " " + result["meta_description"]).lower()
            
            for intent, keywords in intent_keywords.items():
                for keyword in keywords:
                    if keyword in text_to_analyze:
                        intent_scores[intent] += 1
        
        dominant_intent = max(intent_scores, key=intent_scores.get)
        
        all_titles = [result["title"] for result in serp_data["organic_results"]]
        all_descriptions = [result["meta_description"] for result in serp_data["organic_results"]]
        
        title_words = " ".join(all_titles).lower()
        title_words = re.findall(r'\b\w+\b', title_words)
        title_word_freq = Counter(title_words).most_common(10)
        
        desc_words = " ".join(all_descriptions).lower()
        desc_words = re.findall(r'\b\w+\b', desc_words)
        desc_word_freq = Counter(desc_words).most_common(10)
        
        url_patterns = []
        for result in serp_data["organic_results"]:
            parsed_url = urlparse(result["url"])
            path_parts = [part for part in parsed_url.path.split('/') if part]
            if path_parts:
                url_patterns.extend(path_parts)
        
        url_pattern_freq = Counter(url_patterns).most_common(5)
        
        return {
            "dominant_intent": dominant_intent,
            "intent_scores": intent_scores,
            "common_title_words": title_word_freq,
            "common_description_words": desc_word_freq,
            "common_url_patterns": url_pattern_freq,
            "paa_questions": serp_data["paa_questions"]
        }
    
    def extract_headings_from_url(self, url):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            headings = {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []}
            
            for level in headings:
                for heading in soup.find_all(level):
                    text = heading.get_text().strip()
                    if text:
                        headings[level].append(text)
            
            return headings
            
        except Exception as e:
            st.warning(f"Error extracting headings from {url}: {e}")
            return {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []}
    
    def extract_competitor_headings(self, serp_data):
        if not serp_data:
            return None
            
        competitor_headings = {}
        
        for result in serp_data["organic_results"]:
            url = result["url"]
            with st.spinner(f"Extracting headings from: {url}"):
                headings = self.extract_headings_from_url(url)
                competitor_headings[url] = headings
                time.sleep(1)  # Add delay to avoid overwhelming servers
            
        self.competitor_headings = competitor_headings
        return competitor_headings
    
    def analyze_competitor_headings(self):
        if not self.competitor_headings:
            return None
            
        all_headings = {"h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []}
        
        for url, headings in self.competitor_headings.items():
            for level in all_headings:
                all_headings[level].extend(headings[level])
        
        common_headings = {}
        for level in all_headings:
            if all_headings[level]:
                heading_freq = Counter(all_headings[level]).most_common(10)
                common_headings[level] = heading_freq
        
        return {
            "all_headings": all_headings,
            "common_headings": common_headings
        }
    
    def generate_content_brief(self, keyword, serp_data, intent_analysis, headings_analysis):
        if not serp_data or not intent_analysis:
            return None
            
        title_suggestion = self._generate_title_suggestion(keyword, intent_analysis)
        meta_description_suggestion = self._generate_meta_description_suggestion(keyword, intent_analysis)
        content_outline = self._generate_content_outline(keyword, intent_analysis, headings_analysis)
        faq_section = self._generate_faq_section(intent_analysis["paa_questions"])
        key_topics = self._extract_key_topics(intent_analysis, headings_analysis)
        
        content_brief = {
            "keyword": keyword,
            "title_suggestion": title_suggestion,
            "meta_description_suggestion": meta_description_suggestion,
            "search_intent_analysis": {
                "dominant_intent": intent_analysis["dominant_intent"],
                "intent_scores": intent_analysis["intent_scores"]
            },
            "content_outline": content_outline,
            "faq_section": faq_section,
            "key_topics": key_topics,
            "serp_patterns": {
                "common_title_words": intent_analysis["common_title_words"],
                "common_description_words": intent_analysis["common_description_words"],
                "common_url_patterns": intent_analysis["common_url_patterns"]
            },
            "competitor_insights": {
                "common_headings": headings_analysis["common_headings"] if headings_analysis else {}
            }
        }
        
        return content_brief
    
    def _generate_title_suggestion(self, keyword, intent_analysis):
        dominant_intent = intent_analysis["dominant_intent"]
        
        power_words = {
            "informational": ["Ultimate", "Complete", "Comprehensive", "Definitive", "Essential"],
            "commercial": ["Best", "Top", "Premium", "Review", "Comparison"],
            "transactional": ["Buy", "Purchase", "Deal", "Discount", "Affordable"],
            "navigational": ["Official", "Login", "Access", "Download", "Sign Up"]
        }
        
        power_word = power_words.get(dominant_intent, ["Guide"])[0]
        
        title_suggestion = f"{power_word} Guide to {keyword}: Everything You Need to Know"
        
        common_words = [word for word, count in intent_analysis["common_title_words"][:3] 
                       if word.lower() not in [kw.lower() for kw in keyword.split()]]
        
        if common_words:
            title_suggestion = f"{power_word} {common_words[0].title()} for {keyword}: {common_words[1].title() if len(common_words) > 1 else 'Complete'} Guide"
        
        return title_suggestion
    
    def _generate_meta_description_suggestion(self, keyword, intent_analysis):
        dominant_intent = intent_analysis["dominant_intent"]
        
        common_words = [word for word, count in intent_analysis["common_description_words"][:5]]
        
        if dominant_intent == "informational":
            meta_desc = f"Looking for information about {keyword}? Our comprehensive guide covers everything you need to know. Learn about {', '.join(common_words[:3])} and more."
        elif dominant_intent == "commercial":
            meta_desc = f"Searching for the best {keyword}? We've reviewed and compared the top options. Find out which {common_words[0] if common_words else 'product'} is right for you."
        elif dominant_intent == "transactional":
            meta_desc = f"Ready to buy {keyword}? Find the best deals and prices on {common_words[0] if common_words else 'quality products'}. Shop now and save!"
        else:  # navigational
            meta_desc = f"Looking for the official {keyword} website? Find direct access to {', '.join(common_words[:2]) if common_words else 'the resources you need'} here."
        
        if len(meta_desc) > 160:
            meta_desc = meta_desc[:157] + "..."
        
        return meta_desc
    
    def _generate_content_outline(self, keyword, intent_analysis, headings_analysis):
        dominant_intent = intent_analysis["dominant_intent"]
        
        common_h2s = []
        if headings_analysis and "common_headings" in headings_analysis and "h2" in headings_analysis["common_headings"]:
            common_h2s = [heading for heading, count in headings_analysis["common_headings"]["h2"][:5]]
        
        outline = {
            "h1": f"The Ultimate Guide to {keyword}",
            "sections": []
        }
        
        outline["sections"].append({
            "h2": "Introduction to " + keyword,
            "content": "Brief overview of what the article will cover and why the topic is important."
        })
        
        if dominant_intent == "informational":
            outline["sections"].extend([
                {
                    "h2": "What Is " + keyword + "?",
                    "content": "Definition and basic explanation of the concept.",
                    "subsections": [
                        {"h3": "Key Components of " + keyword, "content": "Break down the main elements."},
                        {"h3": "How " + keyword + " Works", "content": "Explanation of the mechanism or process."}
                    ]
                },
                {
                    "h2": "Benefits of " + keyword,
                    "content": "List and explain the main advantages.",
                    "subsections": [
                        {"h3": "Primary Benefits", "content": "Most important advantages."},
                        {"h3": "Secondary Benefits", "content": "Additional advantages."}
                    ]
                },
                {
                    "h2": "Common Challenges with " + keyword,
                    "content": "Discuss potential issues and how to overcome them."
                }
            ])
            
            for h2 in common_h2s:
                if not any(section["h2"] == h2 for section in outline["sections"]):
                    outline["sections"].append({
                        "h2": h2,
                        "content": "Cover this important aspect of " + keyword
                    })
            
            outline["sections"].append({
                "h2": "Conclusion",
                "content": "Summarize key points and provide final thoughts."
            })
            
        elif dominant_intent == "commercial":
            outline["sections"].extend([
                {
                    "h2": "Top " + keyword + " Options",
                    "content": "Overview of the best products/services in this category.",
                    "subsections": [
                        {"h3": "Best Overall", "content": "Top recommendation and why."},
                        {"h3": "Best Value", "content": "Best option for the price."},
                        {"h3": "Premium Choice", "content": "High-end option for those with bigger budgets."}
                    ]
                },
                {
                    "h2": "Comparison of " + keyword + " Features",
                    "content": "Side-by-side comparison of key features.",
                    "subsections": [
                        {"h3": "Feature Comparison Table", "content": "Visual comparison of products."},
                        {"h3": "Performance Analysis", "content": "How each option performs."}
                    ]
                },
                {
                    "h2": "Pros and Cons",
                    "content": "Detailed list of advantages and disadvantages for each option."
                }
            ])
            
            for h2 in common_h2s:
                if not any(section["h2"] == h2 for section in outline["sections"]):
                    outline["sections"].append({
                        "h2": h2,
                        "content": "Cover this important aspect of " + keyword
                    })
            
            outline["sections"].append({
                "h2": "Final Recommendation",
                "content": "Clear recommendation based on different use cases and needs."
            })
            
        elif dominant_intent == "transactional":
            outline["sections"].extend([
                {
                    "h2": "Where to Buy " + keyword,
                    "content": "Best places to purchase this product/service.",
                    "subsections": [
                        {"h3": "Official Retailers", "content": "Authorized sellers."},
                        {"h3": "Online Marketplaces", "content": "E-commerce options."}
                    ]
                },
                {
                    "h2": "Current Deals and Discounts",
                    "content": "Latest promotions and special offers.",
                    "subsections": [
                        {"h3": "Seasonal Sales", "content": "Holiday and event-based discounts."},
                        {"h3": "Coupon Codes", "content": "Available promo codes."}
                    ]
                },
                {
                    "h2": "Price Comparison",
                    "content": "Compare prices across different retailers."
                }
            ])
            
            for h2 in common_h2s:
                if not any(section["h2"] == h2 for section in outline["sections"]):
                    outline["sections"].append({
                        "h2": h2,
                        "content": "Cover this important aspect of " + keyword
                    })
            
            outline["sections"].append({
                "h2": "Best Value for Money",
                "content": "Final recommendation on where to get the best deal."
            })
            
        else:  # navigational
            outline["sections"].extend([
                {
                    "h2": "How to Access " + keyword,
                    "content": "Step-by-step instructions to reach the destination.",
                    "subsections": [
                        {"h3": "Direct Link", "content": "Official URL."},
                        {"h3": "Alternative Access Methods", "content": "Other ways to reach the site/service."}
                    ]
                },
                {
                    "h2": "Account Setup",
                    "content": "How to create an account if needed."
                },
                {
                    "h2": "Troubleshooting Access Issues",
                    "content": "Common problems and solutions."
                }
            ])
            
            for h2 in common_h2s:
                if not any(section["h2"] == h2 for section in outline["sections"]):
                    outline["sections"].append({
                        "h2": h2,
                        "content": "Cover this important aspect of " + keyword
                    })
            
            outline["sections"].append({
                "h2": "Getting Started",
                "content": "Next steps after accessing the site/service."
            })
        
        return outline
    
    def _generate_faq_section(self, paa_questions):
        if not paa_questions:
            return {"h2": "Frequently Asked Questions", "questions": []}
        
        faq_section = {
            "h2": "Frequently Asked Questions",
            "questions": []
        }
        
        for question in paa_questions[:5]:
            faq_section["questions"].append({
                "question": question,
                "answer": "Provide a comprehensive answer to this question based on research and expertise."
            })
        
        return faq_section
    
    def _extract_key_topics(self, intent_analysis, headings_analysis):
        key_topics = []
        
        title_words = [word for word, count in intent_analysis["common_title_words"][:5]]
        key_topics.extend(title_words)
        
        desc_words = [word for word, count in intent_analysis["common_description_words"][:5]]
        key_topics.extend(desc_words)
        
        if headings_analysis and "common_headings" in headings_analysis and "h2" in headings_analysis["common_headings"]:
            common_h2s = [heading for heading, count in headings_analysis["common_headings"]["h2"][:5]]
            key_topics.extend(common_h2s)
        
        return list(set(key_topics))
    
    def generate_seo_content_brief(self, keyword):
        st.write(f"Generating SEO content brief for keyword: **{keyword}**")
        
        # Step 1: Collect SERP data
        with st.spinner("Step 1: Collecting SERP data..."):
            serp_data = self.collect_serp_data(keyword)
            if not serp_data:
                st.error("Failed to collect SERP data.")
                return None
        
        # Step 2: Analyze search intent
        with st.spinner("Step 2: Analyzing search intent..."):
            intent_analysis = self.analyze_search_intent(serp_data)
        
        # Step 4: Extract competitor headings
        with st.spinner("Step 4: Extracting competitor headings..."):
            competitor_headings = self.extract_competitor_headings(serp_data)
        
        # Analyze competitor headings
        with st.spinner("Analyzing competitor headings..."):
            headings_analysis = self.analyze_competitor_headings()
        
        # Step 3 & 5: Generate content brief
        with st.spinner("Step 3 & 5: Generating content brief..."):
            content_brief = self.generate_content_brief(keyword, serp_data, intent_analysis, headings_analysis)
        
        st.success("SEO content brief generated successfully!")
        return content_brief

def display_content_brief(content_brief):
    if not content_brief:
        return
    
    # Display title and meta description
    st.markdown('<div class="section-header">Title & Meta Description</div>', unsafe_allow_html=True)
    st.markdown(f"**Suggested Title:**\n\n> {content_brief['title_suggestion']}")
    st.markdown(f"**Suggested Meta Description:**\n\n> {content_brief['meta_description_suggestion']}")
    
    # Display search intent analysis
    st.markdown('<div class="section-header">Search Intent Analysis</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="intent-card">', unsafe_allow_html=True)
        st.markdown(f"**Dominant Intent:** {content_brief['search_intent_analysis']['dominant_intent'].title()}")
        
        st.markdown("**Intent Scores:**")
        intent_df = pd.DataFrame(
            list(content_brief['search_intent_analysis']['intent_scores'].items()),
            columns=['Intent Type', 'Score']
        )
        st.bar_chart(intent_df.set_index('Intent Type'))
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Display content outline
    st.markdown('<div class="section-header">Content Outline</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="outline-card">', unsafe_allow_html=True)
        st.markdown(f"### {content_brief['content_outline']['h1']}")
        
        for section in content_brief['content_outline']['sections']:
            st.markdown(f"#### {section['h2']}")
            st.write(section['content'])
            
            if 'subsections' in section:
                for subsection in section['subsections']:
                    st.markdown(f"##### {subsection['h3']}")
                    st.write(subsection['content'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Display FAQ section
    st.markdown('<div class="section-header">FAQ Section</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="faq-card">', unsafe_allow_html=True)
        st.markdown(f"### {content_brief['faq_section']['h2']}")
        
        for qa in content_brief['faq_section']['questions']:
            st.markdown(f"**Q:** {qa['question']}")
            st.markdown(f"**A:** {qa['answer']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Display key topics
    st.markdown('<div class="section-header">Key Topics to Cover</div>', unsafe_allow_html=True)
    topics_df = pd.DataFrame(content_brief['key_topics'], columns=['Key Topics'])
    st.dataframe(topics_df)
    
    # Display SERP patterns
    st.markdown('<div class="section-header">SERP Patterns</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Common Title Words**")
        title_words_df = pd.DataFrame(
            content_brief['serp_patterns']['common_title_words'],
            columns=['Word', 'Frequency']
        )
        st.dataframe(title_words_df)
    
    with col2:
        st.markdown("**Common Description Words**")
        desc_words_df = pd.DataFrame(
            content_brief['serp_patterns']['common_description_words'],
            columns=['Word', 'Frequency']
        )
        st.dataframe(desc_words_df)
    
    with col3:
        st.markdown("**Common URL Patterns**")
        url_patterns_df = pd.DataFrame(
            content_brief['serp_patterns']['common_url_patterns'],
            columns=['Pattern', 'Frequency']
        )
        st.dataframe(url_patterns_df)
    
    # Display competitor insights
    st.markdown('<div class="section-header">Competitor Insights</div>', unsafe_allow_html=True)
    
    if 'h2' in content_brief['competitor_insights']['common_headings']:
        st.markdown("**Common H2 Headings**")
        h2_df = pd.DataFrame(
            content_brief['competitor_insights']['common_headings']['h2'],
            columns=['Heading', 'Frequency']
        )
        st.dataframe(h2_df)
    
    if 'h3' in content_brief['competitor_insights']['common_headings']:
        st.markdown("**Common H3 Headings**")
        h3_df = pd.DataFrame(
            content_brief['competitor_insights']['common_headings']['h3'],
            columns=['Heading', 'Frequency']
        )
        st.dataframe(h3_df)

def main():
    st.markdown('<div class="main-header">SEO Content Brief Generator</div>', unsafe_allow_html=True)
    st.markdown("Generate data-driven SEO content briefs by analyzing Google search results.")
    
    # Sidebar for API key and inputs
    st.sidebar.title("Configuration")
    
    # Get SERPAPI key
    serpapi_key = st.sidebar.text_input("Enter your SERPAPI Key", type="password")
    
    # Get keyword input
    keyword = st.text_input("Enter Keyword to Analyze")
    
    # Generate button
    generate_button = st.button("Generate SEO Content Brief")
    
    if generate_button:
        if not serpapi_key:
            st.error("Please enter your SERPAPI key.")
            return
        
        if not keyword:
            st.error("Please enter a keyword to analyze.")
            return
        
        # Initialize the generator
        generator = SEOContentBriefGenerator(serpapi_key)
        
        # Generate the content brief
        content_brief = generator.generate_seo_content_brief(keyword)
        
        # Display the content brief
        if content_brief:
            display_content_brief(content_brief)
            
            # Add download button for JSON
            json_str = json.dumps(content_brief, indent=2)
            st.download_button(
                label="Download Brief as JSON",
                data=json_str,
                file_name=f"{keyword.replace(' ', '_')}_seo_brief.json",
                mime="application/json"
            )

if __name__ == "__main__":
    main()
