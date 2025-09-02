#ai_insight.py
import os
from PIL import Image
import google.generativeai as genai
from .charts import plot_chart
import pandas as pd
from dotenv import load_dotenv
from functools import lru_cache 

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ===== Language helpers =====
@lru_cache(maxsize=2)
def _build_model(lang: str):
    """Khởi tạo model với system_instruction khóa ngôn ngữ."""
    sys = "Always respond in English only." if lang == "en" else "Luôn trả lời hoàn toàn bằng tiếng Việt."
    return genai.GenerativeModel("gemini-2.0-flash", system_instruction=sys)

def _lang_clause(lang: str) -> str:
    """Nhắc lại trong prompt để model nhất quán ngôn ngữ."""
    return ("Respond in English only. Do not use any Vietnamese."
            if lang == "en"
            else "Trả lời hoàn toàn bằng tiếng Việt. Không dùng tiếng Anh.")

# ===== Functions =====
def generate_report_from_chart(folder_path: str, chart_name: str, lang: str = "en"):
    model = _build_model(lang)
    if isinstance(chart_name, str) and chart_name.lower().endswith(('.png', '.jpg', '.jpeg')):
        file_path = os.path.join(folder_path, chart_name)
        if not os.path.exists(file_path):
            return "Chart file not found." if lang == "en" else "Không tìm thấy file biểu đồ."
        try:
            img = Image.open(file_path)
        except Exception as e:
            return f"Cannot open chart: {e}" if lang == "en" else f"Không mở được biểu đồ: {e}"

        base = ("Generate a concise report with insights (max 100 words) from this chart:"
                if lang == "en"
                else "Tạo báo cáo ngắn (tối đa 100 từ) với các insight từ biểu đồ này:")
        prompt = [f"{base} {_lang_clause(lang)}", img]
        try:
            response = model.generate_content(prompt)
            text = (getattr(response, "text", "") or "").replace("*", "").strip()
            return text if text else ("No insight generated." if lang == "en" else "Không tạo được insight.")
        except Exception as e:
            return f"AI error: {e}" if lang == "en" else f"Lỗi AI: {e}"
    return "No insight generated." if lang == "en" else "Không tạo được insight."

def ai_auto_analysis(data: pd.DataFrame, lang: str = "en"):
    reports = []
    folder_path = "./charts"
    os.makedirs(folder_path, exist_ok=True)
    model = _build_model(lang)

    # dtype linh hoạt hơn
    numeric_cols = data.select_dtypes(include=["number"]).columns.tolist()
    category_cols = data.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    if not category_cols:
        data = data.reset_index()
        category_cols = ["index"]

    for category in category_cols[:3]:
        for numeric in numeric_cols[:3]:
            try:
                pivot = data.groupby(category, dropna=False)[numeric].sum().reset_index()
            except Exception:
                continue  # bỏ qua cặp cột không group được

            chart_path, chart_name = plot_chart(folder_path, "Bar Chart", pivot, category, numeric)
            insight = ""
            if chart_path and isinstance(chart_name, str) and chart_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(folder_path, chart_name)
                try:
                    img = Image.open(img_path)
                    base = (f"Analyze this bar chart of '{numeric}' by '{category}' and give 1 short, actionable insight (<=30 words)."
                            if lang == "en"
                            else f"Phân tích biểu đồ cột '{numeric}' theo '{category}' và đưa ra 1 nhận định ngắn gọn, hữu ích (<=30 chữ).")
                    response = model.generate_content([f"{base} {_lang_clause(lang)}", img])
                    insight = (getattr(response, "text", "") or "").replace("*", "").strip()
                except Exception:
                    insight = ""

            reports.append({
                "pivot_table": pivot,
                "chart_path": chart_path,
                "sheet_name": f"{category}_{numeric}",
                "insight": insight
            })
    return reports

def ai_answer_question(data: pd.DataFrame, question: str, lang: str = "en"):
    model = _build_model(lang)
    folder_path = "./charts"
    os.makedirs(folder_path, exist_ok=True)

    numeric_cols = data.select_dtypes(include=["number"]).columns.tolist()
    category_cols = data.select_dtypes(include=["object", "string", "category"]).columns.tolist()

    chart_path, img = None, None
    if category_cols and numeric_cols:
        try:
            pivot = data.groupby(category_cols[0], dropna=False)[numeric_cols[0]].sum().reset_index()
            chart_path, chart_name = plot_chart(folder_path, "Bar Chart", pivot, category_cols[0], numeric_cols[0])
            if chart_path and isinstance(chart_name, str) and chart_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_file = os.path.join(folder_path, chart_name)
                if os.path.exists(img_file):
                    img = Image.open(img_file)
        except Exception:
            pass

    base = (f"User asks: {question}. Dataset columns: {list(data.columns)}. Provide a concise, specific insight."
            if lang == "en"
            else f"Người dùng hỏi: {question}. Các cột dữ liệu: {list(data.columns)}. Trả lời ngắn gọn, cụ thể.")
    prompt = f"{base} {_lang_clause(lang)}"

    try:
        response = model.generate_content([prompt, img] if img is not None else [prompt])
        answer = (getattr(response, "text", "") or "").replace("*", "").strip()
        if not answer:
            answer = "No insight generated." if lang == "en" else "Không tạo được insight."
    except Exception as e:
        answer = f"AI error: {e}" if lang == "en" else f"Lỗi AI: {e}"

    return chart_path, answer
