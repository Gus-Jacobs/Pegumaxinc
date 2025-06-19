import time
from core.logger import bot_logger
import asyncio # For potential async operations if scraper methods become async

class PlatformManager:
    def __init__(self, scraper_instances: list, config):
        self.scrapers = scraper_instances
        self.config = config
        self.platform_states = {}
        self.platform_order = [] # To maintain a consistent order for rotation

        for scraper in self.scrapers:
            name = scraper.__class__.__name__
            self.platform_order.append(name)
            self.platform_states[name] = {
                'instance': scraper,
                'last_checked_bids_at': 0,
                'has_bids_available_cache': None, # True, False, or None (unknown)
                'last_scraped_for_new_jobs_at': 0,
                'found_new_jobs_last_scrape': None, # True, False, or None
                'cooldown_until_next_new_job_scrape': 0, # Timestamp
                'priority_for_new_work': True # Initially, all are candidates
            }
        self.current_new_work_platform_index = 0

    def _update_bid_status_cache(self, platform_name: str, has_bids: bool):
        if platform_name in self.platform_states:
            self.platform_states[platform_name]['has_bids_available_cache'] = has_bids
            self.platform_states[platform_name]['last_checked_bids_at'] = time.time()

    def _update_new_job_scrape_status(self, platform_name: str, found_new_jobs: bool):
        if platform_name in self.platform_states:
            self.platform_states[platform_name]['found_new_jobs_last_scrape'] = found_new_jobs
            self.platform_states[platform_name]['last_scraped_for_new_jobs_at'] = time.time()
            if not found_new_jobs:
                cooldown_seconds = self.config.get("platform_no_new_jobs_cooldown_seconds", 30 * 60) # e.g., 30 mins
                self.platform_states[platform_name]['cooldown_until_next_new_job_scrape'] = time.time() + cooldown_seconds
                bot_logger.info(f"Platform {platform_name} set to cooldown for new job scraping until {time.ctime(self.platform_states[platform_name]['cooldown_until_next_new_job_scrape'])}.")
            else: # Reset cooldown if new jobs were found
                self.platform_states[platform_name]['cooldown_until_next_new_job_scrape'] = 0


    async def get_platform_for_new_work_acquisition(self) -> object | None:
        """
        Selects the next platform to attempt scraping new jobs and submitting new bids.
        Rotates through platforms, prioritizing those with known available bids and not in cooldown.
        """
        num_platforms = len(self.platform_order)
        if num_platforms == 0:
            return None

        for i in range(num_platforms): # Try each platform once per cycle starting from current_index
            platform_idx_to_check = (self.current_new_work_platform_index + i) % num_platforms
            platform_name = self.platform_order[platform_idx_to_check]
            state = self.platform_states[platform_name]
            scraper_instance = state['instance']

            if time.time() < state['cooldown_until_next_new_job_scrape']:
                bot_logger.info(f"Skipping {platform_name} for new work acquisition (in cooldown).")
                continue

            # Perform a live check for bid availability
            has_bids = await scraper_instance.are_bids_available() # Now async
            self._update_bid_status_cache(platform_name, has_bids) # Update cache

            if has_bids:
                bot_logger.info(f"Platform {platform_name} selected for new work acquisition (bids available).")
                # Update index for next call to ensure rotation
                self.current_new_work_platform_index = (platform_idx_to_check + 1) % num_platforms
                return scraper_instance
            else:
                bot_logger.info(f"Platform {platform_name} has no bids available for new work.")
        
        bot_logger.info("No platforms currently meet criteria for new work acquisition in this rotation.")
        # Still advance the index so next cycle starts with the next platform
        self.current_new_work_platform_index = (self.current_new_work_platform_index + 1) % num_platforms
        return None

    def get_all_scraper_instances(self) -> list:
        """Returns all managed scraper instances for tasks like status checking."""
        return [state['instance'] for state in self.platform_states.values()]

    # Call these methods from the main loop after performing actions
    def report_bid_availability(self, platform_name: str, has_bids: bool):
        self._update_bid_status_cache(platform_name, has_bids)

    def report_new_jobs_scrape_result(self, platform_name: str, found_new_jobs: bool):
        self._update_new_job_scrape_status(platform_name, found_new_jobs)
