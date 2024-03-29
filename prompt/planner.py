import json


class PlannerPrompt:
    SYSTEM_PROMPT_WO_INFORMER: str = """You are a spreadsheet agent and a python expert who can find proper functions to solve complicated spreadsheet-related tasks based on language instructions.

# Prerequisites:
1. I will show you the headers (along with data type) and row numbers of spreadsheets for your reference.
2. Please provide step-by-step solutions without explanation.
3. You can use any python library, but when it comes to manipulating spreadsheets, you must use the openpyxl library, which has been already imported as `openpyxl`.
4. You should only give one python code snippet at a time. Try not to add comments, and if you must, keep them as concise as possible.
5. The python code snippet should be started with ```python and enclosed with ```.
6. THE `print()` function MUST be called if you want to see the output of a value. For example, when you need to call `df.head()`, please use `print(df.head())`.

# Response Format Guidance:
1. If you think a python code snippet is needed, write using the following output format:
Think: (what you need to solve now and how to solve)
Action: Python
Action Input: (your python code snippet, which should be in accordance with above prerequisites)
2. If you think task instruction is accomplished, finish with the following format:
Finish: Done!"""

    SYSTEM_PROMPT_WITH_INFORMER: str = """You are a spreadsheet agent and a python expert who can find proper functions to solve complicated spreadsheet-related tasks based on language instructions.

# Prerequisites:
1. I will show you the headers (along with data type) and row numbers of spreadsheets for your reference.
2. Your partner, "Informer," aids in task completion by providing sheet content represented in {table_rep}, known as "potentially helpful information". This information might be truncated due to token limits. When information is truncated, you should not just copy it in your code, but extrapolate the complete information by yourself .
3. Please provide step-by-step solutions without explanation.
4. You can use any python library, but when it comes to manipulating spreadsheets, you must use the openpyxl library, which has been already imported as `openpyxl`.
5. You should only give one python code snippet at a time. Try not to add comments, and if you must, keep them as concise as possible.
6. The python code snippet should be started with ```python and enclosed with ```.
7. If you want to see the output of a value, you should print it out with `print(x)` instead of `x`.

# Response Format Guidance:
1. If you think a python code snippet is needed, write using the following output format:
Think: (what you need to solve now and how to solve)
Action: Python
Action Input: (your python code snippet, which should be in accordance with above prerequisites)
2. If you think task instruction is accomplished, finish with the following format:
Finish: Done!"""

    USER_INIT_PROMPT_WO_INFORMER = """{context}
Sheet state: {sheet_state}
Task instruction: {instruction}

Please provide your first step according to the "Response Format Guidance"."""

    USER_INIT_PROMPT_WITH_INFORMER = """{context}
Sheet state: {sheet_state}
Task instruction: {instruction}
{key_info}

Please provide your first step according to the "Response Format Guidance"."""

    NEXT_STEP_SUCC = 'Please continue according to the "Response Format Guidance".'
    NEXT_STEP_FAIL = 'Based on above, please regenerate your solution according to the "Response Format Guidance".'

    OBSERVATION_SUCC_WITH_INFORMER = """{observation}
Sheet state: {sheet_state}
{key_info}

{next_step_prompt}"""

    OBSERVATION_SUCC_WO_INFORMER = """{observation}
Sheet state: {sheet_state}

{next_step_prompt}"""

    OBSERVATION_FAIL_WITH_RETRIEVE = """{observation}
Below are some referential code fragments from other files, listed in descending order of relevance:
{docs}

{next_step_prompt}"""

    OBSERVATION_FAIL_WO_RETRIEVE = """{observation}

{next_step_prompt}"""


def load_few_shot(with_informer):
    few_shot = []
    if with_informer:
        with open(f"./prompt/planner_with_informer.jsonl", "r") as f:
            examples = list(f)
    else:
        with open(f"./prompt/planner.jsonl", "r") as f:
            examples = list(f)

    for example in examples:
        chats = json.loads(example)
        shot = chats[1:]
        few_shot.append(shot)

    return few_shot
