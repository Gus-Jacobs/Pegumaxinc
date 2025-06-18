from core.logger import bot_logger
import os # For environment variables if you choose to use them for API keys
from deepseek import DeepSeekAPI # Using the suggested import name
import google.generativeai as genai

class BaseLLMClient:
    def __init__(self, api_key=None, config=None):
        self.api_key = api_key
        self.config = config if config else {}

    def generate_text(self, prompt: str, max_tokens: int = 500) -> str | None:
        """
        Generates text based on a given prompt.
        This method should be overridden by specific LLM client implementations.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

class PlaceholderLLMClient(BaseLLMClient):
    """
    A placeholder LLM client for development and testing.
    Simulates an LLM response.
    """
    def generate_text(self, prompt: str, max_tokens: int = 500) -> str | None:
        bot_logger.info(f"PlaceholderLLMClient received prompt (first 100 chars): {prompt[:100]}...")
        
        # Simulate a response based on keywords in the prompt
        if "python script" in prompt.lower():
            response = f"Dear [Client Name],\n\nI have reviewed your project for a Python script. With my extensive experience in Python development, I am confident I can deliver a high-quality solution. My bid is [Bid Amount].\n\nI can start immediately and look forward to discussing this further.\n\nSincerely,\n[Your Name]"
        elif "data entry" in prompt.lower():
            response = f"Hello [Client Name],\n\nI understand you need assistance with data entry. I am meticulous and efficient, ensuring accuracy and timely completion. My proposed bid is [Bid Amount].\n\nThank you for considering my application.\n\nBest regards,\n[Your Name]"
        else:
            response = f"Dear [Client Name],\n\nI am very interested in your project: [Job Title]. I have the skills and experience necessary to complete this task successfully. My bid is [Bid Amount].\n\nI am available to start as soon as possible.\n\nThanks,\n[Your Name]"
        
        # Replace placeholders that would typically be part of the prompt or known data
        # In a real scenario, the LLM would ideally incorporate these naturally.
        # For this placeholder, we'll do a simple replace.
        response = response.replace("[Client Name]", self.config.get("placeholder_client_name", "Hiring Manager"))
        response = response.replace("[Your Name]", self.config.get("profile_name", "Freelancer"))
        # [Job Title] and [Bid Amount] would ideally be part of the prompt for the LLM.
        bot_logger.info(f"PlaceholderLLMClient generated response (first 100 chars): {response[:100]}...")
        return response

class DeepSeekClient(BaseLLMClient):
    def __init__(self, api_key, config=None):
        super().__init__(api_key, config)
        if not self.api_key:
            raise ValueError("DeepSeek API key is required.")
        # The official DeepSeek client is pre-configured for its API endpoint.
        self.client = DeepSeekAPI(api_key=self.api_key)

    def generate_text(self, prompt: str, max_tokens: int = 500) -> str | None:
        bot_logger.info(f"DeepSeekClient attempting to generate text (prompt starts: {prompt[:50]}...).")
        try:
            response = self.client.completions.create(
                model="deepseek-chat", # Or "deepseek-coder" if more appropriate for some tasks
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7 # Adjust as needed
            )
            if response.choices and response.choices[0].message and response.choices[0].message.content:
                generated_content = response.choices[0].message.content.strip()
                bot_logger.info(f"DeepSeekClient successfully generated text (starts: {generated_content[:50]}...).")
                return generated_content
            else:
                bot_logger.error("DeepSeek API response was empty or not in expected format.")
                return None
        except Exception as e:
            # Check for specific rate limit or out-of-tokens errors if the API provides them
            if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                bot_logger.warning(f"DeepSeek API rate limit or quota exceeded: {e}")
                # Consider raising a specific exception to be caught by ProposalWriter for fallback
                raise ConnectionError("DeepSeek quota/rate limit") from e # Example custom error
            bot_logger.error(f"Error during DeepSeek API call: {e}")
            return None

class GeminiLLMClient(BaseLLMClient):
    def __init__(self, api_key, config=None):
        super().__init__(api_key, config)
        if not self.api_key:
            raise ValueError("Gemini API key is required.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro') # Or other suitable Gemini model

    def generate_text(self, prompt: str, max_tokens: int = 500) -> str | None: # max_tokens might be handled differently by Gemini
        bot_logger.info(f"GeminiLLMClient attempting to generate text (prompt starts: {prompt[:50]}...).")
        try:
            response = self.model.generate_content(prompt)
            if response.text:
                bot_logger.info(f"GeminiLLMClient successfully generated text (starts: {response.text[:50]}...).")
                return response.text.strip()
            bot_logger.error("Gemini API response was empty.")
            return None
        except Exception as e:
            if "quota" in str(e).lower() or "limit" in str(e).lower(): # Basic check
                bot_logger.warning(f"Gemini API quota/rate limit likely exceeded: {e}")
                raise ConnectionError("Gemini quota/rate limit") from e
            bot_logger.error(f"Error during Gemini API call: {e}")
            return None