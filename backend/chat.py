from huggingface_hub import InferenceClient
from dotenv import load_dotenv 
from os import getenv

load_dotenv()
class Chat:
    def __init__(self):
        # Accept either HF_TOKEN (existing) or the more-standard HUGGINGFACEHUB_API_TOKEN
        api_key = getenv("GROQ_TOKEN") or getenv("GORQ_API_TOKEN")

        # Provide a clear error if no API key is configured. The underlying library
        # will produce a confusing StopIteration when provider helpers aren't
        # available, so fail early with a helpful message.
        if not api_key:
            raise EnvironmentError(
                "Groq API token not found. Please set either GROQ_TOKEN or GORQ_API_TOKEN in your environment."
            )

        try:
            self.llm = InferenceClient(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        except Exception as e:
            # Surface creation-time errors clearly
            raise RuntimeError(f"Failed to initialize InferenceClient: {e}") from e

        print(f"HF token configured: {api_key is not None}")
        print("Chat instance initialized successfully")
    
    def response(self, user_message):
        """
        Generate a response based on the user message
        
        Args:
            user_message: String containing the user's message
        
        Returns:
            String response from the AI
        """
        # Add system prompt for investment context
        system_message = {
            "role": "system", 
            "content": "no_think\nYou are an investment assistant helping users understand VOO (Vanguard S&P 500 ETF) and Bitcoin (BTC). Provide clear, concise financial advice suitable for beginners. Focus on explaining concepts like ETFs, cryptocurrency, risk, returns, and diversification. Keep responses under 3-4 sentences."
        }
        
        # Create user message object
        message = {
            "role": "user",
            "content": user_message
        }
        
        # Prepare messages for the API
        try:
            response = self.llm.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[system_message, message],
            )
            print("Response received successfully")
            print(f"Response: {response.choices[0].message.content}")
            content = response.choices[0].message.content

            return {"response": content }
        except Exception as e:
            print(f"Error in chat response: {str(e)}")
            return "I apologize, but I encountered an error. Please try asking your question in a different way."