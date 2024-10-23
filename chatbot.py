import os
import streamlit

from typing import Sequence
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, trim_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from utils.search import web_search


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    language: str


load_dotenv()
llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"))
workflow = StateGraph(state_schema=State)

trimmer = trim_messages(
    max_tokens=65,
    strategy="last",
    token_counter=llm,
    include_system=True,
    allow_partial=False,
    start_on="human",
)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant. Answer all questions to the best of your ability in {language}.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)


def call_model(state: State):
    chain = prompt | llm
    trimmed_messages = trimmer.invoke(state["messages"])
    response = chain.invoke({
        "messages": trimmed_messages,
        "language": state["language"]
    })
    return {"messages": [response]}


workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
test_config = {"configurable": {"thread_id": "abc123"}}

if "history" not in streamlit.session_state:
    streamlit.session_state["history"] = []

streamlit.title("Interactive Langchain Chatbot")
user_input = streamlit.text_input("Ask a question:")

if user_input:
    input_messages = streamlit.session_state["history"] + [HumanMessage(user_input)]
    stream_input = {"messages": input_messages, "language": "English"}
    chatbot_response = ""
    response_placeholder = streamlit.empty()

    for chunk, metadata in app.stream(stream_input, test_config, stream_mode="messages"):
        if isinstance(chunk, AIMessage):
            chatbot_response += chunk.content
            response_placeholder.text(chatbot_response)

    streamlit.session_state["history"].append(HumanMessage(user_input))
    streamlit.session_state["history"].append(AIMessage(chatbot_response))

    if "search" in user_input.lower():
        search_result = web_search(user_input)
        streamlit.text(f"Web search result: {search_result}")

for message in streamlit.session_state["history"]:
    if isinstance(message, HumanMessage):
        streamlit.write(f"You: {message.content}")
    elif isinstance(message, AIMessage):
        streamlit.write(f"Bot: {message.content}")
