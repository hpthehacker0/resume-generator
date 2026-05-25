import streamlit as st
import requests
import uuid

# --- Page Configuration ---
st.set_page_config(
    page_title="Multi-Agent Career Generator",
    page_icon="💼",
    layout="wide"
)

# --- API Configuration ---
# Update this if your FastAPI server runs on a different port/host
FASTAPI_URL = "http://localhost:8000/generate"

# Generate a unique session ID to act as the user_id for state tracking
if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())

# --- UI Header ---
st.title("💼 Multi-Agent Resume & Cover Letter Generator")
st.markdown("""
This system uses a team of AI agents (Powered by **LangGraph** & **Ollama**) to analyze a job description, 
rewrite your resume to beat ATS systems, and draft a highly tailored cover letter.
""")
st.divider()

# --- Input Section ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Your Raw Resume")
    resume_text = st.text_area(
        "Paste your current resume here:",
        height=300,
        placeholder="John Doe\nSoftware Engineer\n\nExperience:\n- Built REST APIs..."
    )

with col2:
    st.subheader("2. Target Job Description")
    job_description = st.text_area(
        "Paste the job description you are applying for:",
        height=300,
        placeholder="We are looking for a Backend Engineer with experience in Python, scalable architecture..."
    )

# --- Generation Logic ---
if st.button("🚀 Generate Tailored Application", type="primary", use_container_width=True):
    if not resume_text or not job_description:
        st.warning("Please provide both a resume and a job description.")
    else:
        with st.spinner("Agents are analyzing, optimizing, and writing... This may take a minute or two."):
            # Prepare payload for FastAPI
            payload = {
                "user_id": st.session_state["user_id"],
                "resume_text": resume_text,
                "job_description": job_description
            }
            
            try:
                # Call the FastAPI backend
                response = requests.post(FASTAPI_URL, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("Generation Complete!")
                    st.divider()
                    
                    # --- Output Section ---
                    st.markdown(f"### 📈 Projected ATS Score Improvement: **{result.get('ats_score_improvement', 'N/A')}**")
                    
                    out_col1, out_col2 = st.columns(2)
                    
                    with out_col1:
                        st.subheader("📄 Optimized Resume")
                        st.markdown(result.get("optimized_resume", "No resume generated."))
                        
                    with out_col2:
                        st.subheader("✉️ Tailored Cover Letter")
                        st.markdown(result.get("cover_letter", "No cover letter generated."))
                        
                else:
                    st.error(f"Error from server: {response.status_code} - {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Failed to connect to the backend. Is your FastAPI server running on localhost:8000?")