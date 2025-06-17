import os
import json
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import Supabase
try:
    from supabase import create_client, Client
except ImportError:
    create_client = None  # Skip if supabase is not installed

import google.generativeai as genai

# Initialize FastAPI app
app = FastAPI(title="AI Keyword Agent", version="1.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env file")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Initialize Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None

if SUPABASE_URL and SUPABASE_KEY and create_client:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("⚠️ WARNING: Supabase credentials are missing or invalid.")

# ========== Pydantic Models ==========
class KeywordRequest(BaseModel):
    category: str
    target_platform: Optional[str] = "any"
    language: Optional[str] = "English"
    max_keywords: Optional[int] = 25
    difficulty_level: Optional[str] = "medium"

class KeywordReportRequest(KeywordRequest):
    report_length: Optional[int] = 300

# ========== Core Prompts ==========
PROMPT_TEMPLATES = {
    "seed_keywords": """
    As a professional SEO strategist, generate {max_keywords} highly targeted keywords for [{category}] focusing on:
    1. Platform-specific needs: {target_platform}
    2. Language: {language}
    3. Keyword difficulty: {difficulty_level}
    4. Current trends (2023-2024)
    
    Structure:
    - Include commercial and informational intent
    - Add pain point indicators (e.g., "slow", "easy", "affordable")
    - Use modifiers: "for [audience]", "with [feature]", "without [limitation]"
    
    Format: JSON array with keys:
    "keyword", "intent_type", "difficulty_estimate", "pain_points", "trend_score"
    """,
    
    "competitor_analysis": """
    Analyze top competitors in [{category}] and identify 15 keyword gaps. Consider:
    1. Under-optimized long-tail phrases
    2. Missing feature-focused terms
    3. Untapped pain points
    
    Output: JSON array with:
    "opportunity_keyword", "gap_type", "competitor_missing_count"
    """,
    
    "question_keywords": """
    Generate 10 question-based keywords for [{category}] targeting {target_platform} users.
    Include:
    - How-to questions
    - Comparison questions
    - Problem-solving questions
    
    Format: JSON array with:
    "question", "question_type", "target_intent"
    """,
    
    "trend_report": """
    Create a {report_length}-word trend report for [{category}] covering:
    1. Emerging keyword opportunities
    2. Rising competitor strategies
    3. Recommended keyword targets
    4. Risk assessment
    
    Tone: Professional, data-driven
    Format: Markdown with headings
    """
}

# ========== Helper Functions ==========
def parse_gemini_response(response_text: str) -> List[Dict]:
    try:
        start = response_text.find('[')
        end = response_text.rfind(']') + 1
        return json.loads(response_text[start:end])
    except Exception as e:
        raise ValueError(f"Failed to parse Gemini response: {str(e)}")

def store_search_session(category: str, results: Dict, metadata: Dict):
    if supabase:
        supabase.table("search_sessions").insert({
            "category": category,
            "results": results,
            "metadata": metadata,
            "created_at": datetime.now().isoformat()
        }).execute()

# ========== API Endpoints ==========
@app.post("/generate-keywords", response_model=Dict)
async def generate_keywords(request: KeywordRequest):
    try:
        results = {}
        seed_prompt = PROMPT_TEMPLATES["seed_keywords"].format(
            category=request.category,
            target_platform=request.target_platform,
            language=request.language,
            max_keywords=request.max_keywords,
            difficulty_level=request.difficulty_level
        )
        results["seed_keywords"] = parse_gemini_response(model.generate_content(seed_prompt).text)
        
        competitor_prompt = PROMPT_TEMPLATES["competitor_analysis"].format(category=request.category)
        results["competitor_gaps"] = parse_gemini_response(model.generate_content(competitor_prompt).text)
        
        question_prompt = PROMPT_TEMPLATES["question_keywords"].format(category=request.category, target_platform=request.target_platform)
        results["question_keywords"] = parse_gemini_response(model.generate_content(question_prompt).text)
        
        if supabase:
            store_search_session(request.category, results, {"platform": request.target_platform, "language": request.language})
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"AI Agent Error: {str(exc)}"}
    )

# ========== Health Check ==========
@app.get("/")
async def health_check():
    return {
        "status": "active",
        "model": "gemini-pro",
        "database_connected": bool(supabase)
    }
print("hello this is to test the rabit code review code!!!")