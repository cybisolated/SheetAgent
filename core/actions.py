import abc
import sqlite3
from pathlib import Path
from typing import Any, List, Optional, Tuple

import records
import sqlalchemy

from utils.common import ToolResponse
from utils.enumeration import EXEC_CODE, OBS_TYPE
from utils.types import TableRepType
from utils.utils import *

from .sandbox import Sandbox


class ActionExecutor(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def utilize(self, action_input) -> ToolResponse:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError()


class PythonInterpreter(ActionExecutor):
    def __init__(self, sandbox: Sandbox) -> None:
        super().__init__()
        self.sandbox = sandbox

    def get_name(self) -> str:
        return "Python Interpreter"

    def utilize(self, action_input) -> ToolResponse:
        response = self.sandbox.step(action_input, dummy=False)
        exec_code, output = response.code, response.msg
        if exec_code == EXEC_CODE.FAIL:
            obs = "Error occurs:\n" + output
            obs_type = OBS_TYPE.NOT_NULL
        else:
            if output == "":
                obs = "Executed successfully, no output."
                obs_type = OBS_TYPE.NULL
            else:
                obs = "Executed successfully, output:\n" + output
                obs_type = OBS_TYPE.NOT_NULL
        return ToolResponse(exec_code, obs, obs_type)


class SheetSelector(ActionExecutor):
    def __init__(self, db_path: Path, table_rep: TableRepType, add_row_number: bool, lower_case: bool) -> None:
        super().__init__()
        self.db_path = db_path
        self.table_rep = table_rep
        self.sqlite_conn = sqlite3.connect(self.db_path)

        self.db = records.Database(f"sqlite:///{self.db_path}")
        self.records_conn = self.db.get_connection()
        self.add_row_number = add_row_number
        self.lower_case = lower_case
        if add_row_number:
            self.row_number_column = "Row Number"
            if lower_case:
                self.row_number_column = self.row_number_column.lower()

    def get_name(self) -> str:
        return "Sheet Selector"

    def get_tables(self, table_names: Optional[List[str]] = None):
        table_names = table_names if table_names is not None else self.db.get_table_names()
        return [self.get_table(table_name) for table_name in table_names]

    def get_table(self, table_name: str):
        sql_query = "SELECT * FROM `{}`".format(table_name)
        _, tb = self.execute_query(sql_query)
        return tb

    def get_create_table_sqls(self, table_names: Optional[List[str]] = None):
        table_names = table_names if table_names is not None else self.db.get_table_names()
        return [self.get_create_table_sql(table_name) for table_name in table_names]

    def get_create_table_sql(self, table_name: str):
        table_create_query_sql = 'SELECT sql FROM sqlite_master WHERE type="table" AND name = "{}"'.format(table_name)
        _, res = self.execute_query(table_create_query_sql, convert=False)
        return res

    def get_example_rows_list(self, table_names: Optional[List[str]] = None):
        table_names = table_names if table_names is not None else self.db.get_table_names()
        return [self.get_example_rows(table_name) for table_name in table_names]

    def get_example_rows(self, table_name: str):
        _, tb = self.execute_query("SELECT * FROM `{}` LIMIT 3".format(table_name))
        return tb

    def update_table(self, table_name: str, tb_new: pd.DataFrame):
        if self.add_row_number:  # add row number column
            row_number_col = "row number" if self.lower_case else "Row Number"
            tb_new.insert(0, row_number_col, range(1, 1 + len(tb_new)))
        tb_new.to_sql(table_name, self.sqlite_conn, if_exists="replace", index=False)

    def execute_query(self, sql_query: str, convert=True) -> Tuple[EXEC_CODE, Any]:
        if "select" not in sql_query.lower():
            return EXEC_CODE.FAIL, "Only support SELECT query."
        if self.add_row_number:
            if (
                "sqlite_master" in sql_query.lower()
                or sql_query.lower().startswith("select *")
                or sql_query.lower().startswith("select count")
                or (
                    "row number" in sql_query.lower()
                    and sql_query.lower().index("row number") < sql_query.lower().index("from")
                )
                # or "DISTINCT" in sql_query
                or "ALL" in sql_query
            ):  # do not need to add "Row Number" column
                sql_query_new = sql_query
            elif "DISTINCT" in sql_query:
                sql_query_new = (
                    sql_query[: sql_query.index("DISTINCT") + len("DISTINCT")]
                    + ' "Row Number", '
                    + sql_query[sql_query.index("DISTINCT") + len("DISTINCT") :]
                )
            else:
                sql_query_new = 'SELECT "Row Number", ' + sql_query[7:]
        else:
            sql_query_new = sql_query

        try:
            out = self.records_conn.query(sql_query_new)
        except sqlite3.OperationalError as e:
            return EXEC_CODE.FAIL, "Error occurs:\n" + str(e)
        except sqlalchemy.exc.OperationalError as e:  # type: ignore
            return EXEC_CODE.FAIL, "Error occurs:\n" + str(e)
        except Exception as e:
            return EXEC_CODE.FAIL, "Error occurs:\n" + str(e)

        results: List = out.all()
        if results is None or len(results) == 0:  # no query results
            return EXEC_CODE.SUCCESS, None

        unmerged_results = []
        headers = out.dataset.headers
        for i in range(len(results)):
            unmerged_results.append(results[i].values())
        tb = {"header": headers, "rows": unmerged_results}

        if "sqlite_master" in sql_query.lower() or sql_query.lower().startswith("select count"):
            return EXEC_CODE.SUCCESS, tb["rows"][0][0]

        if convert:
            try:
                tb = eval(f"sqltb2{self.table_rep}(tb, {self.add_row_number}, {self.lower_case})")
            except Exception as e:
                return EXEC_CODE.FAIL, e

        return EXEC_CODE.SUCCESS, tb

    def utilize(self, action_input: str) -> ToolResponse:
        exec_code, obs = self.execute_query(action_input)
        if obs is None:
            obs = "Executed successfully, the query result is empty."
            obs_type = OBS_TYPE.NULL
        else:
            obs_type = OBS_TYPE.NOT_NULL

        return ToolResponse(exec_code, obs, obs_type)


class AnswerSubmitter(ActionExecutor):
    def __init__(self):
        super().__init__()

    def get_name(self) -> str:
        return "Answer Submitter"

    def utilize(self, action_input) -> ToolResponse:
        return ToolResponse(
            EXEC_CODE.SUCCESS,
            f'Your answer "{action_input}" is successfully saved.',
            OBS_TYPE.NOT_NULL,
        )
