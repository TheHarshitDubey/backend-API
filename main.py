from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

genai.configure(api_key=os.getenv("Gemini_API_Key"))
model=genai.GenerativeModel("gemini-pro")


app=FastAPI(title="Scam Detection API",
    description="Backend API that analyzes messages and detects potential scams using AI",
    version="1.0.0")

@app.get("/")
def root():
    return {"Status ":"Running API"}


class chatRequest(BaseModel):
    message:str

@app.post("/chat")
def chat(request:chatRequest):
   text= request.message.lower()
   
   prompt = f"""
    You are a scam detection AI.

    Analyze the following message and answer in this format ONLY:
    is_scam: true or false
    confidence: number between 0 and 1
    reply: short explanation

    Message:
    {text}
    """
   response=model.generate_content(prompt)
   ai_text=response.text
   return {"ai_response":ai_text}