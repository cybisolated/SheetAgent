class ToolNotFoundError(Exception):
    def __init__(self, tool_name):
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' not found.")


class FormatMismatchError(Exception):
    def __init__(self):
        super().__init__(f"Agent did not return reponse in the desired format.")


class ActionInputParseError(Exception):
    def __init__(self, action):
        self.action_input = action
        super().__init__(f"Action input of '{action}' cannot be parsed.")

class CriticParseError(Exception):
    def __init__(self, msg) -> None:
        super().__init__(msg)

class TokenLimitError(Exception):
    def __init__(self, num_tokens:int, token_limit:int) -> None:
        super().__init__(f"Number of tokens {num_tokens} exceeds the limit {token_limit}.")