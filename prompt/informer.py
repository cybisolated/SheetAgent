import json


class InformerPrompt:
    SYSTEM_PROMPT = """You are a table retrieval expert who team up with a spreadsheet agent to accomplish complicated spreadsheet-related tasks. Your partner is good at manipulating spreadsheets; however, some operations require an understanding of the spreadsheet, so your job is to retrieve key information from spreadsheets for your partner's reference according to task instructions. 

Given the table schema and three example rows out of the table, write a SQLite query statement to extract the sub-table that contains the information needed to solve the task, e.g., `SELECT * from w WHERE age = 18;`. The SQLite statement does not need to directly solve the task. Assume you always have enough information when executing the SQLite statement.
Try to use fuzzy-match for values if you are not sure about the values. If there is no need to retrieve information from any spreadsheet, please type "pass"."""

    SYSTEM_PROMPT_NEW = """You are a table retrieval expert who team up with a spreadsheet agent to accomplish complicated spreadsheet-related tasks. Your partner excel in manipulating spreadsheets. However, some of manipulations require an understanding of specific content of the spreadsheet. Therefore, your role is to retrieve key information from spreadsheets for your partner's reference."""

    USER_INIT_PROMPT = """{table_desc}
Task instruction: {instruction}
Give your SQLite statement:"""

    USER_INIT_PROMPT_NEW = """To make it easier for you to retrieve, all sheets are stored in a SQLite database.
{table_desc}
Task instruction: {instruction}
Previous completed subtasks of the spreadsheet agent (which is presented from your partner's point of view and is more of your partner's thought while finishing the subtasks):
{thoughts}
Given the task instruction and subtasks your partner has completed, predict what your patner will solve next, and determine what content is most needed by your partner. Write only one SQLite select statement to achieve this goal. If there is no need to retrieve information from any spreadsheet, please type "pass".
Based on above, responde in the following format:
Think: (how do you think)
Action: (your SQLite statement, e.g., `SELECT * FROM w WHERE age < 18;`, or "pass")"""


def load_few_shot():
    few_shot = []
    with open(f"./prompt/informer.jsonl", "r") as f:
        examples = list(f)

    for example in examples:
        chats = json.loads(example)
        shot = chats[1:]
        few_shot.append(shot)

    return few_shot
