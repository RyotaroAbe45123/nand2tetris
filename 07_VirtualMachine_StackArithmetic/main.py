from enum import Enum
import sys


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
    def __init__(self, vm_file_path: str) -> None:
        """
        入力ファイルを受け付ける
        """
        with open(vm_file_path, "r") as fp:
            self.asm = fp.read()
            self.asm = self.asm.split("\n")

        self.order = None
    
    def has_more_lines(self) -> bool:
        """
        入力にまだ行があるか判断する
        """
        return True if self.asm else False

    def advance(self) -> None:
        """
        入力から次の命令を読み込み、それを現在の命令にする
        """
        self.order = self.asm.pop(0)
        if self.order.startswith("//") or self.order == "":
            self.order = None

    def commnad_type(self) -> Command:
        """
        現在のコマンドの種類を返す
        """
        if len(self.order.split()) == 1:
            return Command.ARITHMETIC
        elif len(self.order.split()) == 3:
            if self.order.startswith("push"):
                return Command.PUSH
            elif self.order.startswith("pop"):
                return Command.POP
        else:
            print(self.order)
    
    def arg1(self) -> str:
        """
        現在のコマンドの最初の引数を返す
        C_ARITHMETICの場合、コマンド自体（add, subなど）を返す
        """
        return self.order.split()[1]
    
    def arg2(self) -> int:
        """
        現在のコマンドの2番目の引数を返す
        C_PUSH, C_POP, C_FUNCTION, C_CALLのみ呼ぶ
        """
        return int(self.order.split()[2])


class CodeWriter:
    def __init__(self, file_path: str) -> None:
        # 出力ファイルのProg.hackを作成する
        self.asm_file_path = f"{file_path.replace('vm', 'asm')}"
        with open(self.asm_file_path, "w") as fp:
            fp.write("")
        
        self._set_stack_base_to_stack_pointer(stack_base=256)

    def _set_stack_base_to_stack_pointer(self, stack_base: int) -> None:
        with open(self.asm_file_path, "a") as fp:
            fp.write("// initialize stack pointer\n")
            fp.write(f"@{stack_base}\n")
            fp.write("D=A\n")
            fp.write("@SP\n")
            fp.write("M=D\n")
    
    def _create_infinite_loop(self) -> None:
        with open(self.asm_file_path, "a") as fp:
            fp.write("(END)\n")
            fp.write("  @END\n")
            fp.write("  0;JMP\n")

    def _store_data_in_stack(self) -> None:
        with open(self.asm_file_path, "a") as fp:
            fp.write("@SP\n")
            fp.write("A=M\n")
            fp.write("M=D\n")
    
    def _get_data_from_stack(self) -> None:
        with open(self.asm_file_path, "a") as fp:
            fp.write("@SP\n")
            fp.write("A=M\n")
            fp.write("D=M\n")
    
    def _increase_stack_pointer(self) -> None:
        with open(self.asm_file_path, "a") as fp:
            fp.write("@SP\n")
            fp.write("M=M+1\n")
    
    def _decrease_stack_pointer(self) -> None:
        with open(self.asm_file_path, "a") as fp:
            fp.write("@SP\n")
            fp.write("M=M-1\n")
    
    def write_arithmetic(self, command: str) -> None:
        """
        算術論理コマンドに対応するアセンブリコードを書く
        """
        if command == "add":
            with open(self.asm_file_path, "a") as fp:
                fp.write("@SP\n")
                fp.write("AM=M-1\n")
                fp.write("D=M\n")
                fp.write("@SP\n")
                fp.write("A=M-1\n")
                fp.write("M=D+M\n")
    
    def write_push_pop(self, command: Command, segment: str, index: int) -> None:
        """
        PUSH, POPコマンドに対応するアセンブリコードを書く
        """
        if segment == "constant":
            with open(self.asm_file_path, "a") as fp:
                fp.write(f"@{index}\n")
                fp.write("D=A\n")
        if command == Command.PUSH:
            self._store_data_in_stack()
            self._increase_stack_pointer()
        elif command == Command.POP:
            self._decrease_stack_pointer()
            self._get_data_from_stack()
    
    def close(self) -> None:
        """
        出力ファイル/ストリームを閉じる
        """
        self._create_infinite_loop()


class VMTranslator:
    def __init__(self, vm_file_name: str) -> None:
        self.vm_file_path = f"./{vm_file_name}"
        self.parser = Parser(vm_file_path=self.vm_file_path)
        self.code_writer = CodeWriter(file_path=self.vm_file_path)

    def translate(self) -> None:
        while self.parser.has_more_lines():
            self.parser.advance()
            if self.parser.order is None:
                continue

            with open(self.code_writer.asm_file_path, "a") as fp:
                fp.write(f"// {self.parser.order}\n")
            if self.parser.commnad_type() == Command.ARITHMETIC:
                self.code_writer.write_arithmetic(command=self.parser.order)
            elif self.parser.commnad_type() == Command.PUSH or self.parser.commnad_type() == Command.POP:
                self.code_writer.write_push_pop(
                    command=self.parser.commnad_type(),
                    segment=self.parser.arg1(),
                    index=self.parser.arg2()
                )
            else:
                print(self.parser.order, self.parser.commnad_type())
            
def main():
    # コマンドライン引数で入力ファイルの名前を受け取る
    args = sys.argv
    if len(args) < 2:
        print("ファイル名を入力してください。")
        return
    vm_file_name = args[1]

    vmtranslator = VMTranslator(vm_file_name=vm_file_name)
    vmtranslator.translate()

if __name__ == "__main__":
    main()