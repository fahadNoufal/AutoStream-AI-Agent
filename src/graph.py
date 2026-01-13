from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.state import State, route_based_on_intent
from src.nodes import (
    classify_user_enquiry_type, 
    reply_to_casual_greeting, 
    ask_user_for_lead_information, 
    extract_lead_data, 
    make_reply_to_enquiry_node
)

def build_graph(retriever):
    builder = StateGraph(State)
    memory = MemorySaver()

    # Nodes
    builder.add_node('classify_user_intent', classify_user_enquiry_type)
    builder.add_node('greeting', reply_to_casual_greeting)
    builder.add_node('inquiry', make_reply_to_enquiry_node(retriever))
    builder.add_node('ask_lead_details', ask_user_for_lead_information)
    builder.add_node('extract_lead_details', extract_lead_data)

    # Edges
    builder.add_edge(START, 'classify_user_intent')
    builder.add_conditional_edges(
        'classify_user_intent',
        route_based_on_intent,
        {
            'lead': 'ask_lead_details',
            'inquiry': 'inquiry',
            'greeting': 'greeting',
            'extract details': 'extract_lead_details'
        }
    )
    builder.add_edge(['inquiry', 'greeting', 'ask_lead_details', 'extract_lead_details'], END)

    return builder.compile(checkpointer=memory)