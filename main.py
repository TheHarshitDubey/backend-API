from fastapi import FastAPI

app=FastAPI()
@app.get("/")
def root():
    return {"Status ":"Running API"}
from pydantic import BaseModel

class chatRequest(BaseModel):
    message:str

@app.post("/chat")
def chat(request:chatRequest):
   text= request.message.lower()
   is_scam="win" in text
   return {"ai reply":"Scam Detected" if is_scam else "Safe Message",
           "is Scan":is_scam,
           "confidence ":0.9 if is_scam else 0.1}