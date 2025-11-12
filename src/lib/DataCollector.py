"""
Data collection module for ArchieAI analytics.
Collects interaction data and saves to CSV for later analysis.
"""
import os
import csv
from datetime import datetime
from typing import Optional


class DataCollector:
    """Collects and logs interaction data to CSV file."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.csv_file = os.path.join(data_dir, "analytics.csv")
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize CSV file with headers if it doesn't exist
        if not os.path.exists(self.csv_file):
            self._create_csv_file()
    
    def _create_csv_file(self):
        """Create CSV file with headers."""
        headers = [
            "timestamp",
            "session_id",
            "user_email",
            "ip_address",
            "device_info",
            "question",
            "question_length",
            "answer",
            "answer_length",
            "generation_time_seconds"
        ]
        
        with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(headers)
    
    def log_interaction(
        self,
        session_id: str,
        user_email: Optional[str],
        ip_address: str,
        device_info: str,
        question: str,
        answer: str,
        generation_time_seconds: float
    ):
        """
        Log a user interaction to the CSV file.
        
        Args:
            session_id: Unique session identifier
            user_email: User's email (None for guests)
            ip_address: User's IP address
            device_info: User agent string
            question: User's question
            answer: AI's answer
            generation_time_seconds: Time taken to generate the answer
        """
        timestamp = datetime.now().isoformat()
        question_length = len(question)
        answer_length = len(answer)
        
        row = [
            timestamp,
            session_id,
            user_email if user_email else "guest",
            ip_address,
            device_info,
            question,
            question_length,
            answer,
            answer_length,
            f"{generation_time_seconds:.2f}"
        ]
        
        # Append to CSV file with proper quoting for text fields
        with open(self.csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerow(row)
