import os
import logging
from abc import ABC, abstractmethod
from typing import List, Dict
import google.generativeai as genai

class BaseLLMService(ABC):
    @abstractmethod
    def generate_answer(
        self,
        system_prompt: str,
        context: str,
        history: List[Dict[str, str]],
        question: str
    ) -> str :
        """
            Takes the RAG context, chat history, and new question,
            and returns the AI's response as a string.
        """
        pass

class GeminiLLMService(BaseLLMService):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logging.warning("GEMINI_API_KEY is missing from environment variables!")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def generate_answer(
            self, 
            system_prompt: str, 
            context: str, 
            history: List[Dict[str, str]], 
            question: str
        ) -> str:
            full_system_instruction = f"{system_prompt}\n\nCONTEXT FROM DOCUMENTS:\n{context}"
            
            # Gemini expects roles to be 'user' and 'model' (not 'assistant')
            gemini_history = []
            for msg in history:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({
                    "role": role,
                    "parts": [msg["content"]]
                })

            chat = self.model.start_chat(history=gemini_history)

            final_prompt = f"{full_system_instruction}\n\nUSER QUESTION:\n{question}"
            
            response = chat.send_message(final_prompt)
            
            return response.text
    
def get_llm_service() -> BaseLLMService:
    """
    Reads the environment configuration to determine which LLM to use.
    Right now, it defaults to Gemini.
    """
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider == "gemini":
        return GeminiLLMService()
    # elif provider == "openai":
    #     return OpenAILLMService()
    # elif provider == "anthropic":
    #     return AnthropicLLMService()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")