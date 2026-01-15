from typing import List, Dict, Any

class RAGRetriever:
    def __init__(self, vector_store, embedding_manager):
        # Initializing the retriever
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager

    def retrieve(self, query: str, top_k: int = 4) -> str:
        query_embedding = self.embedding_manager.generate_embeddings([query])[0]
        results = self.vector_store.query(query_embeddings=[query_embedding.tolist()], n_results=top_k)
        
        if not results['ids']:
            return "No relevant documents found."
        
        # Format results into a string for the LLM
        return "\n\n".join(results['documents'][0])