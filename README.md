# 📊 Data AI Dashboard (Streamlit + Python)

Upload → Auto-clean → Manual/AI Analysis → Charts → Excel Export → i18n (EN/VI).  
Generate quick insights from charts via **Gemini**. Built with **Streamlit**, **pandas**, **Matplotlib**.

<p align="center">
  <!-- Optional: replace with your image -->
  <img src="docs/screenshot_dashboard.png" alt="Dashboard screenshot" width="800"/>
</p>

---

## ✨ Features
- Upload: **CSV / XLSX / JSON**
- **Auto Clean**: strip/lower text, fill numeric NaN=0, drop duplicates
- **Manual Analysis**: quick groupby (sum/mean/count/min/max) & charts
- **AI Analysis (Gemini)**: short insights (EN/VI) + Q&A
- **Reports**: preview charts/insights, delete, **Export Excel**
- **i18n**: English / Vietnamese via JSON locale (safe EN fallback)

---

## 🚀 Quick Start

### 1) Clone & venv
```bash
git clone https://github.com/<yourname>/Capstone_AI_Data_Dashboard.git
cd Capstone_AI_Data_Dashboard
python -m venv .venv
# Windows
. .venv/Scripts/activate
# macOS/Linux
# source .venv/bin/activate

