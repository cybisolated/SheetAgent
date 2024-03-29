from enum import Enum


class ACTION(Enum):
    PYTHON_INTERPRETER = "Python Interpreter"
    SHEET_SELECTOR = "Sheet Selector"
    ANSWER_SUBMITTER = "Answer Submitter"


class EXEC_CODE(Enum):
    FAIL = -1
    SUCCESS = 0


class MODEL_TYPE(Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo-0125"
    GPT_3_5_TURBO_1106 = "gpt-3.5-turbo-1106"
    GPT_4 = "gpt-4"
    GPT_4_1106 = "gpt-4-1106-preview"
    GPT_4V = "gpt-4-1106-vision-preview"
    CLAUDE_OPUS = "claude-3-opus-20240229"
    CLAUDE_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_HAIKU = "claude-3-haiku-20240307"

    def __str__(self) -> str:
        return self.value


class OBS_TYPE(Enum):
    NULL = 0
    NOT_NULL = 1


class ROLE(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
