#excel_report.py
import os
import pandas as pd

def _unique_sheetname(name: str, used: set, maxlen: int = 31) -> str:
    """Tạo tên sheet an toàn + duy nhất theo giới hạn Excel."""
    invalid = '[]:*?/\\'
    for ch in invalid:
        name = name.replace(ch, '-')
    name = name[:maxlen]
    base = name
    i = 1
    while name in used or not name:
        suf = f"_{i}"
        name = (base[:maxlen - len(suf)] + suf) if base else f"Sheet{i}"
        i += 1
    used.add(name)
    return name

def generate_excel_report(df: pd.DataFrame, reports: list, filename: str) -> str:
    """
    df: DataFrame nguồn (có thể None)
    reports: list[dict] với các key tối thiểu:
        - 'sheet_name': str (sẽ được unique ở đây)
        - 'pivot_table': DataFrame hoặc None
        - 'insight': str
        - 'source': 'MANUAL' | 'AI' | ...
    filename: tên file không kèm đuôi
    """
    os.makedirs("./exports", exist_ok=True)
    out_path = os.path.join("./exports", f"{filename}.xlsx")

    # 1) Unique hóa tên sheet NGAY TẠI ĐÂY
    used = set()
    for r in reports:
        base = r.get("sheet_name", "sheet")
        r["sheet_name"] = _unique_sheetname(str(base), used)

    # 2) Ghi file
    # dùng xlsxwriter để có thể mở rộng insert ảnh sau này (nếu cần)
    with pd.ExcelWriter(out_path, engine="xlsxwriter") as writer:
        # (Optional) ghi INDEX sheet cho dễ tra cứu
        index_rows = []
        for r in reports:
            pt = r.get("pivot_table")
            index_rows.append({
                "Sheet": r.get("sheet_name"),
                "Source": r.get("source", ""),
                "Rows": getattr(pt, "shape", [0, 0])[0] if pt is not None else 0,
                "Cols": getattr(pt, "shape", [0, 0])[1] if pt is not None else 0,
                "Insight (truncated)": (r.get("insight") or "")[:200],
            })
        idx_df = pd.DataFrame(index_rows)
        if not idx_df.empty:
            idx_df.to_excel(writer, index=False, sheet_name="INDEX")

        # (Optional) ghi dữ liệu gốc
        if isinstance(df, pd.DataFrame) and not df.empty:
            df_head = df.head(200000)  # tránh file quá nặng
            df_head.to_excel(writer, index=False, sheet_name="DATA")

        # Ghi từng report
        for r in reports:
            sheet_name = r["sheet_name"]
            ws_startrow = 3  # để chừa 3 dòng header
            ws = writer.book.add_worksheet(sheet_name)
            writer.sheets[sheet_name] = ws

            # Header
            ws.write(0, 0, f"Source: {r.get('source','')}")
            ws.write(1, 0, f"Insight: {r.get('insight','')}")

            # Pivot table (nếu có)
            pt = r.get("pivot_table")
            if isinstance(pt, pd.DataFrame) and not pt.empty:
                pt.to_excel(writer, index=False, sheet_name=sheet_name, startrow=ws_startrow)
            else:
                ws.write(ws_startrow, 0, "No pivot table data.")

            # (Optional) Nếu muốn nhúng ảnh chart_path thì bật đoạn dưới:
            # chart_path = r.get("chart_path")
            # if chart_path and os.path.exists(chart_path):
            #     # đặt ảnh dưới bảng, cách 2 dòng
            #     img_row = ws_startrow + (len(pt) + 2 if isinstance(pt, pd.DataFrame) else 4)
            #     ws.insert_image(img_row, 0, chart_path, {"x_scale": 0.8, "y_scale": 0.8})

    return out_path
