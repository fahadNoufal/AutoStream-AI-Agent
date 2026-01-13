# AutoStream AI - Intelligent Sales & Lead Gen Agent

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-Stateful_AI-orange)
![Gemini](https://img.shields.io/badge/AI-Gemini_2.0_Flash-green)
![RAG](https://img.shields.io/badge/RAG-ChromaDB-purple)

**AutoStream AI** is a stateful conversational agent designed to automate the sales process for a SaaS video platform. Unlike simple chatbots, it uses a directed graph architecture to actively guide users from casual inquiries to signed-up leads.

---

## 🌟 Key Features

* **🧠 Intelligent Intent Detection**: Dynamically classifies user input into categories (Greeting, Inquiry, High-Intent Lead) to route the conversation effectively.
* **📚 RAG (Retrieval-Augmented Generation)**: Answers specific product questions (pricing, features, policies) by retrieving data from a local knowledge base (`knowledgeBase.json`).
* **🎣 Active Lead Capture**: Identifies high-intent users and triggers a dedicated flow to collect their Name, Email, and Platform.
* **💾 Contextual Memory**: Remembers conversation history across turns using LangGraph's memory, allowing for natural, multi-turn dialogue.
* **🧩 Modular Architecture**: Built with a clean `src/` structure, separating logic for vector storage, graph nodes, and configuration.

---

## 📂 Project Structure

```text
autostream-bot/
│
├── data/
│   └── knowledgeBase.json       # Source of truth for RAG (Pricing, Policies)
│
├── src/                         # Application Source Code
│   ├── __init__.py
│   ├── config.py                # Environment variables & paths
│   ├── vector_store.py          # ChromaDB initialization & embedding logic
│   ├── retriever.py             # RAG retrieval logic
│   ├── nodes.py                 # Core agent functions (LLM calls)
│   ├── state.py                 # StateGraph definitions & routing
│   └── graph.py                 # Graph compilation
│
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── .env                         # API Keys (Not included in repo)
└── README.md                    # Project documentation
```

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.10 or higher
- A Google Cloud API Key (for Gemini)

### 2. Clone the Repository

```bash
git clone [https://github.com/yourusername/autostream-bot.git](https://github.com/yourusername/autostream-bot.git)
cd autostream-bot
```

### 3. Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it (Linux/Mac)
source venv/bin/activate

# Activate it (Windows)
venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Create a file named .env in the root directory and add your Google API key:

```
GOOGLE_API_KEY=your_google_api_key_here
```

## Usage

Run the main script to start the interactive CLI bot:

```bash
python main.py
```

Note: The first time you run this, it will automatically:

1. Initialize the ChromaDB vector store.
2. Ingest the data from data/knowledgeBase.json.
3. Generate embeddings locally (this may take a few seconds).

Example Interaction:

```
You: hi there
Bot: Hello! 👋 Welcome to AutoStream! We save creators hours on video editing. Want to sign up for a free account and see how it works?

You: befor that i need to know how much your base plan cost
Bot: The Basic Plan is $29 per month. With it, you get 720p resolution, which is great for standard quality viewing, a limit of 10 videos, and standard email support. Ready to try it out?

You: what if i wasnt satisfied
Bot: We want you to be happy with AutoStream! If you're not satisfied, we offer a refund within the first 7 days of your subscription. This gives you a chance to really explore the platform and see if it meets your needs. Ready to sign up?

You: shure
Bot: Awesome! To get you all set up, what's your name, email (or contact number), and which platform do you create content on?

You: i am fahad Noufal 
Bot: Could you please provide your contact, platform to complete the signup?

You: email is examplemail@gmail.com and i create for youtube
Bot: Successfully signed-up! Welcome to AutoStream.

Lead captured successfully: fahad Noufal, examplemail@gmail.com, youtube
```

## 🏗️ Architecture Explained

This project uses **LangGraph** to manage the conversation flow as a flexible state machine, avoiding rigid loops.

![LangGraph Flow](resource/graph.png)

1.  **START**: User input is received.
2.  **Classify Intent**: At **every turn**, the `classify_user_intent` node analyzes the text and dynamically routes to one of four paths:
    * **Greeting**: Handles casual hellos and opens the conversation.
    * **Inquiry**: Uses **RAG** (ChromaDB + Gemini) to answer specific questions based on the JSON knowledge base.
    * **Lead**: Identifies high-intent users expressing interest in signing up.
    * **Extract Details**: parses user input to capture specific data slots (Name, Email, Platform). [design philosophy explained below]
3.  **Memory**: The graph utilizes `MemorySaver` to persist the conversation state, ensuring the bot remembers context (like a name mentioned earlier) even if the topic changes.
4. **Trigger Actions**: User lead information is recieved, it triggers a lead_captured function call.

#### Design Philosophy:
Non-Blocking Flows Instead of trapping users in a rigid data-collection loop, this architecture re-evaluates user intent at every turn. This allows for non-linear conversations: users can pause the sign-up process to ask clarifying questions ("Is it free?") and resume seamlessly. This mimics human interaction, reduces frustration, and increases the likelihood of lead conversion by addressing doubts in real-time.

## Customization

- Change the Knowledge Base: Edit data/knowledgeBase.json to update pricing, plans, or policies. Delete the vector-db folder to force a rebuild on the next run.

- Switch LLM: Open src/config.py to change the model (e.g., from gemini-2.0-flash to gpt-4o via LangChain).

- Adjust Prompts: All system prompts are located in src/nodes.py.