import bcrypt
from fastapi import FastAPI, HTTPException, Depends
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from typing import List
from model import *
from fastapi.middleware.cors import CORSMiddleware
from conversationTest import converse
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
# default initiate conversation
# after the conversation will appear in history
default_conversation = {
    "sophia12345ai": "You're an AI Assistant and your name is Sophia, with\
        philosophical mind that encourages deep thinking and introspection. \
            Respond in style that is {style}. \
            User request begin after the triple backtick and your \
                responses follows alternatively User:```{input}",

    "leo12345ai": "You're an AI Assistant and your name is Leo, with\
        a creative spirit to inspire your artistic endeavors and imagination. \
            Respond in style that is {style}. \
            User request begin after the triple backtick and your \
                responses follows alternatively User:```{input}",

    "alex12345ai": "You're an AI Assistant and your name is Alex, \
        a motivational coach to help you achieve your goals and stay focused. \
            Respond in style that is {style}. \
            User request begin after the triple backtick and your \
                responses follows alternatively User:```{input}",

    "jamie12345ai": "You're an AI Assistant and your name is Jamie, \
        a friendly companion for everyday conversations and light-hearted chats. \
            Respond in style that is {style}. \
            User request begin after the triple backtick and your \
                responses follows alternatively User:```{input}",

    "morgan12345ai": "You're an AI Assistant and your name is Morgan, \
        a practical advisor for problem-solving and strategic thinking. \
            Respond in style that is {style}.  \
            User request begin after the triple backtick and your \
                responses follows alternatively User:```{input}",

    "harper12345ai": "You're an AI Assistant and your name is Harper, \
        a history enthusiast with knowledge spanning various periods and cultures. \
            Respond in style that is {style}. \
            User request begin after the triple backtick and your \
                responses follows alternatively User:```{input}",

}


# AI response style
response_style = """British English in a calm and respectful tone."""

# Instantiate prompt
# function to handle prompt input
def use_prompt(ai_character_id,style:str,prompt:str):
    prompt_template = ChatPromptTemplate.from_template(
    default_conversation[ai_character_id] ).format_messages(
        style=style, input=prompt
        )
    return prompt_template

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
    hash_password = bcrypt.hashpw(request.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db_user = db.query(User).filter(User.username == request.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    new_user = User(username=request.username, hashed_password=hash_password, image=request.image)

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
        "username": user.username,
        "image": user.image,
        "user_id": user.id
        # "exp": datetime.datetime() + datetime.timedelta(hours=1)  # Token expires in 1 hour
    }
    # jwt can be use to manage data validity her

    return {"response": token_payload}

# function to store chat message
#function to store chat message
def store_chat_message(user_id: int, message:str, ai_character_id:str):
    db = SessionLocal()
    chat_entry=ChatHistory(user_id=user_id,message=message, ai_character_id=ai_character_id)
    db.add(chat_entry)
    db.commit()
    db.close()


def get_user(password: str, username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if not user or not bcrypt.checkpw(password.encode("utf-8"), user.hashed_password.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"user_id": user.id, "username": user.username}


# Retrieve previous conversation
def retrieve_previous_chat(user_id: int, ai_id: str):
    db = SessionLocal()

    if not db.query(AiUserStartChat).filter(
            (AiUserStartChat.user_id == user_id) & (AiUserStartChat.ai_character_id == ai_id)):
        return {"response": ""}

    else:
        messages = db.query(ChatHistory).filter(
            (ChatHistory.user_id == user_id) & (ChatHistory.ai_character_id == ai_id)).order_by(
            ChatHistory.id.asc()).all()
        db.close()
        prompt = {"user_id": user_id, "chat_history": [{"id": msg.id, "message": msg.message} for msg in messages]}
        return prompt["chat_history"]


def retrieve_chat(user_id: int, ai_id: str, message: str):
    db = SessionLocal()
    messages = db.query(ChatHistory).filter(
        (ChatHistory.user_id == user_id) & (ChatHistory.ai_character_id == ai_id)).all()
    db.close()

    if not messages:
        prompt = use_prompt(ai_id, response_style, prompt=message)
        new_chat = AiUserStartChat(user_id=user_id,
                                   ai_character_id=ai_id)  # just to keep user initiate conversation with AI
        db.add(new_chat)
        db.commit()
        db.close()
        return prompt

    prompt = {"user_id": user_id, "chat_history": [{"message": msg.message} for msg in messages]}
    prompt["chat_history"].append({"message": message})
    new_prompt = []
    for item in prompt["chat_history"]:
        new_prompt.append(item["message"])

    return new_prompt


def chat_with_ai(user_id:int, prompt:list, ai_id:str, message:str):
    store_chat_message(user_id=user_id, message=message, ai_character_id=ai_id)
    try:
        response= llm.invoke(
            prompt
        )
        for event in response:
            store_chat_message(user_id=user_id, message=event[-1], ai_character_id=ai_id)
            return {"response":event[-1]}  # ✅ Return the text response
    except Exception as e:
        return {"error": str(e)}

@app.post("/history")
def get_chat_history(request:ConversationHistory):
    #fetch history with user and ai id
    user= get_user(request.password, request.username)
    history = retrieve_previous_chat(user["user_id"], request.ai_id)
    return history


@app.post("/chat")
async def chat_text(request: Message):
    # get user state
    prompt_user = get_user(request.password, request.username)

    # retreive message
    get_msg = retrieve_chat(user_id=prompt_user["user_id"], message=request.message, ai_id=request.ai_character_id)

    # chat with AI
    response = chat_with_ai(user_id=prompt_user["user_id"], prompt=get_msg, ai_id=request.ai_character_id,
                            message=request.message)

    return response

# conversation endpoint using langraph
@app.post("/converse")
async def handle_conversation(body: PromptMessage):
    # chat with AI
    response = converse(
        character_name=body.character_name,
        username=body.username,
        prompt=body.prompt,
        character_description=body.character_description
    )
    return {"message": response}
