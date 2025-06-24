import json
import streamlit as st
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Helper function to get leaf paths from JSON structure
def get_leaf_paths(data, parent_key='', sep='.'):
    paths = []
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            paths.extend(get_leaf_paths(value, new_key, sep))
        else:
            paths.append(new_key)
    return paths

# Generate questions using LLM
def generate_single_question(field_path):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You're an expert at creating user interview questions for digital twin systems."),
        ("user", """
        Create ONE interview question for a user profile field with these requirements:
        - Tone: Warmly professional, encouraging, neutral, non-judgmental
        - Language: Second-person ("you"), clear, jargon-free, inclusive
        - Style: One idea per question; mix open-ended/slider formats
        - Length: Under 20 words
        
        Example for "generalprofile.userContextAndLifestyle.timeAvailability.weekend":
        "How much free time do you typically have on weekends?"
        
        Generate only the question text for: {field_path}
        """)
    ])
    
    model = ChatOpenAI(model="gpt-4o", temperature=0.3)
    chain = prompt | model
    response = chain.invoke({"field_path": field_path})
    return response.content.strip()

# Main processing function
def generate_questions(data, section, category=None):
    results = []
    
    if section == "generalprofile":
        leaf_paths = get_leaf_paths(data["generalprofile"])
        for path in leaf_paths:
            subsection = path.split('.')[0]
            absolute_path = f"generalprofile.{path}"
            question = generate_single_question(absolute_path)
            results.append({
                "section": "generalprofile",
                "subsection": subsection,
                "field": path,
                "question": question
            })
            
    elif section == "recommendation" and category:
        category_data = data["recommendationProfiles"][category]
        leaf_paths = get_leaf_paths(category_data)
        for path in leaf_paths:
            absolute_path = f"recommendationProfiles.{category}.{path}"
            question = generate_single_question(absolute_path)
            results.append({
                "section": "recommendationProfiles",
                "subsection": category,
                "field": f"{category}.{path}",
                "question": question
            })
            
    return results

# Streamlit UI
st.title("📝 Digital Twin Interview Question Generator")
st.caption("Generate interview questions for user profile sections")

# Load sample JSON
sample_json = {
    # Your full JSON structure here
}

uploaded_file = st.file_uploader("Upload profile JSON", type=["json"])
json_data = sample_json if uploaded_file is None else json.load(uploaded_file)

# Section selection
section_type = st.radio("Select section to generate questions for:",
                        ("General Profile", "Recommendation Profile"))

if section_type == "General Profile":
    if st.button("✨ Generate General Profile Questions"):
        with st.spinner("Generating questions using GPT-4o..."):
            questions = generate_questions(json_data, "generalprofile")
            st.success(f"Generated {len(questions)} questions!")
            st.json(questions)
            st.download_button("💾 Download Questions", 
                              json.dumps(questions, indent=2),
                              "general_questions.json")
            
elif section_type == "Recommendation Profile":
    categories = list(json_data["recommendationProfiles"].keys())
    selected_category = st.selectbox("Select category:", categories)
    
    if st.button(f"✨ Generate {selected_category} Questions"):
        with st.spinner("Generating questions using GPT-4o..."):
            questions = generate_questions(json_data, "recommendation", selected_category)
            st.success(f"Generated {len(questions)} questions for {selected_category}!")
            st.json(questions)
            st.download_button("💾 Download Questions", 
                              json.dumps(questions, indent=2),
                              f"{selected_category}_questions.json")