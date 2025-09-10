# helpers/data_processing.py
import pandas as pd

def auto_clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
      - strip strings
      - fill numeric NaN with 0
      - drop duplicates
    """
    data = df.copy()
    for col in data.select_dtypes(include=["object", "string"]):
        data[col] = data[col].astype(str).strip()
    for col in data.select_dtypes(include=["number"]).columns:
        data[col] = data[col].fillna(0)
    data.drop_duplicates(inplace=True)
    return data
