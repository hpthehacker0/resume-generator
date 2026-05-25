import json
import asyncpg
from typing import TypedDict, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver # Can be swapped for RedisSaver

app = FastAPI(title="Multi-Agent Career Generator API")

# ==========================================
# 1. Initialize Local LLM (Ollama)
# ==========================================
# Pointing directly to your local Ollama instance running gpt-oss:120b-cloud
llm = ChatOllama(
    model="gpt-oss:120b-cloud", 
    temperature=0.2, # Low temp for precision in parsing/formatting
    base_url="http://localhost:11434"
)

# ==========================================
# 2. Define Shared Context (State)
# ==========================================
class AgentState(TypedDict):
    raw_resume: str
    job_description: str
    job_analysis: Dict[str, Any]
    optimized_resume: str
    final_cover_letter: str
    ats_score_improvement: str

# ==========================================
# 3. Define Agent Nodes
# ==========================================
def job_analyzer_node(state: AgentState):
    """Agent 1: Extracts structured JSON intelligence from JD."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert technical recruiter. Extract the following from the job description and return ONLY valid JSON: 'role', 'skills_required' (list), 'keywords' (list), 'tone' (string)."),
        ("user", "{job_description}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"job_description": state["job_description"]})
    
    try:
        # Strip markdown code blocks if the LLM adds them
        clean_json = response.content.replace("```json", "").replace("```", "").strip()
        analysis = json.loads(clean_json)
    except json.JSONDecodeError:
        analysis = {"error": "Failed to parse JSON"}

    return {"job_analysis": analysis}

def resume_optimizer_node(state: AgentState):
    """Agent 2: Rewrites resume based on JD analysis."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an ATS optimization expert. Rewrite the user's resume to align with these job requirements: {job_analysis}. Insert keywords naturally and quantify achievements. Output the full rewritten resume."),
        ("user", "Original Resume:\n{raw_resume}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "job_analysis": json.dumps(state["job_analysis"]),
        "raw_resume": state["raw_resume"]
    })
    
    # Mocking ATS score logic for the pipeline
    return {
        "optimized_resume": response.content,
        "ats_score_improvement": "72 -> 94" 
    }

def cover_letter_writer_node(state: AgentState):
    """Agent 3: Writes cover letter matching company tone."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Write a 3-paragraph personalized cover letter using this optimized resume: {optimized_resume}. The tone of the company is {tone}. Focus heavily on matching the required skills: {skills}."),
        ("user", "Generate the cover letter.")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "optimized_resume": state["optimized_resume"],
        "tone": state.get("job_analysis", {}).get("tone", "professional"),
        "skills": ", ".join(state.get("job_analysis", {}).get("skills_required", []))
    })
    
    return {"final_cover_letter": response.content}

# ==========================================
# 4. Orchestrate Pipeline (LangGraph)
# ==========================================
workflow = StateGraph(AgentState)

workflow.add_node("job_analyzer", job_analyzer_node)
workflow.add_node("resume_optimizer", resume_optimizer_node)
workflow.add_node("cover_letter_writer", cover_letter_writer_node)

workflow.set_entry_point("job_analyzer")
workflow.add_edge("job_analyzer", "resume_optimizer")
workflow.add_edge("resume_optimizer", "cover_letter_writer")
workflow.add_edge("cover_letter_writer", END)

# Checkpointer manages the temporary context (can easily swap MemorySaver for RedisSaver)
memory = MemorySaver()
app_pipeline = workflow.compile(checkpointer=memory)

# ==========================================
# 5. FastAPI Endpoints & Storage
# ==========================================
class JobApplicationRequest(BaseModel):
    user_id: str
    resume_text: str
    job_description: str

async def save_to_postgres(user_id: str, optimized_resume: str, cover_letter: str):
    """Saves the final generated documents to PostgreSQL."""
    conn = await asyncpg.connect('postgresql://postgres:12345678@localhost/resumedb')
    await conn.execute('''
        INSERT INTO career_documents (user_id, optimized_resume, cover_letter) 
        VALUES ($1, $2, $3)
    ''', user_id, optimized_resume, cover_letter)
    await conn.close()

@app.post("/generate")
async def generate_career_documents(request: JobApplicationRequest):
    initial_state = {
        "raw_resume": request.resume_text,
        "job_description": request.job_description
    }
    
    # Thread ID allows you to resume/track specific generation states in Redis/Memory
    config = {"configurable": {"thread_id": request.user_id}}
    
    try:
        final_state = app_pipeline.invoke(initial_state, config=config)
        
        # Fire off to PostgreSQL
        await save_to_postgres(
            request.user_id, 
            final_state["optimized_resume"], 
            final_state["final_cover_letter"]
        )
        
        return {
            "optimized_resume": final_state["optimized_resume"],
            "cover_letter": final_state["final_cover_letter"],
            "ats_score_improvement": final_state["ats_score_improvement"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))