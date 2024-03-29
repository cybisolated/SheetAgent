from utils.enumeration import EXEC_CODE, OBS_TYPE


class SandboxResponse:
    def __init__(self, code: EXEC_CODE, msg: str) -> None:
        self.code = code
        self.msg = msg

    def __str__(self) -> str:
        return f"Sandbox Response: {self.code}, {self.msg}"

    def __repr__(self) -> str:
        return self.__str__()


class ToolResponse:
    def __init__(self, code: EXEC_CODE, obs: str, obs_type: OBS_TYPE) -> None:
        self.code = code
        self.obs = obs
        self.obs_type = obs_type

    def __str__(self) -> str:
        return f"Tool call Response: {self.code}, {self.obs}, {self.obs_type}"

    def __repr__(self) -> str:
        return self.__str__()
