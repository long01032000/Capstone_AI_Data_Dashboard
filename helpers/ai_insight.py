# helpers/ai_insight.py
import os
import re
import json
from functools import lru_cache
from typing import Optional, Dict, Any

import pandas as pd
from PIL import Image
import google.generativeai as genai
from .paths import get_chart_dir

from dotenv import load_dotenv
from .charts import plot_chart

# ===== Setup =====
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ===== Model helpers =====
@lru_cache(maxsize=2)
def _build_model(lang: str):
    """
    Build a Gemini model with a simple language lock (EN/VI).
    """
    sys = "Always respond in English only." if lang == "en" else "Luôn trả lời hoàn toàn bằng tiếng Việt."
    return genai.GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=sys,
        generation_config={"temperature": 0.4}
    )

def _lang_clause(lang: str) -> str:
    return "Respond in English only." if lang == "en" else "Trả lời hoàn toàn bằng tiếng Việt."

# ===== Small dataset profile for chat fallback =====
def _build_profile(df: pd.DataFrame, max_uniques: int = 12, sample_rows: int = 30) -> Dict[str, Any]:
    """
    Very light profile: shapes, per-column dtype, a few stats for numeric,
    sample values for categorical, and a handful of rows.
    """
    prof: Dict[str, Any] = {"rows": int(len(df)), "cols_count": int(df.shape[1]), "columns": []}
    for c in df.columns:
        s = df[c]
        item = {"name": str(c), "dtype": str(s.dtype)}
        if pd.api.types.is_numeric_dtype(s):
            ss = pd.to_numeric(s, errors="coerce")
            item["summary"] = {
                "min": float(ss.min(skipna=True)) if len(ss) else None,
                "max": float(ss.max(skipna=True)) if len(ss) else None,
                "mean": float(ss.mean(skipna=True)) if len(ss) else None,
            }
        else:
            item["sample_values"] = list(s.dropna().astype(str).head(max_uniques).unique())
        prof["columns"].append(item)

    try:
        prof["sample_rows"] = df.head(sample_rows).to_dict(orient="records")
    except Exception:
        prof["sample_rows"] = []
    return prof

# ===== Chart → short insight =====
def _resolve_chart_path(folder_path: str, chart_path_or_name: str) -> Optional[str]:
    candidates = []
    if isinstance(chart_path_or_name, str):
        if os.path.exists(chart_path_or_name):
            candidates.append(chart_path_or_name)
        candidates.append(os.path.join(folder_path, chart_path_or_name))
    for p in candidates:
        if isinstance(p, str) and os.path.exists(p):
            return p
    return None

def generate_report_from_chart(folder_path: str, chart_path_or_name: str, lang: str = "en"):
    """
    Read the chart image and ask Gemini for a ≤100-word insight.
    """
    file_path = _resolve_chart_path(folder_path, chart_path_or_name)
    if not file_path:
        return "Chart file not found." if lang == "en" else "Không tìm thấy file biểu đồ."
    try:
        img = Image.open(file_path)
    except Exception as e:
        return f"Cannot open chart: {e}" if lang == "en" else f"Không mở được biểu đồ: {e}"

    base = "Generate a concise report (max 100 words) from this chart:" if lang == "en" \
           else "Tạo báo cáo ngắn (tối đa 100 từ) từ biểu đồ này:"
    try:
        model = _build_model(lang)
        resp = model.generate_content([f"{base} {_lang_clause(lang)}", img])
        text = (getattr(resp, "text", "") or "").replace("*", "").strip()
        return text if text else ("No insight generated." if lang == "en" else "Không tạo được insight.")
    except Exception as e:
        return f"AI error: {e}" if lang == "en" else f"Lỗi AI: {e}"

# ===== Simple Auto Analysis (used by 'Run AI Auto Analysis') =====
def ai_auto_analysis(data: pd.DataFrame, lang: str = "en"):
    """
    Create up to 3×3 (categorical × numeric) bar charts and ask Gemini
    for a one-line actionable insight derived from each chart image.
    """
    reports = []
    folder_path = "./charts"
    os.makedirs(folder_path, exist_ok=True)
    model = _build_model(lang)

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
                continue

            chart_path, chart_name = plot_chart(folder_path, "Bar Chart", pivot, category, numeric)
            insight = ""
            if chart_path and isinstance(chart_name, str) and chart_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                try:
                    img = Image.open(os.path.join(folder_path, chart_name))
                    base = (f"Analyze this bar chart of '{numeric}' by '{category}' and give ONE short, actionable insight (<=30 words)."
                            if lang == "en"
                            else f"Phân tích biểu đồ '{numeric}' theo '{category}' và đưa ra MỘT nhận định ngắn gọn (<=30 chữ).")
                    resp = model.generate_content([f"{base} {_lang_clause(lang)}", img])
                    insight = (getattr(resp, "text", "") or "").replace("*", "").strip()
                except Exception:
                    insight = ""

            reports.append({
                "pivot_table": pivot,
                "chart_path": chart_path,
                "sheet_name": f"{category}_{numeric}",
                "insight": insight,
                "source": "AI"
            })
    return reports

# ===== Lightweight “smart” chat (no chart, no report add) =====
def _pick_col_by_hint(all_cols, hint: str):
    """Exact -> case-insensitive -> substring match."""
    if not hint:
        return None
    h = hint.strip().lower()
    for c in all_cols:
        if c.lower() == h:
            return c
    for c in all_cols:
        if h in c.lower():
            return c
    return None

def _detect_parts(question: str, df: pd.DataFrame):
    """
    Tiny parser for beginner-friendly execution:
      - 'by <col>' or 'group by <col>'
      - 'top K' / 'bottom K'
      - sum | avg/mean | count | min | max
      - metric guess from numeric columns or common names
    """
    ql = question.strip().lower()

    by_match = re.search(r"(?:group\s+by|by)\s+([a-z0-9 _\-]+)", ql)
    group_by_hint = by_match.group(1).strip() if by_match else None

    topk = None
    if m := re.search(r"\btop\s*(\d+)?\b", ql):
        topk = int(m.group(1)) if m.group(1) else 5
    bottom = bool(re.search(r"\bbottom\b", ql))

    agg = "sum"
    if any(k in ql for k in ["average", "avg", "mean"]): agg = "mean"
    elif "count" in ql: agg = "count"
    elif "min" in ql: agg = "min"
    elif "max" in ql: agg = "max"
    elif any(k in ql for k in ["sum", "total"]): agg = "sum"

    # metric
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    metric_hint = None
    for kw in ["amount", "revenue", "sales", "qty", "quantity", "price", "unitprice", "total"]:
        if kw in ql:
            metric_hint = kw; break
    metric = None
    if metric_hint:
        for c in num_cols:
            if metric_hint in c.lower():
                metric = c; break
    if not metric and num_cols:
        metric = num_cols[0]

    group_by = _pick_col_by_hint(df.columns, group_by_hint) if group_by_hint else None

    return {"group_by": group_by, "metric": metric, "agg": agg, "topk": topk, "bottom": bottom}

def ai_answer_question(data: pd.DataFrame, question: str, lang: str = "en"):
    """
    Beginner-friendly chat:
      1) Try a simple aggregate if the question looks like “<agg> <metric> by <group> (top K)”.
      2) If possible, compute with pandas and ask Gemini to phrase one short insight. Include a small table.
      3) Otherwise, fallback to normal chat using a lightweight dataset profile.
    Returns: (None, reply_text)
    """
    if not question or not question.strip():
        msg = ("Ask about your data, e.g., “Top 5 Qty by City”, “Average UnitPrice by Product”."
               if lang == "en" else
               "Hãy hỏi về dữ liệu, ví dụ: “Top 5 Qty theo City”, “Giá trung bình theo Product”.")
        return None, msg

    parts = _detect_parts(question, data)
    group_by, metric, agg, topk, bottom = parts["group_by"], parts["metric"], parts["agg"], parts["topk"], parts["bottom"]

    # Try to execute a simple aggregation
    try:
        if group_by and (metric or agg == "count"):
            df = data.copy()
            if agg == "count":
                pivot = df.groupby(group_by, dropna=False).size().reset_index(name="count")
                value_col = "count"
            else:
                if metric not in df.select_dtypes(include=["number"]).columns:
                    raise ValueError("Metric is not numeric or not found.")
                pivot = getattr(df.groupby(group_by, dropna=False)[metric], agg)().reset_index()
                value_col = metric

            pivot = pivot.sort_values(by=value_col, ascending=bottom)
            pivot = pivot.head(topk if topk else 10)

            md_table = pivot.head(10).to_markdown(index=False)

            model = _build_model(lang)
            base = "Write ONE concise insight (<=60 words) from the table. Do not invent numbers." \
                   if lang == "en" else \
                   "Viết MỘT insight ngắn (<=60 chữ) từ bảng. Không bịa số."
            resp = model.generate_content([
                {"text": base},
                {"text": f"Question: {question}"},
                {"text": f"Result (markdown):\n{md_table}"},
                {"text": _lang_clause(lang)}
            ])
            insight = (getattr(resp, "text", "") or "").replace("*", "").strip()
            if not insight:
                row0 = pivot.iloc[0].to_dict()
                insight = (f"Top {group_by} is {row0[group_by]} with {value_col} = {row0[value_col]}."
                           if lang == "en" else
                           f"Nhóm dẫn đầu '{group_by}' là {row0[group_by]} với {value_col} = {row0[value_col]}.")

            return None, insight + "\n\n" + md_table
    except Exception:
        pass  # fall through

    # Fallback: normal chat with dataset profile
    profile = _build_profile(data)
    model = _build_model(lang)
    sys = ("You are a helpful data assistant. Use ONLY the dataset profile & sample rows. "
           "If exact results need aggregation, explain what would be computed and suggest a next step. "
           "Answer concisely (<=120 words)."
           if lang == "en" else
           "Bạn là trợ lý dữ liệu. Chỉ dùng profile và vài dòng mẫu. "
           "Nếu cần tổng hợp để ra kết quả, hãy nói rõ cần tính gì và gợi ý bước tiếp. "
           "Trả lời ngắn gọn (<=120 chữ).")
    try:
        resp = model.generate_content([
            {"text": sys},
            {"text": f"Dataset profile JSON:\n{json.dumps(profile)[:4000]}"},
            {"text": f"User question:\n{question}\n{_lang_clause(lang)}"}
        ])
        reply = (getattr(resp, "text", "") or "").replace("*", "").strip()
        if not reply:
            reply = "I couldn’t generate a response." if lang == "en" else "Chưa tạo được câu trả lời."
        return None, reply
    except Exception as e:
        return None, (f"AI error: {e}" if lang == "en" else f"Lỗi AI: {e}")
