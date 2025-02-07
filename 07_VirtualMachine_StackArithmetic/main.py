from enum import Enum


class Command(Enum):
    ARITHMETIC = "C_ARITHMETIC"
    PUSH = "C_PUSH"
    POP = "C_POP"
    LABEL = "C_LABEL"
    GOTO = "C_GOTO"
    IF = "C_IF"
    FUNCTION = "C_FUNCTION"
    RETURN = "C_RETURN"
    CALL = "C_CALL"


class Parser:
    def __init__(self) -> None:
        pass

    def has_more_lines(self) -> bool:
        pass

    def advance(self) -> None:
        pass

    def commnad_type(self) -> Command:
        pass
    
    def arg1(self) -> str:
        pass
    
    def arg2(self) -> int:
        pass


class CodeWriter:
    def __init__(self, file_path: str) -> None:
        pass
    
    def write_arithmetic(self, command: str) -> None:
        pass
    
    def write_push_pop(self, command: Command, segment: str, index: int) -> None:
        pass
    
    def close(self) -> None:
        pass


class VMTranslator:
    pass

