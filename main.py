import json
from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai

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

        return parsed_response

    except Exception as e:
        return {
            "error": "AI processing failed",
            "details": str(e)
        }
