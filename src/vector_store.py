import json
import chromadb
import numpy as np
from typing import List
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer
from src.config import VECTOR_DB_PATH, EMBEDDING_MODEL

class EmbeddingManager:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self.model = None
        self._load_model()

    def _load_model(self):
        # Loading the model
        try:
            print(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
        except Exception as e:
            print(f"Error loading model {self.model_name}: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        if not self.model:
            raise ValueError("Model not loaded")
        embeddings = self.model.encode(texts)
        return embeddings

    

def load_and_split_data(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)

    docs = []
    for plan in data["plans"]:
        text_content = f"""
        Plan Name: {plan['name']}
        Price: {plan['cost']}
        Resolution: {plan['limits']['resolution']}
        Video Limit: {plan['limits']['videos_per_month']}
        Support Level: {plan['support']}
        """
        docs.append(Document(page_content=text_content.strip(), metadata={"category": "plans", "plan": plan['id']}))

    docs.append(Document(page_content=f"Refund Policy: {data['policies']['refunds']}", metadata={"category": "policies", "type": "refunds"}))
    docs.append(Document(page_content=f"Support Policy: {data['policies']['support_eligibility']}", metadata={"category": "policies", "type": "support"}))
    return docs

def init_vector_db(knowledge_base_path):
    embedding_manager = EmbeddingManager()
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    
    docs = load_and_split_data(knowledge_base_path)
    embeddings = embedding_manager.generate_embeddings([doc.page_content for doc in docs])
    
    db = client.get_or_create_collection(
        name='AutoStream',
        metadata={'description':'Pricing & Policies on AutoStream'}
    )
    
    ids = [str(1000+i) for i in range(len(docs))]
    metadatas = [dict(doc.metadata) for doc in docs]
    db.add(
        ids=ids, 
        embeddings=embeddings.tolist(), 
        metadatas=metadatas, 
        documents=[doc.page_content for doc in docs]
        )
        
    return db, embedding_manager