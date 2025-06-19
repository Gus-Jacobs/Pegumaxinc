from core.logger import bot_logger
from core.queue_manager import QueueManager
from core.proposal_writer import ProposalWriter
# Import base scraper or type hint for scraper instances if you have a common interface
# from platform_modules.base_scraper import BaseScraper # Example

class JobSubmitter:
    def __init__(self,
                 queue_manager: QueueManager,
                 proposal_writer: ProposalWriter,
                 # scraper: BaseScraper, # No longer pass a default scraper here
                 config: dict):
        self.queue_manager = queue_manager
        self.proposal_writer = proposal_writer
        self.config = config

    async def process_job_for_submission(self, job_data: dict, scraper_instance): # Add scraper_instance parameter, make async
        """
        Generates a proposal for a job and attempts to submit it.
        Updates job status in the queue based on the outcome.
        """
        job_id = job_data['job_id']
        bot_logger.info(f"Processing job {job_id} for submission: {job_data.get('title', 'N/A')[:50]}...")

        # 1. Prepare data for the template
        template_data = job_data.copy()
        client_name_value = template_data.get('client_name')

        # Handle client_name: if it's "N/A (from search)" or None, make it an empty string for a cleaner greeting
        if not client_name_value or "N/A" in client_name_value:
            template_data['greeting_name_part'] = "" # Results in "Hello,"
        else:
            template_data['greeting_name_part'] = f" {client_name_value}," # Results in "Hello Client Name,"
        
        # Add other configurable parts from self.config
        template_data['profile_name'] = self.config.get("profile_name", "[Your Default Profile Name]")
        template_data['generic_skills_statement'] = self.config.get("generic_skills_statement", "I have relevant experience for this project.")
        template_data['default_bid_text_segment'] = self.config.get("default_bid_text_segment", "My bid for this project is")

        # Calculate bid_amount for the template, similar to how it's done in scraper.submit_proposal
        default_bid_for_template = str(self.config.get("min_pay", 10))
        bid_amount_for_template = default_bid_for_template
        
        # Ensure scraper has _parse_budget method accessible
        if hasattr(scraper_instance, '_parse_budget'):
            low_budget, _ = scraper_instance._parse_budget(job_data.get("budget", ""))
            if low_budget is not None:
                proposed_bid_for_template = max(low_budget, float(self.config.get("min_pay", 0)))
                bid_amount_for_template = str(int(proposed_bid_for_template))
        else:
            bot_logger.warning("Scraper instance does not have _parse_budget method. Using default bid for template.")
            # Fallback or error handling if _parse_budget is not available
        
        template_data['bid_amount'] = bid_amount_for_template
        # Ensure the 'budget' key itself (raw budget string) is also passed if your template uses it
        template_data['budget'] = job_data.get("budget", "N/A")
        # Ensure the 'title' (which is the database column name) is available for the template
        template_data['title'] = job_data.get('title', "this project")


        proposal_text = self.proposal_writer.generate_proposal(template_data)

        if "Error: Could not load proposal template." in proposal_text:
            bot_logger.error(f"Failed to generate proposal for job {job_id} due to template error.")
            self.queue_manager.update_job_status(job_id, "error", error_message="Proposal template error")
            return False

        # 2. Submit proposal using the scraper
        submission_successful = await scraper_instance.submit_proposal(job_data, proposal_text)

        # Status is updated within scraper.submit_proposal (to 'proposed' or 'error')
        return submission_successful
