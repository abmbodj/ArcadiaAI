"""
Data collection module for ArchieAI analytics.
Collects interaction data and saves to JSON for later analysis.
"""
import os
import json
from datetime import datetime
from typing import Optional
"For the data science class I will probably remove this when the semester ends but for now it will help me collect data on how people are using ArchieAI "
"and i will manipulate the data to find trends for my project"

class DataCollector:
    """Collects and logs interaction data to JSON file."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.json_file = os.path.join(data_dir, "analytics.json")
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize JSON file with empty array if it doesn't exist
        if not os.path.exists(self.json_file):
            self._create_json_file()
    
    def _create_json_file(self):
        """Create JSON file with empty array."""
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    
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
        Log a user interaction to the JSON file.
        
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
        
        interaction = {
            "timestamp": timestamp,
            "session_id": session_id,
            "user_email": user_email if user_email else "guest",
            "ip_address": ip_address,
            "device_info": device_info,
            "question": question,
            "question_length": question_length,
            "answer": answer,
            "answer_length": answer_length,
            "generation_time_seconds": round(generation_time_seconds, 2)
        }
        
        # Read existing data
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
        
        # Append new interaction
        data.append(interaction)
        
        # Write back to file
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

