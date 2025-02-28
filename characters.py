from fastapi import FastAPI
from typing import List


# Initialize FastAPI
app = FastAPI()

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


@app.get("/predefined", response_model=List[dict])
async def get_predefined_characters():
    """Retrieve predefined AI characters."""
    return PREDEFINED_CHARACTERS
