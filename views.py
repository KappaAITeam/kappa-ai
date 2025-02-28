import os
import bcrypt
import datetime
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from typing import List
from model import *
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Groq API
llm = ChatGroq(api_key=GROQ_API_KEY,
               model="llama-3.3-70b-versatile",
               temperature=0.2,
               max_retries=2)

# Initialize FastAPI
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# AI instruction template
template_string = """ 
You're a chat buddy named Maggi, ready to keep your friend company. 
Respond to the user input in a style that is {style}.\n

user:{input}
"""

# AI response style
response_style = """British English in a calm and respectful tone."""

# Instantiate prompt
prompt_template = ChatPromptTemplate.from_template(
    template_string
)

# Predefined AI characters (unchanged)
PREDEFINED_CHARACTERS = [
    {"name": "Historian", "description": "Discusses historical events and their significance."},
    {"name": "Philosopher", "description": "Explores deep, thought-provoking questions."},
    {"name": "Comedian", "description": "Adds humor and light-hearted banter."},
    {"name": "Motivational Coach",
        "description": "Provides encouragement and life advice."},
    {"name": "Science Expert",
        "description": "Talks about scientific topics and discoveries."},
    {"name": "Fiction Writer", "description": "Tells stories and explores creative ideas."},
    {"name": "Travel Guide",
        "description": "Shares travel tips, destinations, and cultural insights."}
]


# function to fetch predefined characters
@app.get("/predefined", response_model=List[dict])
async def get_predefined_characters():
    """Retrieve predefined AI characters."""
    return PREDEFINED_CHARACTERS


# Function to create new user
@app.post("/register")
def register_user(request: CreateUser):
    db = SessionLocal()
    hash_password = bcrypt.hashpw(request.password.encode(
        "utf-8"), bcrypt.gensalt()).decode("utf-8")
    db_user = db.query(User).filter(User.username == request.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = User(username=request.username, hashed_password=hash_password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()

    return {"message": "User registered successfully"}

# function to authenticate user


@app.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    # get user from database
    db = SessionLocal()
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not bcrypt.checkpw(form_data.password.encode("utf-8"), user.hashed_password.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token_payload = {
        "sub": user.username,
        "userId": user.id
        #"exp": datetime.datetime() + datetime.timedelta(hours=1)  # Token expires in 1 hour
    }
    # jwt can be use to manage data validity her

    return {"response": token_payload}

# function to store chat message


def store_chat_message(user_id: int, message):
    db = SessionLocal()
    chat_entry = ChatHistory(user_id=user_id, message=message)
    db.add(chat_entry)
    db.commit()
    db.close()


def get_user(password: str, username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or not bcrypt.checkpw(password.encode("utf-8"), user.hashed_password.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"user_id": user.id, "username": user.username}


def retrieve_chat(user_id: int, message: str):
    db = SessionLocal()
    messages = db.query(ChatHistory).filter(
        ChatHistory.user_id == user_id).all()
    db.close()

    if not messages:
        prompt = prompt_template.format_messages(
            style=response_style, input=message
        )
        return prompt

    prompt = {"user_id": user_id, "chat_history": [
        {"message": msg.message} for msg in messages]}
    prompt["chat_history"].append({"message": message})
    new_prompt = []
    for item in prompt["chat_history"]:
        new_prompt.append(item["message"])

    return new_prompt


def chat_with_ai(user_id: str, prompt: str):
    try:
        response = llm.invoke(
            prompt
        )
        for event in response:
            history = store_chat_message(user_id, event[-1])
            return {"response": event[-1]}  # ✅ Return the text response
    except Exception as e:
        return {"error": str(e)}


@app.post("/chat")
async def chat_text(request: Message):
    # get user state
    prompt_user = get_user(request.password, request.username)

    # retreive message
    get_msg = retrieve_chat(prompt_user["user_id"], request.message)

    # chat with AI
    response = chat_with_ai(prompt_user["user_id"], get_msg)

    return response
