import json
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from src.config import GEMINI_MODEL
from src.state import get_chat_history,State


llm = init_chat_model(GEMINI_MODEL)


def classify_user_enquiry_type(state:State) -> State:
    
    # retrieving past n messages by the user to find out the user intent
    # user_chat = state['messages']
    chat_history = str(get_chat_history(state))
    
    prompt = [ SystemMessage("""
                    You are an intent classification agent:
                    1. Casual greeting
                    2. Product or pricing inquiry
                    3. High-intent lead
                    4. Extract lead details

                    CRITICAL OUTPUT RULES:
                    - Output ONLY the category name. 
                """),
              
              HumanMessage(chat_history)
            ]
    
    intent = llm.invoke(prompt)

    return {'user_intent': intent}

def reply_to_casual_greeting(state:State) -> State:
    
    # user_chat = state['messages'][-1].content
    chat_history = str(get_chat_history(state))
    
    
    prompt = [
        SystemMessage("""
                    You are the Sales & Onboarding Specialist for **AutoStream**, a SaaS platform that automates video editing for creators.

                    **Your Goal:**
                    Secure a user sign-up. However, if the user seems unsure, your secondary goal is to educate them to build trust.

                    **Instructions for Handling Greetings:**
                    When a user sends a greeting 
                    1.  **Warm Welcome:** Greet them professionally and enthusiastically.
                    2.  **Value Hook:** Briefly mention that AutoStream (we saves creators hours of editing time)
                    3.  Invite them sign up to create a free account to test it out (our aim is to capture the user details)
                    4.  Do not give long response.
                    5.  "ONLY IF USER WANT TO SIGNUP" : ask their name, contact and the platform they create video

                    **Tone:**
                    Helpful, knowledgeable, and inviting.

                    """),
        HumanMessage(chat_history)
    ]    
    state = {'messages':[llm.invoke(prompt)]}
    
    return state

import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from langchain_core.messages import SystemMessage, HumanMessage

def ask_user_for_lead_information(state: State):
    
    chat_history = str(get_chat_history(state))
    
    prompt = [
        SystemMessage(f"""
            You are the **AutoStream Sign-Up Assistant**.
            
            **Goal:** Ask the user to provide their registration details to sign up.
            
            **Required Details:**
            1. Name
            2. Email (or Contact Number)
            3. Creator Platform (e.g., YouTube, Instagram, TikTok)
            
            **Instructions:**
            - Check the chat history below.
            - If NO details are present, ask for all three in one friendly, energetic sentence.
            - If SOME details are present (e.g., user already said "I'm John"), ask ONLY for the missing details.
            - Keep it brief and conversational.
        """),
        HumanMessage(chat_history)
    ]
    
    response = llm.invoke(prompt)
    
    return {'messages': [response]}


def extract_lead_data(state: State) -> dict:
    
    chat_history = str(get_chat_history(state))
    
    prompt = [
        SystemMessage("""
            You are the Data Extraction Engine for AutoStream.
            Your Goal: Analyze the chat history and extract user details into JSON.
            
            Extraction Rules:
            - Name: Full name or null
            - Contact: Email/Phone or null
            - Platform: Content platform or null
            
            Output Format: ONLY JSON. No text.
            Example: {"name": "John", "contact": null, "platform": "YouTube"}
        """),
        HumanMessage(content=chat_history)
    ] 
    
    # 3. Invoke LLM & Parse
    response = llm.invoke(prompt).content
    cleaned_json = response.replace('```json', '').replace('```', '').strip()
    
    try:
        lead_data = json.loads(cleaned_json)
    except json.JSONDecodeError:
        lead_data = {"name": None, "contact": None, "platform": None}

    # Check if ALL values are present
    if all(lead_data.values()):
        # All fields have data -> Success
        success_msg = AIMessage(content='Successfully signed-up! Welcome to AutoStream.')
    else:
        # Something is missing -> Identify what is missing
        missing_fields = [key for key, value in lead_data.items() if not value]
        success_msg = AIMessage(content=f"Could you please provide your {', '.join(missing_fields)} to complete the signup?")
        
    return {
        'messages': [success_msg], 
        'user_data': lead_data
    }

def make_reply_to_enquiry_node(rag_retriever):
    
    def reply_to_enquiry(state:State)->State:
        query_topic = get_chat_history(state)[-1]
        context = rag_retriever.retrieve(query_topic)
        
        chat_history = str(get_chat_history(state))
        
        prompt = [
            SystemMessage(f"""
                    You are the **AutoStream Sales AI**.

                    **Goal:** Answer accurately using the Context provided, while persuading the user to sign up (user should say yes to signup).

                    **Instructions:**
                    1. **Source of Truth:** Use ONLY the provided Context.
                    2. **IF THE CONTEXT IS NOT PROVIDED**: respond that you don't have the specific details on that right now, and tell them the known things.
                    3. **Sell the Benefit:** Don't just list specs. Explain *why* the feature helps them (e.g., "4K makes your content look professional").
                    4. **Closing:** Always end with a brief Call to Action (e.g., "Ready to try it out?").
                    
                    CONTEXT:
                    {context}
                    """),
            HumanMessage(chat_history)
        ]
        
        state = {'messages':[llm.invoke(prompt)]}
        return state
    return reply_to_enquiry