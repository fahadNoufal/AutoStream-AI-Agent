from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_intent: Literal['lead', 'inquiry', 'greeting', 'extract details']
    user_data: dict

def get_chat_history(state: State):
    return ['human: '+s.content if isinstance(s, HumanMessage) else 'bot: '+s.content for s in state['messages']]

def route_based_on_intent(state: State):
    intent_raw = state['user_intent'].content.lower().strip()
    
    if 'high-intent' in intent_raw: return 'lead'
    if 'product' in intent_raw or 'inquiry' in intent_raw: return 'inquiry'
    if 'extract' in intent_raw: return 'extract details'
    return 'greeting'   