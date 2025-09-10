# helpers/charts.py
import os
import matplotlib
matplotlib.use("Agg", force=True)  # headless backend

import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import pandas as pd
from datetime import datetime

def _unique_suffix() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")

def plot_chart(folder_path, chart_type, data, x_col, y_col):
    """
    Simple plotting utility that saves the figure and returns (chart_path, chart_name).
    """
    data = data.copy()
    data[x_col] = data[x_col].astype(str)
    data[y_col] = pd.to_numeric(data[y_col], errors='coerce').fillna(0)

    os.makedirs(folder_path, exist_ok=True)
    plt.close('all')
    fig, ax = plt.subplots(figsize=(8, 5))

    safe_type = chart_type.replace(' ', '_')
    chart_name = f"{safe_type}_{x_col}_by_{y_col}_{_unique_suffix()}.png"
    chart_path = os.path.join(folder_path, chart_name)

    try:
        if chart_type == "Line Chart":
            sns.lineplot(data=data, x=x_col, y=y_col, marker='o', ax=ax)
        elif chart_type == "Bar Chart":
            sns.barplot(data=data, x=x_col, y=y_col, ax=ax)
        elif chart_type == "Scatter Plot":
            sns.scatterplot(data=data, x=x_col, y=y_col, ax=ax)
        elif chart_type == "Pie Chart":
            pie_data = data.groupby(x_col)[y_col].sum()
            pie_data.plot.pie(autopct='%1.1f%%', startangle=90, ax=ax)
            ax.set_ylabel('')
        else:
            st.error(f"❌ Chart type '{chart_type}' is not supported!")
            return None, None

        fig.tight_layout()
        fig.savefig(chart_path, bbox_inches='tight')
        plt.close(fig)
        return chart_path, chart_name
    except Exception as e:
        st.error(f"❌ Chart rendering error: {e}")
        return None, None

def remove_chart(file_path):
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
    except Exception:
        pass
