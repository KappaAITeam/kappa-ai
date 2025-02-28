import os
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine,URL, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import SQLAlchemyError

#Database setup
# DATABASE_URL=URL.create("sqlite",host="localhost",database="chat_history.db")
DATABASE_URL="sqlite:////home/cyberjroid/Documents/Projects/CyberJroid/Tutorials/Divverse/Team Kappa/kappa_backend/chat_history1.db"
engine = create_engine(DATABASE_URL,connect_args={"check_same_thread": False})
SessionLocal=sessionmaker(bind=engine, autoflush=False,autocommit=False)

#SQLAlchemy ORM model
Base= declarative_base()


class User(Base):
    __tablename__ = "user"
    
    id = Column(Integer, primary_key=True, index=True)
    username= Column(String,unique=True, index=True)
    image=Column(String, unique=True, index=True)
    hashed_password= Column(String)

class ChatHistory(Base):
    __tablename__ = "chat_history" 
    
    id = Column(Integer,primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    message = Column(Text)
    
    user= relationship("User")

class AiAvatar(Base):
    __tablename__ = "ai_avatar" 
    
    id = Column(Integer,primary_key=True, index=True)
    image=Column(String, unique=True, index=True)
    
   
    
        
#Create Tables
Base.metadata.create_all(bind=engine)

#OAuth2 for authentication
oauth2_scheme =OAuth2PasswordBearer(tokenUrl="Login")

#pydantic models
class CreateUser(BaseModel):
    username: str
    password: str

class Message(BaseModel):
    password: str
    username: str
    message: str