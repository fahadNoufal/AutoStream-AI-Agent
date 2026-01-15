from langchain_core.messages import HumanMessage
from src.config import KNOWLEDGE_BASE_PATH
from src.vector_store import init_vector_db
from src.retriever import RAGRetriever
from src.graph import build_graph
import sys
import re
import os

def main():
    # Initialize DB & Retriever
    db, embedding_manager = init_vector_db(KNOWLEDGE_BASE_PATH)
    retriever = RAGRetriever(db, embedding_manager)

    # Build Graph
    graph = build_graph(retriever)
    config = {"configurable": {"thread_id": "1"}}

    print("AutoStream Bot Initialized. Type 'quit' to exit.",end='\n\n')
    
    def mock_lead_capture(name, email, platform):
        print(f"Lead captured successfully: {name}, {email}, {platform}")

    # Chat Loop
    while True:
        query = input('Client: ')
        if query.strip().lower() in ['exit', 'q', 'quit']:
            break

        state = {'messages': [HumanMessage(query)]}
        result = graph.invoke(state, config=config)
        
        # Check for completion
        if result.get('user_data') and all(result['user_data'].values()):
            print('Bot:', result['messages'][-1].content)
            captured_lead = result['user_data']
            mock_lead_capture(captured_lead['name'],captured_lead['contact'],captured_lead['platform'])
            break

        result_message = result['messages'][-1].content
        result_message = re.sub(r"[\*\n\t]+", " ", result_message)
        

        print('Bot:',result_message ,end='\n\n')

if __name__ == "__main__":
    main()