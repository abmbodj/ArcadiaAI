#Manipulate data for analysis and graphs and trends and yada yada


import os
import json
import pandas as pd
import matplotlib.pyplot as plt

def load_data(json_file: str) -> pd.DataFrame:
    """Load interaction data from JSON file into a DataFrame."""
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

print("DataManipulator.py loaded successfully.")
data = load_data("data/analytics.json")
#This does nothing for now but i want to create this file for data manipulation later

