import os
import sqlite3
from pathlib import Path
from typing import List, Optional

import openpyxl
import pandas as pd


class SheetProblem:
    def __init__(
        self, workbook_path: Path, db_path: Path, context: Optional[str], instruction: str, sheet_vars: List[str]
    ) -> None:
        self.workbook_path = workbook_path
        self.db_path = db_path
        self.context = context
        self.instruction = instruction
        self.sheet_vars = sheet_vars


def load_problem(workbook_path: Path, db_path: Path, instruction: str) -> SheetProblem:
    def create_database(wb_path: Path, db_path: Path) -> None:
        wb = pd.read_excel(wb_path, sheet_name=None)
        conn = sqlite3.connect(db_path)

        for sheet_name, df in wb.items():
            # add row number
            row_number_col = "row number"
            df.insert(0, row_number_col, range(1, 1 + len(df)))
            table_name = sheet_name
            if not df.empty:
                df.to_sql(table_name, conn, index=False, if_exists="replace")

    os.makedirs(db_path, exist_ok=True)
    db_path = db_path / "database.db"
    create_database(workbook_path, db_path)

    workbook = openpyxl.load_workbook(workbook_path)
    sheet_vars = workbook.sheetnames

    context = "The workbook is already loaded as `workbook` using openpyxl, you only need to load the sheet(s) you want to use manually. Besides, the workbook will be automatically saved, so you don't need to save it manually."
    return SheetProblem(
        workbook_path=workbook_path, db_path=db_path, context=context, instruction=instruction, sheet_vars=sheet_vars
    )
