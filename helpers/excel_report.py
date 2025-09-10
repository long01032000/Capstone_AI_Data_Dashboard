# helpers/excel_report.py
import os
import pandas as pd

def _unique_sheetname(name: str, used: set, maxlen: int = 31) -> str:
    """Excel-safe & unique sheet name."""
    invalid = '[]:*?/\\'
    for ch in invalid:
        name = name.replace(ch, '-')
    name = (name or "Sheet")[:maxlen]
    base = name
    i = 1
    while name in used or not name:
        suf = f"_{i}"
        name = base[:maxlen - len(suf)] + suf
        i += 1
    used.add(name)
    return name

def generate_excel_report(df: pd.DataFrame, reports: list, filename: str) -> str:
    """
    Excel output with:
      - 'DATA' sheet (first 200k rows)
      - For each report sheet:
          * Pivot table at A1
          * Chart image at F1
          * AI Insight at F24
    Returns absolute path.
    """
    os.makedirs("./exports", exist_ok=True)
    out_path = os.path.abspath(os.path.join("./exports", f"{filename}.xlsx"))

    # Make sheet names safe/unique
    used = set()
    for r in reports:
        r["sheet_name"] = _unique_sheetname(str(r.get("sheet_name", "sheet")), used)

    with pd.ExcelWriter(out_path, engine="xlsxwriter") as writer:
        wb = writer.book
        wrap = wb.add_format({"text_wrap": True, "valign": "top"})
        note = wb.add_format({"italic": True, "font_color": "#666666"})

        # 1) DATA sheet
        if isinstance(df, pd.DataFrame) and not df.empty:
            df.head(200_000).to_excel(writer, sheet_name="DATA", index=False)

        # 2) Report sheets
        for r in reports:
            name = r["sheet_name"]
            pt = r.get("pivot_table")

            if isinstance(pt, pd.DataFrame) and not pt.empty:
                # Writing pivot creates the worksheet
                pt.to_excel(writer, sheet_name=name, index=False, startrow=0, startcol=0)
                ws = writer.sheets[name]
            else:
                # Create empty worksheet and add a note
                ws = wb.add_worksheet(name)
                writer.sheets[name] = ws
                ws.write("A1", "No pivot table data.", note)

            # Ensure column F is wide enough for image/insight
            ws.set_column("F:F", 60)

            # 2.1) Insert chart image at F1
            chart_path = r.get("chart_path")
            if chart_path and os.path.exists(chart_path):
                try:
                    ws.insert_image("F1", chart_path, {"x_scale": 0.6, "y_scale": 0.6, "object_position": 1})
                except Exception as e:
                    ws.write("F1", f"[Chart insert error] {e}", note)
            else:
                ws.write("F1", "No chart image found.", note)

            # 2.2) Write AI Insight at F24
            insight_text = str(r.get("insight", "")).strip() or "No insight."
            ws.write("F24", insight_text, wrap)

    return out_path
