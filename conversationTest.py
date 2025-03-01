import os
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from typing_extensions import TypedDict, Annotated
from dotenv import load_dotenv

load_dotenv()

# Persistent memory checkpoint for LangGraph
memory = MemorySaver()


# Define our state to hold conversation messages.
class State(TypedDict):
    messages: Annotated[list, add_messages]


# Create a global state graph instance.
graph_builder = StateGraph(State)

llm = ChatGroq(
    model_name='llama-3.3-70b-versatile',
    groq_api_key=os.getenv("GROQ_API_KEY"),
)


def chatbot(state: State):
    # Invoke the LLM using the current conversation messages.
    return {"messages": [llm.invoke(state["messages"])]}


def converse(character_name: str, character_description: str, username: str, prompt: str) -> str:
    """
    Builds a conversation with system and developer messages, streams the conversation,
    and returns only the AI's response as a string.
    """
    # Build a system message to set context and persona.
    system_message = (
        "system",
        f"You are {character_name}, a helpful AI with a personality based on '{character_description}'. "
        f"You are conversing with {username}. Always maintain this persona. Refer to the person you are conversing with by the name in the email"
    )

    # Use an allowed message type ('developer') to provide instructions.
    developer_message = (
        "developer",
        "Initiate conversation protocol and follow the provided instructions."
    )

    # Build the initial conversation messages: system, developer, then the user input.
    messages = [system_message, developer_message, ("user", prompt)]

    # Add nodes and edges. If they already exist, ignore the error.
    try:
        graph_builder.add_node("chatbot", chatbot)
    except ValueError as e:
        # Node already exists, so we ignore this error.
        pass

    try:
        graph_builder.add_edge(START, "chatbot")
    except ValueError:
        pass

    try:
        graph_builder.add_edge("chatbot", END)
    except ValueError:
        pass

    graph = graph_builder.compile(checkpointer=memory)
    config = {"configurable": {"thread_id": f"{character_name.replace(' ', '_')}_{username.replace(' ','_')}"}}

    # Stream the conversation events and extract the AI response.
    ai_response = ""
    events = graph.stream({"messages": messages}, config, stream_mode="values")
    for event in events:
        last_message = event["messages"][-1]
        candidate = last_message[1] if isinstance(last_message, tuple) else last_message
        if hasattr(candidate, "content"):
            ai_response = candidate.content
        else:
            ai_response = str(candidate)

    return ai_response
