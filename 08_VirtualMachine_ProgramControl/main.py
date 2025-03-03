from enum import Enum
import os
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


SEGMENT_MAP = {
    "stack": "SP",
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT"
}


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
        コマンドと同行にあるコメントも削除する
        """
        self.order = self.asm.pop(0)
        comment_index = self.order.find("//")
        if comment_index != -1:
            self.order = self.order[:comment_index]
        self.order = self.order.strip()
        if self.order.startswith("//") or self.order == "":
            self.order = None

    def commnad_type(self) -> Command:
        """
        現在のコマンドの種類を返す
        """
        command_list = self.order.split()
        command_length = len(command_list)
        if command_length == 1:
            if "return" in command_list:
                return Command.RETURN
            else:
                return Command.ARITHMETIC
        elif command_length == 2:
            if "label" in command_list:
                return Command.LABEL
            elif "goto" in command_list:
                return Command.GOTO
            elif "if-goto" in command_list:
                return Command.IF
            else:
                raise Exception(f"Invalid Command Type: {self.order}")
        elif command_length == 3:
            if "push" in command_list:
                return Command.PUSH
            elif "pop" in command_list:
                return Command.POP
            elif "function" in command_list:
                return Command.FUNCTION
            else:
                raise Exception(f"Invalid Command Type: {self.order}")
        else:
            raise Exception(f"Invalid Command Type: {self.order.split()}")
    
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
        self.file_name = os.path.basename(file_path).split(".")[0]
        # 出力ファイルのProg.hackを作成する
        self.asm_file_path = f"{file_path.replace('vm', 'asm')}"
        self.fp = open(self.asm_file_path, "w")

        self.jump_number = 0
        
    def set_file_name(file_name: str) -> None:
        """
        新しいVMファイルの変換が開始されたことを知らせる
        VMTranslatorによって呼び出される
        ----------
        file_name : str
            ファイル名
        """
        pass
    
    def _create_infinite_loop(self) -> None:
        self.fp.write("(END)\n")
        self.fp.write("  @END\n")
        self.fp.write("  0;JMP\n")

    def _store_data_in_stack(self) -> None:
        """
        スタックへデータを格納するヘルパー関数
        """
        self.fp.write("  @SP\n")
        self.fp.write("  A=M\n")
        self.fp.write("  M=D\n")
    
    def _get_data_from_stack(self) -> None:
        """
        スタックからデータを取得するヘルパー関数
        """
        self.fp.write("  @SP\n")
        self.fp.write("  A=M\n")
        self.fp.write("  D=M\n")

    def _increase_stack_pointer(self) -> None:
        """
        スタックポインタを1増やすヘルパー関数
        """
        self.fp.write("  @SP\n")
        self.fp.write("  M=M+1\n")

    def _decrease_stack_pointer(self) -> None:
        """
        スタックポインタを1減らすヘルパー関数
        """
        self.fp.write("  @SP\n")
        self.fp.write("  M=M-1\n")
        
    def _store_one_data_in_stack(self) -> None:
        """
        スタックへ一つデータを格納するヘルパー関数 (スタックポインタは考慮不要)
        """
        self._store_data_in_stack()
        self._increase_stack_pointer()
        
    def _get_one_arg_from_stack(self) -> None:
        """
        スタックから一つデータを取得するヘルパー関数 (スタックポインタは考慮不要)
        """
        self._decrease_stack_pointer()
        self._get_data_from_stack()

    def _get_two_args_from_stack(self) -> None:
        """
        スタックへ一つデータを格納するヘルパー関数 (スタックポインタは考慮不要)
        """
        self._get_one_arg_from_stack()
        self.fp.write("  @SP\n")
        self.fp.write("  AM=M-1\n")

    def _calculate_segment_address(self, segment: str, index: int) -> None:
        """
        セグメントのアドレスを計算する関数
        
        Parameters
        ----------
        segment : str
            LCL, ARG, THIS, THATの4種類
        index : int
            インデックス
        """
        # セグメントのベースアドレスを取得
        self.fp.write(f"  @{segment}\n")
        self.fp.write("  D=M\n")
        # idx分ずらす
        self.fp.write(f"  @{index}\n")
        self.fp.write("  D=D+A\n")
        # 一時的にTEMPへsegment+idxを保存
        self.fp.write("  @5\n")
        self.fp.write("  M=D\n")
        
    def _store_data_in_segment(self, segment: str, index: int, data: int = None) -> None:
        """
        セグメントからデータを取得し、データレジスタへ格納する関数
        インデックスにも対応

        Parameters
        ----------
        segment : str
            LCL, ARG, THIS, THATの4種類
        index : int
            インデックス
        data : int
            格納するデータ
            指定されない場合(=None)はデータレジスタの値を格納する
        """
        self._calculate_segment_address(
            segment=segment, index=index
        )
        # データを格納
        # データの指定がある場合、直前でデータレジスタにその値を格納する
        if data is not None:
            self.fp.write(f"  @{data}\n")
            self.fp.write("  D=A\n")
        self.fp.write("  @5\n")
        self.fp.write("  A=M\n")
        self.fp.write("  M=D\n")
        self._increase_stack_pointer()
        
    def _get_data_from_segment(self, segment: str, index: int) -> None:
        self._calculate_segment_address(
            segment=segment, index=index
        )
        self.fp.write("  @5\n")
        self.fp.write("  A=M\n")
        self.fp.write("  D=M\n")

    def write_arithmetic(self, command: str) -> None:
        """
        算術論理コマンドに対応するアセンブリコードを書く
        """
        if command == "add":
            self._get_two_args_from_stack()
            self.fp.write("  M=D+M\n")
            self._increase_stack_pointer()
        elif command == "sub":
            self._get_two_args_from_stack()
            self.fp.write("  M=M-D\n")
            self._increase_stack_pointer()
        elif command == "neg":
            self.fp.write("  @SP\n")
            self.fp.write("  AM=M-1\n")
            self.fp.write("  M=-M\n")
            self._increase_stack_pointer()
        elif command in ("eq", "gt", "lt"):
            self._get_two_args_from_stack()
            self.fp.write("  D=M-D\n")
            self.fp.write(f"  @true_{self.jump_number}\n")
            jump = ""
            if command == "eq":
                jump = "JEQ"
            elif command == "gt":
                jump = "JGT"
            elif command == "lt":
                jump = "JLT"
            self.fp.write(f"  D;{jump}\n")
            self.fp.write("  @SP\n")
            self.fp.write("  A=M\n")
            self.fp.write("  M=0\n")
            self.fp.write(f"  @end_{self.jump_number}\n")
            self.fp.write("  0;JMP\n")
            self.fp.write(f"(true_{self.jump_number})\n")
            self.fp.write("  @SP\n")
            self.fp.write("  A=M\n")
            self.fp.write("  M=-1\n")
            self.fp.write(f"(end_{self.jump_number})\n")
            self._increase_stack_pointer()
            self.jump_number += 1
        elif command == "and":
            self._get_two_args_from_stack()
            self.fp.write("  M=D&M\n")
            self._increase_stack_pointer()
        elif command == "or":
            self._get_two_args_from_stack()
            self.fp.write("  M=D|M\n")
            self._increase_stack_pointer()
        elif command == "not":
            self.fp.write("  @SP\n")
            self.fp.write("  AM=M-1\n")
            self.fp.write("  M=!M\n")
            self._increase_stack_pointer()
        else:
            raise Exception(f"Invalid Command: {command}")

    def write_push_pop(self, command: Command, segment: str, index: int) -> None:
        """
        PUSH, POPコマンドに対応するアセンブリコードを書く
        """
        if segment == "constant":
            self.fp.write(f"  @{index}\n")
            self.fp.write("  D=A\n")
            self._store_one_data_in_stack()
        elif segment in ("local", "argument", "this", "that", "temp"):
            if command == Command.PUSH:
                self._get_data_from_segment(
                    # segment_base=self.pointer_map[segment]["base"],
                    segment=SEGMENT_MAP[segment],
                    index=index
                )
                self._store_one_data_in_stack()
            elif command == Command.POP:
                self._get_one_arg_from_stack()
                # self._store_data_in_segment(
                #     segment_base=self.pointer_map[segment]["base"], index=index                    
                # )
                self._store_data_in_segment(
                    segment=SEGMENT_MAP[segment],
                    index=index
                )
        # elif segment in ("this", "that"):
            # self.fp.write(f"  @{SEGMENT_MAP[segment]}\n")
            # self.fp.write(f"  @{self.pointer_map[segment]['symbol']}\n")
            # self.fp.write("  D=M\n")
            # self.fp.write(f"  @{index}\n")
            # self.fp.write("  D=D+A\n")
            # 5をAレジスタへ、一時的な保存
            # self.fp.write("  @5\n")
            # self.fp.write("  M=D\n")
            # if command == Command.PUSH:
                # 5をAレジスタへ、一時的な保存
                # self.fp.write("  @5\n")
                # self.fp.write("  A=M\n")
                # self.fp.write("  D=M\n")
                # self._store_one_data_in_stack()
            # elif command == Command.POP:
                # self._get_one_arg_from_stack()
                # 5をAレジスタへ、一時的な保存
                # self.fp.write("  @5\n")
                # self.fp.write("  A=M\n")
                # self.fp.write("  M=D\n")
        elif segment == "pointer":
            seg = "THIS" if index == 0 else "THAT"
            if command == Command.PUSH:
                self.fp.write(f"  @{seg}\n")
                self.fp.write("  D=M\n")
                self._store_one_data_in_stack()
            elif command == Command.POP:
                self._get_one_arg_from_stack()
                self.fp.write(f"  @{seg}\n")
                self.fp.write("  M=D\n")
        elif segment == "static":
            if command == Command.PUSH:
                self.fp.write(f"  @{self.file_name}.{index}\n")
                self.fp.write("  D=M\n")
                self._store_one_data_in_stack()
            elif command == Command.POP:
                self._get_one_arg_from_stack()
                self.fp.write(f"  @{self.file_name}.{index}\n")
                self.fp.write("  M=D\n")

    def write_label(self, label: str) -> None:
        self.fp.write(f"({label})\n")
    
    def write_goto(self, label: str) -> None:
        self.fp.write(f"  @{label}\n")
        self.fp.write("  0;JMP\n")
    
    def write_if(self, label: str) -> None:
        self._get_one_arg_from_stack()
        self.fp.write(f"  @{label}\n")
        self.fp.write("  D;JGT\n")
    
    def write_function(self, function_name: str, n_vars: int) -> None:
        """
        関数fを宣言し、関数がn_vars個のローカル変数を持つことを知らせる

        Parameters
        ----------
        function_name : str
            関数名
        n_vars : int
            ローカル変数の数
            この数だけスタックを0で初期化する
        """
        for i in range(n_vars):
            self._store_data_in_segment(
                segment=SEGMENT_MAP["local"],
                index=i,
                data=0
            )
    
    def write_call(self, function_name: str, n_args: int) -> None:
        """_summary_

        Parameters
        ----------
        function_name : str
            _description_
        n_args : int
            _description_
        """
        pass
    
    def write_return(self, function_name: str) -> None:
        """
        現在の関数を終了し、呼び出し側に制御を返す

        Parameters
        ----------
        function_name : str
            関数名
        """
        # fname = LCL
        self.fp.write("  @LCL\n")
        self.fp.write("  D=M\n")
        # self.fp.write("  D=M\n")
        self.fp.write("  @13\n")
        self.fp.write("  M=D\n")
        # retAddr = *(fname-5)
        self.fp.write("  @LCL\n")
        self.fp.write("  D=M\n")
        self.fp.write("  @5\n")
        self.fp.write("  D=D-A\n")
        self.fp.write("  A=D\n")
        self.fp.write("  D=M\n")
        self.fp.write("  @14\n")
        self.fp.write("  M=D\n")
        # *ARG = pop()
        self._get_one_arg_from_stack()
        self.fp.write("  @ARG\n")
        self.fp.write("  A=M\n")
        self.fp.write("  M=D\n")
        # SP = ARG + 1
        self.fp.write("  @ARG\n")
        self.fp.write("  D=M+1\n")
        self.fp.write("  @SP\n")
        self.fp.write("  M=D\n")
        # THAT = *(fname-1)
        self.fp.write("  @13\n")
        self.fp.write("  D=M\n")
        self.fp.write("  @1\n")
        self.fp.write("  A=D-A\n")
        self.fp.write("  D=M\n")
        self.fp.write("  @THAT\n")
        self.fp.write("  M=D\n")
        # THIS = *(fname-2)
        self.fp.write("  @13\n")
        self.fp.write("  D=M\n")
        self.fp.write("  @2\n")
        self.fp.write("  A=D-A\n")
        self.fp.write("  D=M\n")
        self.fp.write("  @THIS\n")
        self.fp.write("  M=D\n")
        # ARG = *(fname-3)
        self.fp.write("  @13\n")
        self.fp.write("  D=M\n")
        self.fp.write("  @3\n")
        self.fp.write("  A=D-A\n")
        self.fp.write("  D=M\n")
        self.fp.write("  @ARG\n")
        self.fp.write("  M=D\n")
        # LCL = *(fname-4)
        self.fp.write("  @13\n")
        self.fp.write("  D=M\n")
        self.fp.write("  @4\n")
        self.fp.write("  A=D-A\n")
        self.fp.write("  D=M\n")
        self.fp.write("  @LCL\n")
        self.fp.write("  M=D\n")
        # goto retAddr
        self.fp.write("  @14\n")
        self.fp.write("  A=M\n")
        self.fp.write("  0;JMP\n")

    def close(self) -> None:
        """
        出力ファイル/ストリームを閉じる
        """
        self._create_infinite_loop()
        self.fp.close()


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

            self.code_writer.fp.write(f"  // {self.parser.order}\n")
            command_type = self.parser.commnad_type()
            if command_type == Command.ARITHMETIC:
                self.code_writer.write_arithmetic(command=self.parser.order)
            elif command_type == Command.PUSH or command_type == Command.POP:
                self.code_writer.write_push_pop(
                    command=self.parser.commnad_type(),
                    segment=self.parser.arg1(),
                    index=self.parser.arg2()
                )
            elif command_type == Command.LABEL:
                self.code_writer.write_label(label=self.parser.order.split()[-1])
            elif command_type == Command.GOTO:
                self.code_writer.write_goto(label=self.parser.order.split()[-1])
            elif command_type == Command.IF:
                self.code_writer.write_if(label=self.parser.order.split()[-1])
            elif command_type == Command.FUNCTION:
                self.function_name = self.parser.arg1()
                self.n_args = self.parser.arg2()
                self.n_vars = self.parser.arg2()
                self.code_writer.write_function(
                    function_name=self.function_name,
                    n_vars=self.parser.arg2()
                )
            elif command_type == Command.RETURN:
                self.code_writer.write_return(function_name=self.function_name)
            elif command_type == Command.CALL:
                self.code_writer.write_call(
                    function_name=self.function_name,
                    n_vars=self.n_vars
                )
            else:
                print(self.parser.order, command_type)
        self.code_writer.close()
            
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