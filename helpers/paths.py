# helpers/paths.py
import os, streamlit as st

def get_chart_dir() -> str:
    """
    Return the chart directory (default ./charts). Cloud-friendly default: /tmp/charts if set in secrets.
    """
    base = st.secrets.get("CHART_DIR", "./charts")
    path = os.path.abspath(base)
    os.makedirs(path, exist_ok=True)
    return path
