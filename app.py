import streamlit as st
import pandas as pd
import random
from datetime import datetime

# Set up the app
st.set_page_config(
    page_title="SEO Content Brief Generator",
    page_icon="📊",
    layout="wide"
)

# App title and description
st.title("🔍 SEO Content Brief Generator")
st.markdown("""
Generate data-driven SEO content briefs for any keyword. This tool analyzes SERP data, identifies search intent,
and creates comprehensive content outlines that can help you outrank competitors.
""")

# Sidebar for input
with st.sidebar:
    st.header("Configuration")
    keyword = st.text_input("Enter target keyword:", "digital marketing strategies")
    location = st.text_input("Location (optional):", "United States")
    language = st.selectbox("Language:", ["en", "es", "fr", "de", "jp"])
    
    # Mock API key input (in a real app, this would be stored in secrets)
    api_key = st.text_input("SerpAPI Key (simulated):", type="password")
    
    generate_btn = st.button("Generate Content Brief", type="primary")

# Mock SERP data function (in a real app, this would call the SerpAPI)
def get_serp_data(keyword, location, language):
    # Simulating API delay
    with st.spinner(f"Analyzing SERP for '{keyword}'..."):
        # This would be replaced with actual API call:
        # from serpapi import GoogleSearch
        # params = {
        #   "q": keyword,
        #   "location": location,
        #   "hl": language,
        #   "api_key": api_key
        # }
        # search = GoogleSearch(params)
        # results = search.get_dict()
        
        # Mock data for demonstration
        mock_organic_results = [
            {
                "position": 1,
                "title": "10 Digital Marketing Strategies for Business Growth in 2023",
                "url": "https://example.com/digital-marketing-strategies",
                "snippet": "Learn the most effective digital marketing strategies to grow your business. Includes SEO, content marketing, social media, and more."
            },
            {
                "position": 2,
                "title": "The Complete Guide to Digital Marketing | Strategies & Examples",
                "url": "https://example.com/complete-digital-marketing-guide",
                "snippet": "A comprehensive guide to digital marketing strategies with real-world examples and case studies."
            },
            {
                "position": 3,
                "title": "15 Effective Digital Marketing Strategies for Small Businesses",
                "url": "https://example.com/digital-marketing-small-business",
                "snippet": "Digital marketing strategies tailored for small businesses with limited budgets but big goals."
            },
            {
                "position": 4,
                "title": "Digital Marketing Strategies: Ultimate Guide with Examples",
                "url": "https://example.com/digital-marketing-ultimate-guide",
                "snippet": "Everything you need to know about digital marketing strategies with practical examples and templates."
            },
            {
                "position": 5,
                "title": "How to Create a Digital Marketing Strategy in 7 Steps",
                "url": "https://example.com/create-digital-marketing-strategy",
                "snippet": "Step-by-step guide to creating an effective digital marketing strategy for your business."
            }
        ]
        
        mock_paa = [
            "What are the most effective digital marketing strategies?",
            "How do I create a digital marketing strategy?",
            "What are the types of digital marketing?",
            "Which digital marketing strategy is best for small business?",
            "How much does digital marketing strategy cost?",
            "What is an example of a digital marketing strategy?",
            "How often should I update my digital marketing strategy?"
        ]
        
        return mock_organic_results, mock_paa

# Function to analyze search intent
def analyze_intent(organic_results, paa_questions):
    # Simple intent analysis based on keywords in titles and snippets
    text_corpus = " ".join([result["title"] + " " + result["snippet"] for result in organic_results])
    text_corpus += " ".join(paa_questions)
    
    text_corpus = text_corpus.lower()
    
    # Check for commercial intent keywords
    commercial_keywords = ["buy", "price", "cost", "deal", "discount", "review", "best", "top", "compare"]
    transactional_keywords = ["buy", "purchase", "order", "deal", "discount", "for sale"]
    informational_keywords = ["how to", "what is", "guide", "strategies", "tips", "ways to", "examples"]
    
    commercial_score = sum(1 for word in commercial_keywords if word in text_corpus)
    transactional_score = sum(1 for word in transactional_keywords if word in text_corpus)
    informational_score = sum(1 for word in informational_keywords if word in text_corpus)
    
    # Determine dominant intent
    if transactional_score > commercial_score and transactional_score > informational_score:
        intent = "Transactional"
    elif commercial_score > informational_score:
        intent = "Commercial Investigation"
    else:
        intent = "Informational"
    
    return intent

# Function to generate content brief
def generate_content_brief(keyword, organic_results, paa_questions, intent):
    # Generate title suggestions
    titles = [
        f"Ultimate Guide to {keyword.title()} in {datetime.now().year}",
        f"Top 10 {keyword.title()} That Actually Work",
        f"How to Master {keyword.title()}: A Step-by-Step Guide",
        f"The Complete {keyword.title()} Guide for Beginners"
    ]
    
    # Generate meta description
    meta_description = f"Discover the most effective {keyword} with our comprehensive guide. Learn proven strategies, tips and examples to improve your results."
    
    # Generate outline based on intent and competitor analysis
    if intent == "Informational":
        h2_structure = [
            f"What is {keyword.split()[0]}?",
            "Why Are Effective Strategies Important?",
            "Key Types and Approaches",
            "Step-by-Step Implementation Guide",
            "Common Mistakes to Avoid",
            "Advanced Tips and Techniques",
            "Tools and Resources",
            "FAQs"
        ]
    else:  # Commercial or Transactional
        h2_structure = [
            f"Best {keyword.title()} Compared",
            "Key Features to Look For",
            "Pricing Comparison",
            "Pros and Cons Analysis",
            "How to Choose the Right One",
            "Implementation Tips",
            "Alternative Options",
            "FAQs"
        ]
    
    # Generate H3 structure for each H2
    h3_structure = {}
    for h2 in h2_structure:
        if h2 == "Key Types and Approaches":
            h3_structure[h2] = [
                "Content Marketing Strategies",
                "Social Media Approaches",
                "SEO Techniques",
                "Email Marketing Tactics",
                "PPC Advertising Methods"
            ]
        elif h2 == "Step-by-Step Implementation Guide":
            h3_structure[h2] = [
                "Setting Clear Objectives",
                "Audience Research and Targeting",
                "Strategy Development",
                "Implementation Timeline",
                "Measuring and Analyzing Results"
            ]
        elif h2 == "FAQs":
            # Use the PAA questions here
            h3_structure[h2] = random.sample(paa_questions, min(5, len(paa_questions)))
        else:
            h3_structure[h2] = [f"Key aspect of {h2}", f"Important consideration for {h2}", f"Expert tip on {h2}"]
    
    return {
        "title": random.choice(titles),
        "meta_description": meta_description,
        "intent": intent,
        "h2_structure": h2_structure,
        "h3_structure": h3_structure,
        "paa_questions": paa_questions
    }

# Main app logic
if generate_btn:
    if not keyword:
        st.error("Please enter a keyword to analyze.")
    else:
        # Get SERP data
        organic_results, paa_questions = get_serp_data(keyword, location, language)
        
        # Analyze search intent
        intent = analyze_intent(organic_results, paa_questions)
        
        # Generate content brief
        brief = generate_content_brief(keyword, organic_results, paa_questions, intent)
        
        # Display results in tabs
        tab1, tab2, tab3, tab4 = st.tabs(["Content Brief", "SERP Analysis", "Competitor Headings", "PAA Questions"])
        
        with tab1:
            st.header("SEO Content Brief")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Optimized Title")
                st.success(brief["title"])
                
                st.subheader("Meta Description")
                st.info(brief["meta_description"])
                
                st.subheader("Search Intent")
                st.write(brief["intent"])
                
            with col2:
                st.subheader("Content Outline")
                
                for h2 in brief["h2_structure"]:
                    with st.expander(h2):
                        if h2 in brief["h3_structure"]:
                            for h3 in brief["h3_structure"][h2]:
                                st.write(f"- {h3}")
        
        with tab2:
            st.header("SERP Analysis")
            st.subheader("Top Ranking Pages")
            
            serp_df = pd.DataFrame(organic_results)
            serp_df = serp_df[['position', 'title', 'snippet']]
            serp_df.columns = ['Position', 'Title', 'Description']
            st.dataframe(serp_df, use_container_width=True)
            
            st.subheader("Intent Analysis")
            intent_col1, intent_col2, intent_col3 = st.columns(3)
            
            with intent_col1:
                st.metric("Informational Intent", "Strong" if brief["intent"] == "Informational" else "Moderate")
            
            with intent_col2:
                st.metric("Commercial Intent", "Strong" if brief["intent"] == "Commercial Investigation" else "Moderate")
            
            with intent_col3:
                st.metric("Transactional Intent", "Strong" if brief["intent"] == "Transactional" else "Moderate")
        
        with tab3:
            st.header("Competitor Headings Analysis")
            
            # Mock competitor headings analysis
            st.subheader("Most Common Headings Across Competitors")
            
            common_headings = [
                "What is Digital Marketing?",
                "Types of Digital Marketing",
                "Benefits of Digital Marketing",
                "How to Create a Strategy",
                "Digital Marketing Examples",
                "Measuring Success",
                "Tools and Resources"
            ]
            
            for heading in common_headings:
                st.write(f"- {heading}")
            
            st.subheader("Heading Gaps & Opportunities")
            
            opportunity_headings = [
                "Digital Marketing for Local Businesses",
                "Integrating AI in Digital Marketing",
                "Voice Search Optimization Strategies",
                "Interactive Content Approaches",
                "Micro-moments in Customer Journey"
            ]
            
            for heading in opportunity_headings:
                st.write(f"- {heading}")
        
        with tab4:
            st.header("People Also Ask Questions")
            
            for i, question in enumerate(brief["paa_questions"], 1):
                st.write(f"{i}. {question}")
            
            st.subheader("FAQ Section Recommendation")
            st.info("Include these questions in your FAQ section to target featured snippets and voice search queries.")

else:
    # Show instructions when no keyword has been entered
    st.info("👈 Enter a keyword in the sidebar and click 'Generate Content Brief' to get started.")
    
    # Example output
    st.subheader("Example Output")
    with st.expander("See what a generated content brief looks like"):
        st.write("""
        **Keyword:** "content marketing strategies"
        
        **Title:** Ultimate Guide to Content Marketing Strategies in 2023
        
        **Meta Description:** Discover the most effective content marketing strategies with our comprehensive guide. Learn proven approaches, tips and examples to improve your results.
        
        **Search Intent:** Informational
        
        **Content Outline:**
        - What is Content Marketing?
        - Why Are Effective Strategies Important?
        - Key Types and Approaches
          - Blogging and Article Marketing
          - Social Media Content Strategies
          - Video Marketing Approaches
          - Email Newsletter Tactics
          - Interactive Content Methods
        - Step-by-Step Implementation Guide
        - Common Mistakes to Avoid
        - Advanced Tips and Techniques
        - Tools and Resources
        - FAQs
          - What are the most effective content marketing strategies?
          - How do I create a content marketing strategy?
          - What types of content work best?
        """)

# Footer
st.markdown("---")
st.markdown("📊 *This tool generates SEO content briefs based on SERP analysis. Connect to SerpAPI for real data.*")
