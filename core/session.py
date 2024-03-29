import os
import re
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml
from colorama import Fore

from dataset.dataloader import SheetProblem
from prompt.informer import InformerPrompt
from prompt.planner import PlannerPrompt
from utils.common import ToolResponse
from utils.enumeration import *
from utils.exceptions import *
from utils.types import TableRepType
from utils.utils import parse_action, parse_action_input, parse_think, valid_action

from .actions import AnswerSubmitter, PythonInterpreter, SheetSelector
from .assistant import Informer, Planner
from .rag import MilvusStore
from .sandbox import Sandbox


class Session:
    def __init__(
        self,
        problem: SheetProblem,
        output_dir: Path,
        model_type: MODEL_TYPE,
        table_rep: TableRepType,
        sandbox: Sandbox,
        few_shot_planner: bool,
        api_config: Optional[dict],
        milvus_config: Optional[dict],
        with_informer: bool = False,
        few_shot_informer: bool = False,
        with_retriever: bool = False,
        add_row_number: bool = False,
        lower_case: bool = True,
        verbose: bool = False,
    ):
        self.problem = problem
        self.output_dir = output_dir
        self.model_type = model_type
        self.table_rep = table_rep
        self.few_shot_planner = few_shot_planner
        self.with_informer = with_informer
        self.few_shot_informer = few_shot_informer
        self.with_retriever = with_retriever
        self.max_step_planner = 10
        self.verbose = verbose
        self.api_config = api_config

        self.sandbox = sandbox
        self.sandbox.load_workbook(self.problem.workbook_path)

        # store the answers
        self.answers = []
        # store the thoughts of agent
        self.thoughts = []

        os.makedirs(output_dir, exist_ok=True)

        config_api = yaml.load(open(api_config, "r"), Loader=yaml.FullLoader)
        # construct milvus store
        if self.with_retriever:
            config_milvus = yaml.load(open(milvus_config, "r"), Loader=yaml.FullLoader)
            self.vector_store = MilvusStore(**config_milvus)

        # build tools
        python_interpreter = PythonInterpreter(sandbox=self.sandbox)
        sheet_selector = SheetSelector(
            db_path=self.problem.db_path, table_rep=self.table_rep, add_row_number=add_row_number, lower_case=lower_case
        )
        answer_subumitter = AnswerSubmitter()
        self.tools = {
            python_interpreter.get_name(): python_interpreter,
            sheet_selector.get_name(): sheet_selector,
            answer_subumitter.get_name(): answer_subumitter,
        }
        key_info = None
        if self.with_informer:
            self.system_prompt_informer, self.user_init_prompt_informer = self.construct_informer_prompt()
            # construct informer
            self.informer = Informer(
                self.system_prompt_informer,
                model_type=self.model_type,
                few_shot=few_shot_informer,
                api_config=config_api,
            )
            key_info = self.step_informer()

        # construct agent
        self.system_prompt_planner, self.user_init_prompt_planner = self.construct_planner_prompt(key_info)
        self.planner = Planner(
            self.system_prompt_planner,
            model_type=self.model_type,
            few_shot=few_shot_planner,
            table_rep=table_rep,
            with_informer=self.with_informer,
            api_config=config_api,
        )

    def construct_planner_prompt(self, key_info: Optional[str]):
        system_prompt = (
            PlannerPrompt.SYSTEM_PROMPT_WITH_INFORMER if self.with_informer else PlannerPrompt.SYSTEM_PROMPT_WO_INFORMER
        )
        system_prompt = (
            system_prompt + "\nI will give you few examples to help you understand."
            if self.few_shot_planner
            else system_prompt
        )
        if self.with_informer:
            system_prompt = system_prompt.format(table_rep=self.table_rep)
        assert self.problem.context is not None
        context = "Now it's your turn. " + self.problem.context if self.few_shot_planner else self.problem.context

        sheet_names = self.sandbox.get_existing_sheet_names()

        table_create_sqls = self.tools[ACTION.SHEET_SELECTOR.value].get_create_table_sqls(sheet_names)
        example_rows_list = self.tools[ACTION.SHEET_SELECTOR.value].get_example_rows_list(sheet_names)

        db_descs = []
        for _, (sheet_name, sql, rows) in enumerate(zip(sheet_names, table_create_sqls, example_rows_list)):
            db_descs.append(f'Table create SQL statement for "{sheet_name}":\n{sql}')

        if key_info is not None:
            key_info = f"/*\nPotentially helpful information:\n{key_info}\n*/"
        user_init_prompt = (
            PlannerPrompt.USER_INIT_PROMPT_WITH_INFORMER
            if self.with_informer
            else PlannerPrompt.USER_INIT_PROMPT_WO_INFORMER
        )

        user_init_prompt = user_init_prompt.format(
            context=context,
            sheet_state=self.sandbox.get_sheet_state(),
            instruction=self.problem.instruction,
            key_info=key_info if key_info is not None else "",
        )

        return system_prompt, user_init_prompt

    def construct_informer_prompt(self):
        system_prompt = InformerPrompt.SYSTEM_PROMPT_NEW

        system_prompt = (
            system_prompt + "\nI will give you few examples to help you understand."
            if self.few_shot_informer
            else system_prompt
        )

        db_descs = []

        sheet_names = self.sandbox.get_existing_sheet_names()
        table_create_sqls = self.tools[ACTION.SHEET_SELECTOR.value].get_create_table_sqls(sheet_names)
        example_rows_list = self.tools[ACTION.SHEET_SELECTOR.value].get_example_rows_list(sheet_names)
        for _, (sheet_name, sql, rows) in enumerate(zip(sheet_names, table_create_sqls, example_rows_list)):
            db_descs.append(
                f'Table schema of "{sheet_name}":\n{sql}\n/*\n3 example rows:\nSELECT * FROM "{sheet_name}" LIMIT 3;\n{rows}\n*/'
            )
        db_descs = "\n".join(db_descs)
        thoughts = (
            "Your patner does not have any thoughts at the moment."
            if len(self.thoughts) == 0
            else "\n".join([f"{idx+1}. {t}" for idx, t in enumerate(self.thoughts)])
        )
        user_init_prompt = InformerPrompt.USER_INIT_PROMPT_NEW.format(
            instruction=self.problem.instruction,
            thoughts=thoughts,
            sheet_state=self.sandbox.get_sheet_state(),
            table_desc=db_descs,
        )

        return system_prompt, user_init_prompt

    def get_observation(self, action: str, action_input: str) -> ToolResponse:
        # when call this function, the action is already validated, so the tool must exist
        tool = self.tools[action]
        response = tool.utilize(action_input)

        return response

    def run(self):
        if self.verbose:
            print(Fore.YELLOW + f"System prompt:\n{self.system_prompt_planner}\n")
        prompt = self.user_init_prompt_planner
        last_sheet_state = ""

        for step in range(self.max_step_planner):
            if self.verbose:
                print(Fore.RESET + f"========Round {step + 1}========\n")
                print(Fore.BLUE + f"Observation:\n{prompt}\n")
            try:
                # ask
                msg = self.planner.ask(prompt)
            except TokenLimitError as e:
                print(Fore.RED + str(e))
                self.save()
                break

            if msg is None:
                continue

            if self.verbose:
                print(Fore.GREEN + f"Planner:\n{msg}\n")
            if "Done" in msg or "Finish" in msg:  # task finished
                self.save()
                break

            try:
                think = parse_think(msg)
                action = parse_action(msg)  # may raise FormatMismatchError
                action = valid_action(action)  # may raise ToolNotFoundError
                # action = "Python Interpreter"
                action_input = parse_action_input(
                    msg, action
                )  # may raise ActionInputParseError and FormatMismatchError
            except (ToolNotFoundError, FormatMismatchError, ActionInputParseError) as e:
                if self.verbose:
                    print(Fore.RED + str(e))
                self.save()
                break
            except Exception as e:
                if self.verbose:
                    print(Fore.RED + str(e))
                self.save()
                break

            assert action_input is not None

            response = self.get_observation(action, action_input)
            exec_code, obs, obs_type = response.code, response.obs, response.obs_type

            if exec_code == EXEC_CODE.FAIL:  # only action `Python` could return `EXEX_CODE.FAIL`
                if self.with_retriever:
                    docs = self.vector_store.mmr_search(query=action_input, k=2)
                    docs_string = ""
                    for idx, doc in enumerate(docs):
                        docs_string += f"Code fragment {idx + 1}\n```\n{doc}\n```"
                        if idx != len(docs) - 1:
                            docs_string += "\n\n"
                    observation = PlannerPrompt.OBSERVATION_FAIL_WITH_RETRIEVE
                else:
                    docs_string = None
                    observation = PlannerPrompt.OBSERVATION_FAIL_WO_RETRIEVE
                observation = observation.format(
                    observation=obs,
                    docs=docs_string if docs_string is not None else "",
                    next_step_prompt=PlannerPrompt.NEXT_STEP_FAIL,
                )
            else:
                if self.with_informer:
                    self.thoughts.append(think)
                    key_info = self.step_informer()
                    # key_info = None
                    observation = PlannerPrompt.OBSERVATION_SUCC_WITH_INFORMER
                else:
                    key_info = None
                    observation = PlannerPrompt.OBSERVATION_SUCC_WO_INFORMER
                sheet_state = self.sandbox.get_sheet_state()
                if sheet_state != last_sheet_state:  # update database

                    self.sandbox.save_temp_workbook(self.output_dir)
                    wb = pd.read_excel(self.output_dir / "workbook_temp.xlsx", sheet_name=None)
                    for sheet_name, df in wb.items():
                        # table_name = f"ws_{title2camel(sheet_name)}"
                        table_name = sheet_name
                        if not df.empty:
                            self.tools["Sheet Selector"].update_table(table_name, df)

                    last_sheet_state = sheet_state

                if key_info is not None:
                    key_info = f"/*\nPotentially helpful information for your next step:\n{key_info}\n*/"
                observation = observation.format(
                    observation=obs,
                    sheet_state=sheet_state,
                    key_info=key_info if key_info is not None else "",
                    next_step_prompt=PlannerPrompt.NEXT_STEP_SUCC,
                )

            if "answer" in action.lower():  # save answer
                self.answers.append(action_input)

            prompt = observation

        self.save()

    def step_informer(self) -> Optional[str]:
        max_step = 3

        # informer
        def extract_select_line(input_string):
            # pattern = r'\bSELECT\b.*?;'
            match = re.search(r"\bSELECT\b.*?;", input_string, re.DOTALL)
            if not match:
                return None

            return match.group(0).strip()

        sheet_names = self.sandbox.get_existing_sheet_names()
        table_create_sqls = self.tools[ACTION.SHEET_SELECTOR.value].get_create_table_sqls(sheet_names)
        example_rows_list = self.tools[ACTION.SHEET_SELECTOR.value].get_example_rows_list(sheet_names)
        db_descs = []
        for _, (sheet_name, sql, rows) in enumerate(zip(sheet_names, table_create_sqls, example_rows_list)):
            db_descs.append(
                f'Table schema of "{sheet_name}":\n{sql}\n/*\n3 example rows:\nSELECT * FROM "{sheet_name}" LIMIT 3;\n{rows}\n*/'
            )
        db_descs = "\n".join(db_descs)

        thoughts = (
            "The spreadsheet agent has not started any subtask yet."
            if len(self.thoughts) == 0
            else "\n".join([f"{idx+1}. {t}" for idx, t in enumerate(self.thoughts)])
        )
        user_init_prompt = InformerPrompt.USER_INIT_PROMPT_NEW.format(
            instruction=self.problem.instruction,
            thoughts=thoughts,
            sheet_state=self.sandbox.get_sheet_state(),
            table_desc=db_descs,
        )

        # prompt = self.user_init_prompt_informer
        prompt = user_init_prompt
        if self.few_shot_informer:
            prompt = "Now it's your turn. " + prompt

        sql_res = None
        skip_retrevial = False
        for _ in range(max_step):
            try:
                msg = self.informer.ask(prompt)
            except Exception as e:
                print(e)
                skip_retrevial = True
                break

            assert msg is not None
            print(Fore.MAGENTA + f"Informer:\n{msg}")
            if "pass" in msg.lower():  # no need to retrieve
                skip_retrevial = True
                break

            sql = extract_select_line(msg)
            if sql is None:
                continue

            if ";" not in sql:
                sql = sql + ";"
            try:
                res = self.get_observation("Sheet Selector", sql)
            except Exception as e:
                print(e)
                continue
            exec_code, obs, obs_type = res.code, res.obs, res.obs_type
            if exec_code == EXEC_CODE.SUCCESS and obs_type == OBS_TYPE.NOT_NULL:
                sql_res = obs
                break
            if exec_code == EXEC_CODE.FAIL:
                prompt = f"Error occurs when executing the statement:\n{obs}\nPlease give another SQLite statement:"
            elif obs_type == OBS_TYPE.NULL:
                prompt = f"The query result is empty. Please give another SQLite statement:"

        # assert sql_res is not None

        key_info = None
        if not skip_retrevial and sql_res is not None:
            sql_res = str(sql_res) if not isinstance(sql_res, str) else sql_res
            key_info = f"{sql}\n{sql_res}"
        return key_info

    def save(self):
        self.sandbox.save(self.output_dir)
        self.planner.save(self.output_dir)
        if len(self.answers) != 0:
            with open(self.output_dir / "answers.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(self.answers))
