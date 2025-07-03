import json
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
import re

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
# def generate_single_question(field_path):
#     prompt = ChatPromptTemplate.from_messages([
#         ("system", "You're an expert at creating user interview questions for digital twin systems."),
#         ("user", """
#         Create ONE interview question for a user profile field with these requirements:
#         - Tone: Warmly professional, encouraging, neutral, non-judgmental
#         - Language: Second-person ("you"), clear, jargon-free, inclusive
#         - Style: One idea per question; mix open-ended/slider formats
#         - Length: Under 20 words
        
#         Example for "generalprofile.userContextAndLifestyle.timeAvailability.weekend":
#         "How much free time do you typically have on weekends?"
        
#         Generate only the question text for: {field_path}
#         """)
#     ])


# def generate_single_question(field_path):
#     prompt = ChatPromptTemplate.from_messages([
#         ("system", "You're an expert at creating user interview questions for digital twin systems."),
#         ("user", """
#         First, ask the user:
#   “Which type of recommendations would you like—movies, food, travel, or something else?”

# Then, create ONE interview question for a user profile field with these requirements:
#   - Tone: Warmly professional, encouraging, neutral, non-judgmental  
#   - Language: Second-person (“you”), clear, jargon-free, inclusive  
#   - Style: One idea per question; mix open-ended/slider formats  
#   - Length: Under 20 words  
#   - Include the predetermined answer options for that field, formatted as bullet points or parentheses  

# Example for  
# `generalprofile.userContextAndLifestyle.timeAvailability.weekend`:  
#   “How much free time do you typically have on weekends?  
#    - Very little (under 2 hours)  
#    - Some (2–5 hours)  
#    - Plenty (5+ hours)”

# Generate only the question text (with its options) for: `{field_path}`  

#         """)
#     ])
def generate_single_question(field_path, intentDescription):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a friendly AI assistant helping users build their personalized digital twin for better recommendations. Your tone should be warm, encouraging, and respectful."),
        ("user", """
    You will be given a field from a JSON schema and a description explaining its intent.

    Generate a conversational, open-ended question that:
    - Feels like part of a friendly dialogue
    - Offers light guidance or an example to help the user answer
    - Is inclusive and privacy-aware (especially if the topic is sensitive)
    - Does NOT include multiple-choice options or lists
    - Sounds like something a thoughtful assistant would naturally ask


    Use the field name and description to craft the question.

    Example input:
    Field Name: userContextAndLifestyle.lifeStageNotes  
    Description: Capture the user’s current phase in life, such as studying, working, married, retired, etc.

    Example output:
    “What stage of life are you currently in? Feel free to share if you’re studying, working, raising a family, or going through any major change right now.”

    Now generate a similar conversational question for:

    Field Name: {field_path}  
    Description: {intentDescription}
    """)
    ])

    model = ChatOpenAI(model="gpt-4o", temperature=0.3)
    chain = prompt | model
    response = chain.invoke({"field_path": field_path , "intentDescription": intentDescription})
    return response.content.strip()


# function for getting description path
# def get_description_for_path(root: dict, dotted_path: str) -> str:
#     """
#     Given a nested dict `root` and a dotted path like "corePreferences.noveltySeeking",
#     walks the dict and returns the value of its "description" key, or "" if not found.
#     """
#     node = root
#     for p in dotted_path.split('.'):
#         node = node.get(p, {})
#     return node.get("description", "")



def get_description_for_path(root: dict, dotted_path: str) -> str:
    # Strip trailing 'value' or 'description'
    parts = dotted_path.split('.')
    if parts[-1] in ("value", "description"):
        parts = parts[:-1]

    node = root
    for key in parts:
        if not isinstance(node, dict):
            return ""
        node = node.get(key, {})

    # Final check: node must be dict before accessing .get("description")
    if isinstance(node, dict):
        return node.get("description", "")
    return ""



# Main processing function
def generate_questions(data, section, category=None):
    results = []
    
    if section == "generalprofile":
        leaf_paths = get_leaf_paths(data["generalprofile"])
        for path in leaf_paths:
            subsection = path.split('.')[0]
            absolute_path = f"generalprofile.{path}"

            field_path = path.replace(".value", "")   
        

            # pull description out of your JSON schema
            intent_desc = get_description_for_path(data["generalprofile"], field_path)

            question = generate_single_question(absolute_path , intent_desc)
            results.append({
                "section": "generalprofile",
                "subsection": subsection,
                "field": path,
                "question": question
            })
            
    # elif section == "recommendation" and category:
    #     category_data = data["recommendationProfiles"][category]
    #     leaf_paths = get_leaf_paths(category_data)
    #     for path in leaf_paths:
    #         absolute_path = f"recommendationProfiles.{category}.{path}"

    #         intent_desc = get_description_for_path(data["generalprofile"], field_path)
    #         question = generate_single_question(absolute_path , intent_desc)
    #         results.append({
    #             "section": "recommendationProfiles",
    #             "subsection": category,
    #             "field": f"{category}.{path}",
    #             "question": question
    #         })
            
    # return results


    elif section == "recommendation" and category:
        category_data = data["recommendationProfiles"][category]
        leaf_paths = get_leaf_paths(category_data)
        for path in leaf_paths:
            absolute_path = f"recommendationProfiles.{category}.{path}"

            # Get description from within category schema
            intent_desc = get_description_for_path(category_data, path)

            # Generate question
            question = generate_single_question(absolute_path, intent_desc)

            results.append({
                "section": "recommendationProfiles",
                "subsection": category,
                "field": f"{category}.{path}",
                "description": intent_desc,
                "question": question
            })

    return results


# — Helper to pull out only the JSON array from LLM output —
def extract_json_array(s: str) -> str:
    """
    Finds the first JSON array in a string and returns it.
    Raises ValueError if none is found.
    """
    pattern = r'\[\s*(?:\{.*?\}\s*,?\s*)+\]'
    match = re.search(pattern, s, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in LLM response")
    return match.group(0)


def rank_and_tier_with_gpt4o(questions: list[dict]) -> list[dict]:
    """
    Takes the list of question‐dicts and returns the same list,
    each augmented with:
      - impactScore: integer 0–100
      - tier: "Tier 1" / "Tier 2" / "Tier 3"
    Sorted by descending impactScore.
    """
    # 1. Build prompt
    system = SystemMessagePromptTemplate.from_template(
        "You are an expert in personalization and recommendation logic. "
        "Given a list of user‐profile questions (each with 'field', 'question', and optional 'options'), "
        "score each from 0–100 on its impact for generating high-quality recommendations, "
        "rank them, and bucket into three equal tiers (top 33%, middle 33%, bottom 33%)."
    )
    human = HumanMessagePromptTemplate.from_template(
        """Here is a JSON array of questions.  
Respond with ONLY a JSON array of the same objects, each with added::
- impactScore: integer between 0 and 100  
- tier: "Tier 1", "Tier 2", or "Tier 3"  
- qest: "pending" 


Sort by descending impactScore.

```json
{questions}
```"""
    )
    prompt = ChatPromptTemplate.from_messages([system, human])

    # 2. Call GPT-4o
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    raw = llm(prompt.format_messages(questions=json.dumps(questions, indent=2)))
    
    # extract json 
    json_text = extract_json_array(raw.content)
    return json.loads(json_text)

    # 3. Parse and return
    # return json.loads(raw.content)



from collections import defaultdict
from typing import List, Dict, Any

def wrap_questions_by_tier(
    flat_questions: List[Dict[str, Any]],
    status: str = "in_process"
) -> Dict[str, Dict[str, Any]]:
    """
    Groups a flat list of question‑dicts (each with 'tier': "Tier 1"/"Tier 2"/"Tier 3")
    into a nested dict with keys 'tier1', 'tier2', 'tier3', each having:
      - 'status': same status for all tiers (default "in_process")
      - 'questions': list of question‑dicts for that tier

    Example return:
    {
      "tier1": {"status": "in_process", "questions": [ ... Tier 1 items ... ]},
      "tier2": {"status": "in_process", "questions": [ ... Tier 2 items ... ]},
      "tier3": {"status": "in_process", "questions": [ ... Tier 3 items ... ]},
    }
    """
    grouped = defaultdict(list)
    for q in flat_questions:
        grouped[q["tier"]].append(q)

    return {
        "tier1": {"status": status, "questions": grouped.get("Tier 1", [])},
        "tier2": {"status": status, "questions": grouped.get("Tier 2", [])},
        "tier3": {"status": status, "questions": grouped.get("Tier 3", [])},
    }




# def get_next_question(data):
#     """
#     Given a dict with tier1, tier2, tier3, each having 'status' and 'questions',
#     returns the 'question' text of the first pending question in the first in_process tier.
#     """
#     for tier in ("tier1", "tier2", "tier3"):
#         tier_info = data.get(tier, {})
#         if tier_info.get("status") == "in_process":
#             for q in tier_info.get("questions", []):
#                 if q.get("qest") == "pending":
#                     return q.get("question")
#     return None


# def get_all_pending_questions(data):
#     """
#     Given a dict with tier1, tier2, tier3, each having 'status' and 'questions',
#     returns a list of 'question' texts for all pending questions
#     in the first tier whose status is 'in_process'. If none, returns [].
#     """
#     for tier in ("tier1", "tier2", "tier3"):
#         tier_info = data.get(tier, {})
#         if tier_info.get("status") == "in_process":
#             return [
#                 q.get("question")
#                 for q in tier_info.get("questions", [])
#                 if q.get("qest") == "pending"
#             ]
#     return []




def get_all_pending_questions(json_input):
    """
    Accepts a JSON string with tier1, tier2, tier3,
    each having 'status' and 'questions',
    and returns a list of 'question' texts for all pending questions
    in the first tier whose status is 'in_process'.
    """
    if isinstance(json_input, str):
        try:
            data = json.loads(json_input)
        except json.JSONDecodeError:
            raise ValueError("Input is not valid JSON.")
    else:
        raise TypeError("Function expects a JSON string as input.")

    for tier in ("tier1", "tier2", "tier3"):
        tier_info = data.get(tier, {})
        if isinstance(tier_info, dict) and tier_info.get("status") == "in_process":
            return [
                q.get("question")
                for q in tier_info.get("questions", [])
                if q.get("qest") == "pending"
            ]
    return []







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

# if section_type == "General Profile":
#     if st.button("✨ Generate General Profile Questions"):
#         with st.spinner("Generating questions using GPT-4o..."):
#             questions = generate_questions(json_data, "generalprofile")
#             tiered_questions = rank_and_tier_with_gpt4o(questions)   ## added this function
#             st.success(f"Generated {len(tiered_questions)} questions!")
#             st.json(tiered_questions)
#             st.download_button("💾 Download Questions", 
#                               json.dumps(tiered_questions, indent=2),
#                               "general_questions.json")


if section_type == "General Profile":
    if st.button("✨ Generate General Profile Questions"):
        with st.spinner("Generating questions using GPT-4o..."):
            # 1) Generate the raw questions
            questions = generate_questions(json_data, "generalprofile")
            
            # 2) Rank & tier via GPT-4.o, with JSON‐only extraction
            try:
                tiered_questions = rank_and_tier_with_gpt4o(questions)
                wrapped_output = wrap_questions_by_tier(tiered_questions, status="in_process")
            except ValueError as e:
                st.error(f"Failed to parse LLM response: {e}")
                st.stop()



        # 3) Display results
        st.success(f"Generated {len(wrapped_output)} questions!")
        st.json(wrapped_output)
        st.download_button(
            "💾 Download Questions",
            data=json.dumps(wrapped_output, indent=2),
            file_name="general_questions.json",
            mime="application/json"
        )



    if st.button("Show Next Question"):
        questions = generate_questions(json_data, "generalprofile")
        
        # 2) Rank & tier via GPT-4.o, with JSON‐only extraction
        try:
            tiered_questions = rank_and_tier_with_gpt4o(questions)
            wrapped_output = wrap_questions_by_tier(tiered_questions, status="in_process")
        except ValueError as e:
            st.error(f"Failed to parse LLM response: {e}")
            st.stop()
        try:
            pending_q = get_all_pending_questions(wrapped_output)
            print(pending_q)

            if pending_q:
                st.markdown("**Pending Questions:**")
                for q in pending_q:
                    st.markdown(f"- {q}")
    
            else:
                st.info("No pending questions found.")
        except json.JSONDecodeError:
            st.error("Invalid JSON—please check your syntax.")


# elif section_type == "Recommendation Profile":
#     categories = list(json_data["recommendationProfiles"].keys())
#     selected_category = st.selectbox("Select category:", categories)
    
#     if st.button(f"✨ Generate {selected_category} Questions"):
#         with st.spinner("Generating questions using GPT-4o..."):
#             questions = generate_questions(json_data, "recommendation", selected_category)
#             st.success(f"Generated {len(questions)} questions for {selected_category}!")
#             st.json(questions)
#             st.download_button("💾 Download Questions", 
#                               json.dumps(questions, indent=2),
#                               f"{selected_category}_questions.json")


elif section_type == "Recommendation Profile":
    categories = list(json_data.get("recommendationProfiles", {}).keys())
    selected_category = st.selectbox("Select category:", categories)
    
    if st.button(f"✨ Generate {selected_category} Questions"):
        with st.spinner("Generating questions using GPT-4o..."):
            # 1) Generate the raw questions for this category
            questions = generate_questions(json_data, "recommendation", selected_category)
            
            # 2) Rank & tier via GPT-4.o, catching JSON extraction errors
            try:
                tiered_questions = rank_and_tier_with_gpt4o(questions)
            except ValueError as e:
                st.error(f"Failed to parse LLM response: {e}")
                st.stop()

        # 3) Display and download
        st.success(f"Generated and tiered {len(tiered_questions)} questions for {selected_category}!")
        st.json(tiered_questions)
        st.download_button(
            "💾 Download Questions",
            data=json.dumps(tiered_questions, indent=2),
            file_name=f"{selected_category}_questions.json",
            mime="application/json"
        )






