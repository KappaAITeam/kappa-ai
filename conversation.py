import os
# from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model_name='llama-3.3-70b-versatile',
    groq_api_key=os.getenv("GROQ_API_KEY"),
)
memory = ConversationBufferMemory(
        return_messages=False,
        ai_prefix="AI",
        human_prefix="Me"
    )
def converse(character_name: str, character_description: str, username: str, prompt: str):
    system_n = f"You have a description of {character_description or 'A help AI bot'}. You will assume the persona of the description seriously"
    system_n += "Your name is {name}."
    system_n += (f"You will be having a conversation with {username}. "
                 f"When convenient you will always include in your "
                 f"conversation the name of who you are chatting with but do not make it frequent.")
    u_n = (f"You will assume the role of AI where your name is {character_name}. The person you will be conversing with is {username} and will assume the role of Me."
           f"{character_name} has a description of {character_description}. In your response you will not include the role prefixed with ':'. "
           f"You will refer the person by name when you have to during your conversations. ")
    u_n += "The following is a conversation between Me and AI:\n\n{history}\n\nMe: {input}\nAI:"

    template = PromptTemplate(
        input_variables=['history', 'input'],  # include history
        template=u_n
    )
    # template = ChatPromptTemplate([
    #     {"role": "system", "content": system_n},
    #     {"role": "human", "content": "Hello {name}, how are you doing?"},
    #     {"role": "ai", "content": "I'm doing well, thanks!"},
    #     {"role": "human", "content": "{user_input}"}
    # ])

    # prompt_value = template.invoke(
    #     {"name": character_name, "user_input": prompt}
    # )
    conversation = ConversationChain(
        llm=llm,
        prompt=template,
        verbose=True,
        memory=memory
    )
    return conversation.predict(input=prompt)
    # return llm.invoke(prompt_value).content