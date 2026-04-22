import openpyxl
import os

file_path = "LEVEL 100 DATABASE 25_26 (Responses).xlsx"
if os.path.exists(file_path):
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active
    print(f"Sheet: {ws.title}")
    for row in ws.iter_rows(max_row=2, values_only=True):
        print(row)
else:
    print("File not found.")
