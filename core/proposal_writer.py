import os
from core.logger import bot_logger
from core.llm_client import BaseLLMClient, DeepSeekClient, GeminiLLMClient # Import specific clients

TEMPLATES_DIR = "templates"
DEFAULT_TEMPLATE_FILE = "default.txt"

class ProposalWriter:
    def __init__(self, deepseek_client: DeepSeekClient | None, gemini_llm_client: GeminiLLMClient | None, config: dict, templates_dir=TEMPLATES_DIR):
        self.deepseek_client = deepseek_client
        self.gemini_llm_client = gemini_llm_client
        self.config = config
        self.templates_dir = templates_dir
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            bot_logger.warning(f"Templates directory '{self.templates_dir}' did not exist and was created. Please add proposal templates.")

    def _load_template(self, template_name=DEFAULT_TEMPLATE_FILE):
        """Loads a proposal template from a file."""
        template_path = os.path.join(self.templates_dir, template_name)
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            bot_logger.error(f"Proposal template '{template_path}' not found.")
            # Fallback to a very basic template if default is missing
            if template_name == DEFAULT_TEMPLATE_FILE:
                bot_logger.warning("Using a basic fallback proposal template.")
                return "Hello {client_name},\n\nI am interested in your project: {job_title}.\nMy bid is {budget}.\n\nRegards."
            return None
        except Exception as e:
            bot_logger.error(f"Error loading proposal template '{template_path}': {e}")
            return None

    def generate_proposal(self, job_data, template_name=DEFAULT_TEMPLATE_FILE):
        """
        Generates a proposal using an LLM, tailored to the job_data.
        The old template system can be a fallback or used for structure if needed.
        """
        bot_logger.info(f"Generating LLM-based proposal for job: {job_data.get('title', 'N/A')}")

        job_title = job_data.get('title', 'N/A')
        job_description = job_data.get('description', 'No description provided.')
        job_budget = job_data.get('budget', 'N/A') # Raw budget string
        bid_amount = job_data.get('bid_amount', self.config.get("min_pay", 10)) # Calculated bid amount
        profile_name = self.config.get("profile_name", "a skilled freelancer")
        
        # Construct a prompt for the LLM
        # This prompt engineering is crucial for good results.
        prompt = f"""
        You are an expert proposal writer for freelance jobs.
        Write a concise, professional, and compelling proposal for the following job.
        Highlight how my skills align with the project requirements.
        Keep the tone friendly yet professional.
        Do not use overly complex language.
        You can include a sentence about relevant past experience (you can make this up if needed, but keep it plausible).
        My profile name is: {profile_name}.
        The proposed bid amount for this project is: ${bid_amount}.

        Job Title: {job_title}
        Job Budget (as listed by client): {job_budget}
        Job Description:
        ---
        {job_description}
        ---
        Generate the proposal text now.
        """

        generated_text = None
        
        # Try DeepSeek first
        if self.deepseek_client:
            try:
                bot_logger.info(f"Attempting proposal generation with DeepSeek for job {job_data.get('job_id')}.")
                generated_text = self.deepseek_client.generate_text(prompt)
            except ConnectionError as e: # Catch specific error for quota/rate limit
                bot_logger.warning(f"DeepSeek failed (likely quota/rate limit): {e}. Trying Gemini.")
                generated_text = None # Ensure it's None to trigger next fallback
            except Exception as e:
                bot_logger.error(f"Unexpected error with DeepSeek client: {e}")
                generated_text = None

        # If DeepSeek fails or is not available, try Gemini
        if not generated_text and self.gemini_llm_client:
            try:
                bot_logger.info(f"Attempting proposal generation with Gemini for job {job_data.get('job_id')}.")
                generated_text = self.gemini_llm_client.generate_text(prompt)
            except ConnectionError as e:
                bot_logger.warning(f"Gemini failed (likely quota/rate limit): {e}. Falling back to template.")
            except Exception as e:
                bot_logger.error(f"Unexpected error with Gemini client: {e}")

        if not generated_text: # Fallback to template if both LLMs fail
            bot_logger.error(f"LLM failed to generate proposal for job {job_data.get('job_id')}. Falling back to template.")
            # Fallback to old template method if LLM fails
            template_content = self._load_template(template_name)
            if not template_content:
                return "Error: Could not load proposal template or generate via LLM."
            # Ensure job_data has all keys the template might expect
            job_data_for_template = job_data.copy()
            job_data_for_template.setdefault('client_name', 'Hiring Manager') # Ensure client_name exists
            job_data_for_template.setdefault('greeting_name_part', f" {job_data_for_template['client_name']}," if job_data_for_template['client_name'] != 'Hiring Manager' else ",")
            job_data_for_template.setdefault('profile_name', profile_name)
            job_data_for_template.setdefault('bid_amount', bid_amount)
            job_data_for_template.setdefault('budget', job_budget)
            job_data_for_template.setdefault('title', job_title)
            job_data_for_template.setdefault('generic_skills_statement', "I have relevant experience.")
            job_data_for_template.setdefault('default_bid_text_segment', "My bid is")
            
            try:
                return template_content.format(**job_data_for_template)
            except KeyError as e:
                bot_logger.error(f"KeyError formatting fallback template: {e}. Missing key in job_data_for_template.")
                return f"Error: Fallback template formatting failed due to missing key: {e}."

        return generated_text