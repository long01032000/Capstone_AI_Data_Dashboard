# app.py
import os
import io
import pandas as pd
import streamlit as st
from datetime import datetime

from helpers.data_processing import auto_clean_data
from helpers.charts import plot_chart, remove_chart
from helpers.excel_report import generate_excel_report
from helpers.i18n import load_language, trans
from helpers.ai_insight import ai_auto_analysis, ai_answer_question, generate_report_from_chart

# ============== UI CONFIG ==============
st.set_page_config(page_title="📊 Data AI Dashboard", layout="wide")

# ============== SESSION DEFAULTS ==============
if "lang" not in st.session_state: st.session_state.lang = "en"
if "data" not in st.session_state: st.session_state.data = None
if "cleaned_data" not in st.session_state: st.session_state.cleaned_data = None
if "is_cleaned" not in st.session_state: st.session_state.is_cleaned = False
if "manual_reports" not in st.session_state: st.session_state.manual_reports = []
if "ai_reports" not in st.session_state: st.session_state.ai_reports = []
if "_file_id" not in st.session_state: st.session_state._file_id = None

# ============== CACHED HELPERS ==============
@st.cache_data(show_spinner=False)
def _auto_clean_cached(df: pd.DataFrame) -> pd.DataFrame:
    return auto_clean_data(df)

@st.cache_data(show_spinner=False)
def _aggregate_cached(df: pd.DataFrame, category_col: str, numeric_col: str, agg_func: str) -> pd.DataFrame:
    return getattr(df.groupby(category_col)[numeric_col], agg_func)().reset_index()

@st.cache_data(show_spinner=False)
def _read_df_from_bytes(data_bytes: bytes, ext: str) -> pd.DataFrame:
    if ext == "csv":  return pd.read_csv(io.BytesIO(data_bytes))
    if ext in ("xlsx", "xls"): return pd.read_excel(io.BytesIO(data_bytes))
    if ext == "json": return pd.read_json(io.BytesIO(data_bytes))
    raise ValueError("Unsupported file type")

# ============== I18N ==============
lang = st.session_state.lang
locale = load_language(lang)

# ============== SIDEBAR ==============
with st.sidebar:
    settings_tab, upload_tab = st.tabs([
        trans(locale, "sidebar_settings", "Settings"),
        trans(locale, "sidebar_upload",  "Upload"),
    ])
    # Language
    with settings_tab:
        labels = ["English", "Tiếng Việt"]; values = {"English": "en", "Tiếng Việt": "vi"}
        def _set_lang(): st.session_state.lang = values[st.session_state.lang_choice]
        default_label = "Tiếng Việt" if st.session_state.lang == "vi" else "English"
        st.selectbox(trans(locale, "language_label", "Language"), labels,
                     index=labels.index(default_label), key="lang_choice", on_change=_set_lang)

    # Upload
    with upload_tab:
        uploaded_file = st.file_uploader(
            trans(locale, "upload_file", "Upload file"),
            type=["csv", "xlsx", "json"],
            key="data_uploader"
        )

# Reload locale if language changed in sidebar
lang = st.session_state.lang
locale = load_language(lang)

# ============== TITLE ==============
st.title(trans(locale, "page_title", "📊 Data AI Dashboard"))

# ============== HELPERS ==============
def warn_if_not_clean():
    if st.session_state.data is not None and not st.session_state.is_cleaned:
        st.warning(trans(locale, "warn_not_clean",
            "⚠️ Your data hasn't been auto-cleaned yet. Results may be less reliable. "
            "Go to the Upload tab and click “Auto clean data”."
        ))

def no_data_msg():
    st.info(trans(locale, "no_data_msg", "No data yet. Please upload a file in the Upload tab."))

# ============== MAIN TABS ==============
tabs = st.tabs([
    trans(locale, "tab_upload", "Upload"),
    trans(locale, "tab_manual", "Manual Analysis"),
    trans(locale, "tab_ai", "AI Analysis"),
    trans(locale, "tab_reports", "Reports"),
])

chart_folder = "./charts"; os.makedirs(chart_folder, exist_ok=True)

# ===== TAB 1: Upload & Clean =====
with tabs[0]:
    st.subheader(trans(locale, "tab_upload", "Upload"))
    if uploaded_file is not None:
        try:
            data_bytes = uploaded_file.getvalue()
            ext = uploaded_file.name.split(".")[-1].lower()
            file_id = (uploaded_file.name, len(data_bytes))
        except Exception as e:
            st.error(f"Cannot read file: {e}"); st.stop()

        if st.session_state._file_id != file_id:
            try:
                df = _read_df_from_bytes(data_bytes, ext)
            except Exception as e:
                st.error(f"Cannot parse file: {e}"); st.stop()

            st.session_state._file_id = file_id
            st.session_state.data = df
            st.session_state.cleaned_data = df.copy()
            st.session_state.is_cleaned = False
            st.session_state.manual_reports = []
            st.session_state.ai_reports = []
            st.success(trans(locale, "file_loaded", "File loaded."))

    if st.session_state.data is None:
        no_data_msg()
    else:
        with st.expander(trans(locale, "data_preview", "Data preview"), expanded=False):
            st.dataframe(st.session_state.data.head(50))

        if st.button(trans(locale, "auto_clean", "Auto clean data")):
            with st.spinner(trans(locale, "loading", "Loading...")):
                st.session_state.cleaned_data = _auto_clean_cached(st.session_state.data)
                st.session_state.is_cleaned = True
                st.success(trans(locale, "data_cleaned", "Data cleaned successfully!"))
                st.dataframe(st.session_state.cleaned_data.head(50), height=400)

# ===== TAB 2: Manual Analysis =====
with tabs[1]:
    st.subheader(trans(locale, "tab_manual", "Manual Analysis"))

    data = st.session_state.cleaned_data
    if data is None: no_data_msg(); st.stop()
    warn_if_not_clean()

    cat_cols = data.select_dtypes(include=["object", "string", "category"]).columns.tolist()
    num_cols = data.select_dtypes(include=["number"]).columns.tolist()
    if not cat_cols or not num_cols:
        st.info(trans(locale, "no_cols_msg", "Need at least one categorical and one numeric column.")); st.stop()

    with st.form("manual_form", clear_on_submit=False):
        category_col = st.selectbox(trans(locale, "choose_category", "Choose a category column"), cat_cols, key="manual_cat")
        numeric_col  = st.selectbox(trans(locale, "choose_numeric", "Choose a numeric column"),   num_cols, key="manual_num")

        AGG_OPTIONS = [
            {"value": "sum", "label": trans(locale, "agg_sum", "Sum")},
            {"value": "mean","label": trans(locale, "agg_mean","Mean")},
            {"value": "count","label": trans(locale, "agg_count","Count")},
            {"value": "min", "label": trans(locale, "agg_min", "Min")},
            {"value": "max", "label": trans(locale, "agg_max", "Max")},
        ]
        agg_choice = st.selectbox(trans(locale, "aggregation", "Aggregation"), AGG_OPTIONS, format_func=lambda o: o["label"], key="manual_agg")
        agg_func   = agg_choice["value"]

        CHART_TYPES = [
            {"value":"Line Chart", "label":trans(locale,"chart_line","Line Chart")},
            {"value":"Bar Chart",  "label":trans(locale,"chart_bar","Bar Chart")},
            {"value":"Scatter Plot","label":trans(locale,"chart_scatter","Scatter Plot")},
            {"value":"Pie Chart",  "label":trans(locale,"chart_pie","Pie Chart")},
        ]
        chart_choice = st.selectbox(trans(locale, "chart_type", "Chart Type"), CHART_TYPES, format_func=lambda o:o["label"], key="manual_chart")

        submitted = st.form_submit_button(trans(locale, "plot_graph", "Plot chart"))

    if submitted:
        with st.spinner(trans(locale, "loading", "Loading...")):
            agg_data = _aggregate_cached(data, category_col, numeric_col, agg_func)
            st.dataframe(agg_data if len(agg_data) > 500 else agg_data.style.background_gradient(cmap="viridis"))

            chart_path, chart_name = plot_chart(chart_folder, chart_choice["value"], agg_data, category_col, numeric_col)
            insight = generate_report_from_chart(chart_folder, chart_name, lang=lang) if chart_path else ""

            st.session_state.manual_reports.append({
                "pivot_table": agg_data,
                "chart_path": chart_path,
                "sheet_name": f"{category_col}_{numeric_col}",
                "insight": insight,
                "source": "MANUAL",
            })
        st.toast(trans(locale, "analysis_ready", "Analysis ready. Open the Report page for full details."), icon="✅")

# ===== TAB 3: AI Analysis =====
with tabs[2]:
    st.subheader(trans(locale, "tab_ai", "AI Analysis"))

    data = st.session_state.cleaned_data
    if data is None: no_data_msg(); st.stop()
    warn_if_not_clean()

    if st.button(trans(locale, "run_ai_auto", "Run AI Auto Analysis"), key="btn_ai_auto"):
        with st.spinner(trans(locale, "loading", "Loading...")):
            reports = ai_auto_analysis(data, lang=lang)
            st.session_state.ai_reports.extend(reports)
        st.toast(trans(locale, "analysis_ready", "Analysis ready. Open the Report page for full details."), icon="✅")

    with st.form("ai_ask_form", clear_on_submit=False):
        user_question = st.text_input(trans(locale, "ask_ai", "Ask AI about your data"), key="ai_question")
        ask = st.form_submit_button(trans(locale, "send_question", "Send Question"))

    if ask and user_question.strip():
        with st.spinner(trans(locale, "loading", "Loading...")):
            _, answer = ai_answer_question(data, user_question, lang=lang)
            st.markdown(f"**{trans(locale, 'ai_answer', 'AI Answer')}:** {answer}")

# ===== TAB 4: Reports =====
with tabs[3]:
    st.subheader(trans(locale, "tab_reports", "Reports"))

    data = st.session_state.cleaned_data
    if data is None: no_data_msg(); st.stop()

    manual_reports = st.session_state.manual_reports
    ai_reports     = st.session_state.ai_reports

    if not manual_reports and not ai_reports:
        st.info(trans(locale, "no_reports_yet", "No reports yet. Create charts in the Manual/AI tabs."))
    else:
        # Manual
        with st.expander(trans(locale, "manual_reports_section", "🛠 Manual Reports"), expanded=False):
            if not manual_reports:
                st.info(trans(locale, "no_manual", "No manual charts."))
            else:
                for idx, report in enumerate(list(manual_reports)):
                    chart_path = report.get("chart_path"); insight = report.get("insight", "")
                    if chart_path and os.path.exists(chart_path):
                        st.image(chart_path, caption=trans(locale, "manual_chart_caption_fmt", "Manual Chart {i}").format(i=idx+1))
                    st.markdown(f"**{trans(locale, 'insight', 'Insight')}:** {insight}")
                    if st.button(trans(locale, "remove_manual_chart_fmt", "🗑 Remove Manual Chart {i}").format(i=idx+1), key=f"remove_manual_{idx}"):
                        if chart_path: remove_chart(chart_path)
                        st.session_state.manual_reports.pop(idx); st.rerun()

        # AI
        with st.expander(trans(locale, "ai_reports_section", "🤖 AI Reports"), expanded=True):
            if not ai_reports:
                st.info(trans(locale, "no_ai", "No AI charts."))
            else:
                for idx, report in enumerate(list(ai_reports)):
                    chart_path = report.get("chart_path"); insight = report.get("insight", "")
                    if chart_path and os.path.exists(chart_path):
                        st.image(chart_path, caption=trans(locale, "ai_chart_caption_fmt", "AI Chart {i}").format(i=idx+1))
                    st.markdown(f"**{trans(locale, 'insight', 'Insight')}:** {insight}")
                    if st.button(trans(locale, "remove_ai_chart_fmt", "🗑 Remove AI Chart {i}").format(i=idx+1), key=f"remove_ai_{idx}"):
                        if chart_path: remove_chart(chart_path)
                        st.session_state.ai_reports.pop(idx); st.rerun()

        # Export
        st.markdown("---")
        if st.button(trans(locale, "export_all", "📥 Export All Reports"), key="btn_export_all"):
            with st.spinner(trans(locale, "creating_combined", "⏳ Creating combined Excel report...")):
                all_reports = []
                for r in st.session_state.manual_reports:
                    rr = r.copy(); rr["source"] = rr.get("source", "MANUAL")
                    rr["sheet_name"] = f"MAN_{rr.get('sheet_name','manual')}"
                    all_reports.append(rr)
                for r in st.session_state.ai_reports:
                    rr = r.copy(); rr["source"] = rr.get("source", "AI")
                    rr["sheet_name"] = rr.get("sheet_name","ai") if rr.get("sheet_name","").startswith("AI_") else f"AI_{rr.get('sheet_name','ai')}"
                    all_reports.append(rr)

                report_path = generate_excel_report(st.session_state.cleaned_data, all_reports,
                                                    f"all_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            st.success(trans(locale, "export_success", "Export success. Please download your file below."))
            if os.path.exists(report_path):
                with open(report_path, "rb") as f:
                    st.download_button(
                        label=trans(locale, "download_all", "Download All Reports"),
                        data=f,
                        file_name=os.path.basename(report_path),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key="btn_download_all"
                    )
