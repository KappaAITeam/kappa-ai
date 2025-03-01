from fastapi import FastAPI
from pydantic import BaseModel
from conversationTest import converse

app = FastAPI()

class ChatRequest(BaseModel):
    userId: str
    username: str
    prompt: str
    characterName: str
    characterDescription: str

# user_id,name,message,character_name,character_description

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/chat")
async def handle_conversation(body: ChatRequest):
    response = converse(
        character_name=body.characterName,
        username=body.username,
        prompt=body.prompt,
        character_description=body.characterDescription
    )
    return {
        "response": response
    }