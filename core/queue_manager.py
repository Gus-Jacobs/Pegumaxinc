import sqlite3
import os
import time
from datetime import datetime, timedelta
from core.logger import bot_logger

DB_DIR = "db"
DB_FILE = os.path.join(DB_DIR, "job_queue.db")

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# Define Job States
class JobState:
    NEW = "new"
    SCRAPED = "scraped"
    FILTERED_OUT = "filtered_out"
    PROPOSED = "proposed"
    VIEWED_BY_CLIENT = "viewed_by_client"
    CHAT_INITIATED = "chat_initiated"
    BID_RATED = "bid_rated"
    AWARDED_TO_ME = "awarded_to_me"
    AWARDED_OTHER = "awarded_other"
    REJECTED_BY_CLIENT = "rejected_by_client"
    NO_REPLY = "no_reply"
    QUEUED_FOR_AI = "queued_for_ai"
    AI_IN_PROGRESS = "ai_in_progress"
    AWAITING_UPLOAD = "awaiting_upload"
    COMPLETED = "completed"
    FAILED_AI = "failed_ai"
    ERROR = "error"
    REVIEW_REQUIRED = "review_required"

class QueueManager:
    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self._create_table()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    title TEXT,
                    url TEXT,
                    client_name TEXT,
                    budget TEXT,
                    status TEXT DEFAULT '{JobState.NEW}', -- Use new job state
                    platform TEXT DEFAULT 'freelancer',
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    proposed_at TIMESTAMP,
                    last_checked_at TIMESTAMP,
                    proposal_text TEXT,
                    error_message TEXT
                )
            """)
            conn.commit()
            bot_logger.info("Job queue table initialized successfully.")
        except sqlite3.Error as e:
            bot_logger.error(f"Database error during table creation: {e}")
        finally:
            if conn:
                conn.close()

    def add_job(self, job_data):
        """Adds a new job to the queue if it doesn't already exist."""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO job_queue (job_id, title, url, client_name, budget, platform, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (job_data['job_id'], job_data['title'], job_data['url'],
                  job_data.get('client_name'), job_data.get('budget'), job_data.get('platform', 'freelancer'), JobState.SCRAPED))
            conn.commit()
            bot_logger.info(f"Added job {job_data['job_id']} to queue.")
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            bot_logger.warning(f"Job {job_data['job_id']} already exists in the queue.")
            return None
        except sqlite3.Error as e:
            bot_logger.error(f"Database error adding job {job_data.get('job_id', 'N/A')}: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_job_status(self, job_id, status, proposal_text=None, error_message=None):
        """Updates the status of a job."""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            timestamp_field = ""
            if status == JobState.PROPOSED:
                timestamp_field = ", proposed_at = CURRENT_TIMESTAMP"

            query = f"""
                UPDATE job_queue
                SET status = ?, last_checked_at = CURRENT_TIMESTAMP {timestamp_field}
            """
            params = [status]

            if proposal_text is not None:
                query += ", proposal_text = ?"
                params.append(proposal_text)
            if error_message is not None:
                query += ", error_message = ?"
                params.append(error_message)

            query += " WHERE job_id = ?"
            params.append(job_id)

            cursor.execute(query, tuple(params))
            conn.commit()
            bot_logger.info(f"Updated job {job_id} status to {status}.")
        except sqlite3.Error as e:
            bot_logger.error(f"Database error updating job {job_id}: {e}")
        finally:
            if conn:
                conn.close()
    def get_jobs_by_status(self, status, platform_filter=None, limit=10):
        """
        Retrieves jobs with a specific status, or all jobs if status is None.
        Optionally filters by platform.
        Orders by scraped_at ascending.
        """
        try:
            conn = self._connect()
            cursor = conn.cursor()
            query = "SELECT * FROM job_queue"
            conditions = []
            params = []

            if status:
                conditions.append("status = ?")
                params.append(status)
            if platform_filter:
                conditions.append("platform = ?")
                params.append(platform_filter)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY scraped_at ASC LIMIT ?"
            params.append(limit)

            cursor.execute(query, tuple(params))
            jobs = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in jobs]
        except sqlite3.Error as e:
            bot_logger.error(f"Database error fetching jobs (status: {status}, platform: {platform_filter}): {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_job_by_url(self, url: str):
        """Retrieves a single job by its URL."""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM job_queue WHERE url = ?", (url,))
            job = cursor.fetchone()
            if not job:
                return None
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, job))
        except sqlite3.Error as e:
            bot_logger.error(f"Database error fetching job by url {url}: {e}")
            return None # Return None on error, consistent with no job found
        finally:
            if conn:
                conn.close()

    def get_all_active_jobs(self, limit=50):
        """Retrieves all jobs not in a final state, ordered by scraped_at."""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM job_queue 
                WHERE status NOT IN (?, ?, ?, ?, ?, ?) 
                ORDER BY scraped_at ASC 
                LIMIT ?
            """, (JobState.NO_REPLY, JobState.COMPLETED, JobState.ERROR, 
                  JobState.FILTERED_OUT, JobState.FAILED_AI, JobState.AWARDED_OTHER, 
                  limit))
            jobs = cursor.fetchall()
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in jobs]
        except sqlite3.Error as e:
            bot_logger.error(f"Database error fetching all active jobs: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_active_job_count(self):
        """Gets the count of jobs that are not in a final state (e.g., 'no_reply', 'completed', 'error')."""
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM job_queue WHERE status NOT IN (?, ?, ?, ?, ?, ?)",
                           (JobState.NO_REPLY, JobState.COMPLETED, JobState.ERROR, JobState.FILTERED_OUT, JobState.FAILED_AI, JobState.AWARDED_OTHER))
            return cursor.fetchone()[0]
        except sqlite3.Error as e:
            bot_logger.error(f"Database error getting active job count: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def get_bot_status_from_db(self, bot_id_val="freelance-bot-main"):
        """Retrieves the BotStatus object for a given bot_id."""
        # This method needs to access the Django ORM model BotStatus
        # Since QueueManager is a standalone SQLite manager, it cannot directly
        # access Django models. This method is a placeholder.
        # In a real integrated system, this would query the Django DB.
        # For now, it will return a dummy object or None.
        bot_logger.warning("QueueManager cannot directly access Django's BotStatus model. Returning None.")
        return None # Placeholder: In a real Django app, you'd query BotStatus.objects.get(bot_id=bot_id_val)

# Example usage (for testing this module directly)
if __name__ == '__main__':
    qm = QueueManager()
    # qm._create_table() # Ensure table exists
    # test_job = {'job_id': 'test12345', 'title': 'Test Job', 'url': 'http://example.com/job/123', 'client_name': 'Test Client', 'budget': '$100'}
    # qm.add_job(test_job)
    # qm.update_job_status('test12345', 'proposed', proposal_text="This is my proposal.")
    # print(qm.get_jobs_by_status('proposed'))
    # print(f"Active jobs: {qm.get_active_job_count()}")
