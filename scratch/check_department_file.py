import openpyxl
import os

file_path = "For Department.xlsx"
if os.path.exists(file_path):
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb.active
    print(f"Sheet: {ws.title}")
    # Print first few rows to see column structure
    for row in ws.iter_rows(max_row=5, values_only=True):
        print(row)
else:
    print("File not found.")
