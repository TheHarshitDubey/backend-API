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



@app.get("/")
def root():
    return {"Status ":"Running API"}


class chatRequest(BaseModel):
    message:str

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
    

@app.get("/history")
def get_history():
    db = SessionLocal()
    scans = db.query(Scan).order_by(Scan.timestamp.desc()).all()
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

