# 📊 Data AI Dashboard (Streamlit + Python)

Upload → Auto-clean → Manual/AI Analysis → Charts → Excel Export → i18n (EN/VI).  
Generate quick insights from charts via **Gemini**. Built with **Streamlit**, **pandas**, **Matplotlib**.

<p align="center">
  <!-- Optional: replace with your image -->
  <img src="./Untitled.png" alt="Dashboard screenshot" width="800"/>
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
```

### 2) Install
```bash
pip install -r requirements.txt
```

> **requirements.txt** (gợi ý)
```txt
streamlit>=1.24
pandas>=2.0
matplotlib>=3.7
Pillow>=10.0
python-dotenv>=1.0
google-generativeai>=0.7
openpyxl>=3.1
```

### 3) Set API key
Tạo file `.env` (ở gốc):
```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
```

### 4) Run
```bash
streamlit run app.py
```

---

## 🗂️ Structure
```
Capstone_AI_Data_Dashboard/
├─ app.py
├─ helpers/
│  ├─ ai_insight.py         # Gemini prompts, AI auto-analysis, Q&A
│  ├─ charts.py             # Plot & save charts (PNG)
│  ├─ data_processing.py    # auto_clean_data + warning helper
│  ├─ excel_report.py       # Export Excel (openpyxl)
│  └─ i18n.py               # load_language(), trans(), hot-reload
├─ locales/
│  ├─ en.json
│  └─ vi.json
├─ charts/                  # generated charts
├─ reports/                 # exported Excel
├─ docs/                    # screenshots (optional)
└─ README.md
```

---

## 🌐 i18n (EN/VI)
- `helpers/i18n.py` hợp nhất `en.json` (base) + `vi.json` (overlay) → **dict read-only**.
- Dùng `trans(locale, "key", "fallback")` trong UI để an toàn khi thiếu key.

<details>
<summary><b>locales/en.json</b></summary>

```json
{
  "page_title": "📊 Data AI Dashboard",
  "sidebar_settings": "Settings",
  "sidebar_upload": "Upload",
  "language_label": "Language",
  "upload_file": "Upload file",
  "tab_upload": "Upload",
  "tab_manual": "Manual Analysis",
  "tab_ai": "AI Analysis",
  "tab_reports": "Reports",
  "auto_clean": "Auto clean data",
  "loading": "Loading...",
  "data_cleaned": "Data cleaned successfully!",
  "no_data_msg": "No data yet. Please upload a file in the Upload tab.",
  "warn_not_clean": "⚠️ Your data hasn't been auto-cleaned yet. Results may be less reliable. Go to the Upload tab and click “Auto clean data”.",
  "data_preview": "Data preview",
  "choose_category": "Choose a category column",
  "choose_numeric": "Choose a numeric column",
  "aggregation": "Aggregation",
  "agg_sum": "Sum",
  "agg_mean": "Mean",
  "agg_count": "Count",
  "agg_min": "Min",
  "agg_max": "Max",
  "chart_type": "Chart Type",
  "chart_line": "Line Chart",
  "chart_bar": "Bar Chart",
  "chart_scatter": "Scatter Plot",
  "chart_pie": "Pie Chart",
  "plot_graph": "Plot chart",
  "analysis_ready": "Analysis ready. Open the Report page for full details.",
  "ask_ai": "Ask AI about your data",
  "send_question": "Send Question",
  "ai_answer": "AI Answer",
  "manual_reports_section": "🛠 Manual Reports",
  "ai_reports_section": "🤖 AI Reports",
  "no_manual": "No manual charts.",
  "no_ai": "No AI charts.",
  "insight": "Insight",
  "loading_manual_chart_fmt": "⏳ Loading Manual Chart {i}...",
  "manual_chart_caption_fmt": "Manual Chart {i}",
  "remove_manual_chart_fmt": "🗑 Remove Manual Chart {i}",
  "loading_ai_chart_fmt": "⏳ Loading AI Chart {i}...",
  "ai_chart_caption_fmt": "AI Chart {i}",
  "remove_ai_chart_fmt": "🗑 Remove AI Chart {i}",
  "no_reports_yet": "No reports yet. Create charts in the Manual/AI tabs.",
  "export_all": "📥 Export All Reports",
  "creating_combined": "⏳ Creating combined Excel report...",
  "export_success": "Export success. Please download your file below.",
  "download_all": "Download All Reports",
  "reset_workspace": "Reset workspace (clear data & reports)",
  "workspace_cleared": "Workspace cleared.",
  "file_loaded": "File loaded.",
  "no_cols_msg": "Need at least one categorical and one numeric column."
}
```
</details>

<details>
<summary><b>locales/vi.json</b></summary>

```json
{
  "page_title": "📊 Bảng điều khiển AI dữ liệu",
  "sidebar_settings": "Cài đặt",
  "sidebar_upload": "Tải dữ liệu",
  "language_label": "Ngôn ngữ",
  "upload_file": "Tải lên tệp",
  "tab_upload": "Tải lên",
  "tab_manual": "Phân tích thủ công",
  "tab_ai": "Phân tích AI",
  "tab_reports": "Báo cáo",
  "auto_clean": "Làm sạch tự động",
  "loading": "Đang xử lý...",
  "data_cleaned": "Dữ liệu đã được làm sạch!",
  "no_data_msg": "Chưa có dữ liệu. Hãy tải tệp ở tab Tải lên.",
  "warn_not_clean": "⚠️ Dữ liệu chưa được làm sạch. Kết quả có thể kém chính xác. Vào tab Tải lên và bấm “Làm sạch tự động”.",
  "data_preview": "Xem nhanh dữ liệu",
  "choose_category": "Chọn cột phân loại",
  "choose_numeric": "Chọn cột số",
  "aggregation": "Hàm tổng hợp",
  "agg_sum": "Tổng",
  "agg_mean": "Trung bình",
  "agg_count": "Đếm",
  "agg_min": "Nhỏ nhất",
  "agg_max": "Lớn nhất",
  "chart_type": "Loại biểu đồ",
  "chart_line": "Đường",
  "chart_bar": "Cột",
  "chart_scatter": "Phân tán",
  "chart_pie": "Tròn",
  "plot_graph": "Vẽ biểu đồ",
  "analysis_ready": "Đã xong. Xem chi tiết ở tab Báo cáo.",
  "ask_ai": "Hỏi AI về dữ liệu",
  "send_question": "Gửi câu hỏi",
  "ai_answer": "Trả lời AI",
  "manual_reports_section": "🛠 Biểu đồ thủ công",
  "ai_reports_section": "🤖 Biểu đồ AI",
  "no_manual": "Chưa có biểu đồ thủ công.",
  "no_ai": "Chưa có biểu đồ AI.",
  "insight": "Nhận định",
  "loading_manual_chart_fmt": "⏳ Đang tải biểu đồ thủ công {i}...",
  "manual_chart_caption_fmt": "Biểu đồ thủ công {i}",
  "remove_manual_chart_fmt": "🗑 Xóa biểu đồ thủ công {i}",
  "loading_ai_chart_fmt": "⏳ Đang tải biểu đồ AI {i}...",
  "ai_chart_caption_fmt": "Biểu đồ AI {i}",
  "remove_ai_chart_fmt": "🗑 Xóa biểu đồ AI {i}",
  "no_reports_yet": "Chưa có báo cáo. Hãy tạo ở tab Thủ công/AI.",
  "export_all": "📥 Xuất tất cả báo cáo",
  "creating_combined": "⏳ Đang tạo file Excel tổng hợp...",
  "export_success": "Xuất thành công. Tải file bên dưới.",
  "download_all": "Tải toàn bộ báo cáo",
  "reset_workspace": "Làm mới (xóa dữ liệu & báo cáo)",
  "workspace_cleared": "Đã làm mới.",
  "file_loaded": "Đã tải tệp.",
  "no_cols_msg": "Cần ít nhất 1 cột phân loại và 1 cột số."
}
```
</details>

---

## 🧠 Notes (AI)
- `.env` cần `GEMINI_API_KEY`.  
- `helpers/ai_insight.py` dùng **system_instruction** khoá ngôn ngữ (EN/VI) + lặp lại clause trong prompt để tránh trộn ngôn ngữ.

---

## 📦 Excel Export
- Gom `manual_reports + ai_reports`, prefix sheet: `MAN_...` và `AI_...`.
- Lưu tại `reports/all_reports_YYYYMMDD_HHMMSS.xlsx`.

---

## 🧭 Troubleshooting
- **NameError: locale** → gọi `locale = load_language(lang)` trước `trans(...)`.
- **Streamlit version cũ** → lỗi `use_container_width/use_column_width`: bỏ tham số hoặc nâng version.
- **AI sai ngôn ngữ** → kiểm tra `lang` truyền vào các hàm trong `ai_insight.py`.
- **Reset state khi browse** → app dùng `_file_id=(name,size)` để chỉ reset khi file thực sự đổi.

---

## ☁️ Deploy (Streamlit Cloud)
1. Push repo lên GitHub (public).
2. Vào https://share.streamlit.io → New app → chọn repo/branch/file `app.py`.
3. Thêm `GEMINI_API_KEY` vào **Secrets** của app.
4. Deploy.

---

## 📝 License
MIT © 2025
