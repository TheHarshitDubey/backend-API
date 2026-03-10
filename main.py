from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./scam_shield.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String)
    message = Column(String)
    is_scam = Column(Boolean)
    confidence = Column(Float)
    reply = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)


load_dotenv()
print("ENV LOADED:", os.getenv("GEMINI_API_KEY"))
genai.configure(api_key=os.getenv("Gemini_API_Key"))
print("Configured Gemini")
model=genai.GenerativeModel("models/gemini-flash-latest")


app=FastAPI(title="Scam Detection API",
    description="Backend API that analyzes messages and detects potential scams using AI",
    version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"Status ":"Running API"}


class chatRequest(BaseModel):
    message:str
    user_id: str

@app.post("/chat")
async def chat(request: chatRequest):

    prompt = f"""
    You are a scam detection AI.

    Respond ONLY in valid JSON format like this:

    {{
      "is_scam": true or false,
      "confidence": number between 0 and 1,
      "reply": "short explanation"
    }}

    Message:
    {request.message}
    """

    try:
        response = await model.generate_content_async(prompt)
        ai_text = response.text.strip()

        parsed_response = json.loads(ai_text)

        db = SessionLocal()

        scan = Scan(
            user_id=request.user_id,
            message=request.message,
            is_scam=parsed_response["is_scam"],
            confidence=parsed_response["confidence"],
            reply=parsed_response["reply"]
        )

        db.add(scan)
        db.commit()
        print("Saved to database")

        db.close()


        return parsed_response

    except Exception as e:
        return {
            "error": "AI processing failed",
            "details": str(e)
        }
    
@app.post("/generate-reply")
async def generate_reply(request: chatRequest):

    prompt = f"""
    You are a cybersecurity assistant.

    The following message was identified as a scam:

    "{request.message}"

    Generate a safe and smart response that:
    - Does not reveal personal information
    - Does not share OTP
    - Politely declines
    - Optionally wastes scammer time without giving real data

    Return only the reply text.
    """

    try:
        response = await model.generate_content_async(prompt)
        return {"generated_reply": response.text.strip()}

    except Exception as e:
        return {"error": str(e)}   

@app.get("/history/{user_id}")
def get_history(user_id:str):
    db = SessionLocal()
    scans = db.query(Scan)\
        .filter(Scan.user_id==user_id)\
    .order_by(Scan.timestamp.desc())\
    .all()
    db.close()

    return [
        {
            "id": scan.id,
            "message": scan.message,
            "is_scam": scan.is_scam,
            "confidence": scan.confidence,
            "reply": scan.reply,
            "timestamp": scan.timestamp
        }
        for scan in scans
    ]

@app.get("/stats/{user_id}")
def get_stats():
    db = SessionLocal()
   
    
    total_scans = db.query(Scan).count()

    scams = db.query(Scan).filter(Scan.is_scam == True).count()

    safe = db.query(Scan).filter(Scan.is_scam == False).count()

    high_risk_rate = 0

    if total_scans > 0:
        high_risk_rate = round((scams / total_scans) * 100)
    db.close()
    return {
        "total_scans": total_scans,
        "scams_detected": scams,
        "safe_messages": safe,
        "high_risk_rate": high_risk_rate
    }
