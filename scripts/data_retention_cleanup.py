import os
import time
import glob
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger("data_retention", "logs/data_retention.log")

# Configuration
RETENTION_DAYS = 180
DATA_DIRECTORIES = [
    "outputs",
    "logs",
    "data/processed"
]

def run_cleanup():
    """
    Scans configured data directories and purges files older than RETENTION_DAYS.
    This aligns with GDPR and company data retention policies.
    """
    logger.info(f"Starting data retention cleanup task. Retention period: {RETENTION_DAYS} days.")
    
    cutoff_time = time.time() - (RETENTION_DAYS * 86400)
    cutoff_date = datetime.fromtimestamp(cutoff_time)
    
    logger.info(f"Purging files created/modified before: {cutoff_date.isoformat()}")
    
    files_deleted = 0
    bytes_freed = 0

    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    for directory in DATA_DIRECTORIES:
        dir_path = os.path.join(base_path, directory)
        if not os.path.exists(dir_path):
            continue
            
        # Using glob to search recursively
        search_pattern = os.path.join(dir_path, "**", "*")
        for file_path in glob.glob(search_pattern, recursive=True):
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                # Check modification time
                if file_stat.st_mtime < cutoff_time:
                    try:
                        file_size = file_stat.st_size
                        os.remove(file_path)
                        files_deleted += 1
                        bytes_freed += file_size
                        logger.debug(f"Deleted outdated file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")

    mb_freed = bytes_freed / (1024 * 1024)
    logger.info(f"Cleanup complete. Deleted {files_deleted} files. Freed {mb_freed:.2f} MB.")
    print(f"Cleanup complete. Deleted {files_deleted} files. Freed {mb_freed:.2f} MB.")

if __name__ == "__main__":
    run_cleanup()
