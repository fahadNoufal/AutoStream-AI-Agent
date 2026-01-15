from fastapi import FastAPI, HTTPException, Request
from twilio.rest import Client
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn
import uuid
import re
import os

# Import your existing modules
from langchain_core.messages import HumanMessage
from src.config import KNOWLEDGE_BASE_PATH
from src.vector_store import init_vector_db
from src.retriever import RAGRetriever
from src.graph import build_graph
from src.utils import save_lead_to_excel,log_conversation




# Twilio configuration
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
# This must be your Twilio Sandbox number (e.g., whatsapp:+14155238886)
TWILIO_NUMBER = "whatsapp:+14155238886"

# --- 1. SETUP FASTAPI APP ---
app = FastAPI(title="AutoStream AI Server")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Global variable to hold the graph instance
workflow_app = None

# --- 2. DATA MODELS ---
# This defines what the API expects from the frontend/user
class ChatRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None  # Client sends this to resume a chat

class ChatResponse(BaseModel):
    response: str
    thread_id: str
    lead_captured: bool = False
    lead_data: Optional[Dict] = None
    

# --- 3. LIFESPAN / STARTUP ---
@app.on_event("startup")
def startup_event():
    """
    Initialize the DB and Graph ONCE when the server starts.
    This prevents reloading the Vector DB for every single user request.
    """
    global workflow_app
    print("Initializing Vector DB and Graph...")
    
    # Initialize DB
    db, embedding_manager = init_vector_db(KNOWLEDGE_BASE_PATH)
    retriever = RAGRetriever(db, embedding_manager)
    
    # Build Graph (Ensure your build_graph uses checkpointer=MemorySaver)
    workflow_app = build_graph(retriever)
    print("✅ AutoStream Graph Ready!")


def send_whatsapp_message(to_number: str, body_text: str):
    """Helper to send message back via Twilio"""
    try:
        # Twilio requires text to be strictly under 1600 chars sometimes, 
        # but WhatsApp supports more. We truncate just in case or split logic could be added.
        message = twilio_client.messages.create(
            from_=TWILIO_NUMBER,
            body=body_text,
            to=to_number
        )
        print(f"Sent message SID: {message.sid}")
    except Exception as e:
        print(f"Error sending WhatsApp: {e}")


# --- 4. API ENDPOINT ---
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    global workflow_app
    thread_id = request.thread_id or str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {'messages': [HumanMessage(content=request.query)]}
    
    try:
        result = workflow_app.invoke(input_state, config=config)
        
        # Get Bot Response
        bot_message = result['messages'][-1].content
        
        # Optional: Clean text (remove markdown like your main.py)
        clean_response = re.sub(r"[\*\t]+", " ", bot_message).strip()

        # E. Check for Lead Capture Completion
        lead_data = result.get('user_data', {})
        is_captured = False
        
        # Check if lead data exists and has no empty values
        if lead_data and all(lead_data.values()):
            is_captured = True
            save_lead_to_excel(lead_data)
            # Here you would typically trigger a webhook or save to SQL DB
            print(f"Lead Captured in Thread {thread_id}: {lead_data}")

        return ChatResponse(
            response=clean_response,
            thread_id=thread_id,
            lead_captured=is_captured,
            lead_data=lead_data if is_captured else None
        )

    except Exception as e:
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    """
    Twilio sends a POST request here for every incoming message.
    """
    
    # 1. Parse Incoming Data (Twilio sends Form Data)
    form_data = await request.form()
    user_msg = form_data.get("Body", "").strip()
    sender_number = form_data.get("From", "")  # e.g., 'whatsapp:+19876543210'
    profile_name = form_data.get("ProfileName", "User")

    print(f"📩 Received from {profile_name} ({sender_number}): {user_msg}")
    
    log_conversation(sender_number, "User", user_msg)

    # 2. Setup Thread Config (Phone number = Thread ID)
    # This ensures every user has their own independent chat history
    config = {"configurable": {"thread_id": sender_number}}
    
    # 3. Invoke LangGraph Agent
    try:
        input_state = {'messages': [HumanMessage(content=user_msg)]}
        result = workflow_app.invoke(input_state, config=config)
        
        # 4. Get Bot Response
        bot_response = result['messages'][-1].content
        
        # Optional: Clean text format
        clean_response = re.sub(r"[\*\n\t]+", " ", bot_response).strip()
        
        user_data = result.get('user_data', {})
        is_captured = bool(user_data and all(user_data.values()))
        
        # 5. Send Reply
        send_whatsapp_message(sender_number, clean_response)
        
        log_conversation(
            phone_number=sender_number, 
            sender="Bot", 
            message=clean_response, 
            user_details=user_data, 
            lead_captured=is_captured
        )
        
        # 6. Check for Lead Capture
        lead_data = result.get('user_data', {})
        if lead_data and all(lead_data.values()):
            
            lead_data['sender_number'] = sender_number
            lead_data['profile_name'] = profile_name
            
            print(f"LEAD CAPTURED: {lead_data}")
            # TODO: Add your Excel/DB save logic here
            save_lead_to_excel(lead_data)

    except Exception as e:
        print(f"❌ Error processing message: {e}")
        send_whatsapp_message(sender_number, "Sorry, I'm having trouble processing that right now.")

    return {"status": "success"}

# # --- 5. RUN SERVER ---
if __name__ == "__main__":
    # Workers=1 is fine for MemorySaver. 
    # For true concurrent scaling with multiple workers, you need Postgres checkpointer.
    uvicorn.run(app, host="0.0.0.0", port=8080)