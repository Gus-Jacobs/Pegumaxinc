import os
import json
import re
from core.logger import bot_logger
from platform_modules.freelancer_scraper import FreelancerScraper # To fetch full job details/attachments

PROJECTS_BASE_DIR = "projects"

if not os.path.exists(PROJECTS_BASE_DIR):
    os.makedirs(PROJECTS_BASE_DIR)

def sanitize_filename(name):
    """Sanitizes a string to be used as a valid filename."""
    name = re.sub(r'[^\w\s-]', '', name).strip() # Remove invalid chars
    name = re.sub(r'[-\s]+', '-', name) # Replace spaces/hyphens with a single hyphen
    return name

class TaskHandler:
    def __init__(self, config, queue_manager, scraper_instance: FreelancerScraper):
        self.config = config
        self.queue_manager = queue_manager
        self.scraper = scraper_instance # Needs the scraper to fetch full details/attachments

    def prepare_awarded_job(self, job_data_db: dict):
        """
        Prepares a job folder, downloads attachments, and saves description
        for a job marked "awarded_to_me".
        """
        job_id = job_data_db['job_id']
        job_title = job_data_db.get('title', 'Unknown Job')
        job_url = job_data_db.get('url')

        sanitized_title = sanitize_filename(job_title)
        job_folder_name = f"{sanitized_title}_{job_id}"
        job_project_path = os.path.join(PROJECTS_BASE_DIR, job_folder_name)

        raw_files_path = os.path.join(job_project_path, "raw_input")

        try:
            if not os.path.exists(job_project_path):
                os.makedirs(job_project_path)
                bot_logger.info(f"Created project folder: {job_project_path}")
            if not os.path.exists(raw_files_path):
                os.makedirs(raw_files_path)
                bot_logger.info(f"Created raw input folder: {raw_files_path}")

            # Fetch full job details (including description and attachments)
            # This requires a new method in FreelancerScraper
            full_job_details = self.scraper.get_full_job_details(job_url) # Placeholder

            if not full_job_details:
                bot_logger.error(f"Could not fetch full details for awarded job {job_id} from {job_url}")
                self.queue_manager.update_job_status(job_id, "error", error_message="Failed to fetch full job details post-award")
                return False

            # Save description
            description_file_path = os.path.join(job_project_path, "description.txt")
            with open(description_file_path, "w", encoding="utf-8") as f:
                f.write(full_job_details.get("full_description", "No description fetched."))
            bot_logger.info(f"Saved description.txt for job {job_id}")

            # Download attachments
            attachments = full_job_details.get("attachments", []) # List of dicts: {'name': 'file.pdf', 'url': '...'}
            for attachment in attachments:
                attachment_name = attachment.get('name', f"attachment_{len(os.listdir(raw_files_path))}")
                attachment_url = attachment.get('url')
                if attachment_url:
                    # This requires a download method in the scraper
                    self.scraper.download_file(attachment_url, os.path.join(raw_files_path, attachment_name))
            
            self.queue_manager.update_job_status(job_id, "Queued") # New status: "Queued" for AI processing
            bot_logger.info(f"Job {job_id} ('{job_title}') prepared and status set to Queued.")
            return True
        except Exception as e:
            bot_logger.error(f"Error preparing awarded job {job_id}: {e}")
            self.queue_manager.update_job_status(job_id, "error", error_message=f"Error in post-award prep: {e}")
            return False