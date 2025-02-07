from enum import Enum
import sys


class Instruction(Enum):
    # Aは@xxx
    A = "A_INSTRUCTION"
    # Cはdest=comp;jump
    C = "C_INSTRUCTION"
    # Lは(シンボル)
    L = "L_INSTRUCTION"


class Parser:
    def __init__(self, asm_file_path: str) -> None:
        """
        入力ファイルを受け付ける
        """
        with open(asm_file_path, "r") as fp:
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
    
    def instruction_type(self) -> Instruction:
        """
        現在の命令のタイプを返す
        """
        if self.order.startswith("@"):
            return Instruction.A
        elif self.order.startswith("(") and self.order.endswith(")"):
            return Instruction.L
        else:
            return Instruction.C
    
    def symbol(self) -> str:
        """
        現在の命令に、シンボルが含まれる場合は、シンボルを
        そうでない場合は、10進数を文字列で返す
        """
        if self.instruction_type == Instruction.L:
            return self.order[1:-1]
        else:
            return self.order[1:]
    
    def dest(self) -> str:
        """
        現在のC命令のdestを返す
        """
        if "=" in self.order:
            return self.order.split("=")[0]
        else:
            return "null"
    
    def comp(self) -> str:
        """
        現在のC命令のcompを返す
        """
        if "=" in self.order and ";" in self.order:
            return self.order.split("=")[-1].split(";")[0]
        elif "=" in self.order:
            return self.order.split("=")[-1]
        elif ";" in self.order:
            return self.order.split(";")[0]

    def jump(self) -> str:
        """
        現在のC命令のjumpを返す
        """
        if ";" in self.order:
            return self.order.split(";")[-1]
        else:
            return "null"


class Code:
    @classmethod
    def dest(self, arg: str) -> str:
        """
        destニーモニックのバイナリーコード(3ビット)を返す
        """
        is_m_in_dest = "1" if "M" in arg else "0"
        is_d_in_dest = "1" if "D" in arg else "0"
        is_a_in_dest = "1" if "A" in arg else "0"
        return is_a_in_dest + is_d_in_dest + is_m_in_dest

    @classmethod
    def comp(self, arg: str) -> str:
        """
        compニーモニックのバイナリーコード(7ビット)を返す
        """
        unified_arg = arg.replace("M", "A")
        comp_map = {
            "0": "101010",
            "1": "111111",
            "-1": "111010",
            "D": "001100",
            "A": "110000",
            "!D": "001101",
            "!A": "110001",
            "-D": "001111",
            "-A": "110011",
            "D+1": "011111",
            "A+1": "110111",
            "D-1": "001110",
            "A-1": "110010",
            "D+A": "000010",
            "D-A": "010011",
            "A-D": "000111",
            "D&A": "000000",
            "D|A": "010101",
        }
        return comp_map[unified_arg]    

    @classmethod
    def jump(self, arg: str) -> str:
        """
        jumpニーモニックのバイナリーコード(3ビット)を返す
        """
        jump_map = {
            "null": "000",
            "JGT": "001",
            "JEQ": "010",
            "JGE": "011",
            "JLT": "100",
            "JNE": "101",
            "JLE": "110",
            "JMP": "111",
        }
        return jump_map[arg]


class Hack:
    def __init__(self, asm_file_name: str) -> None:
        self.asm_file_path = f"./{asm_file_name}"
        self.parser = Parser(asm_file_path=self.asm_file_path)
        # 出力ファイルのProg.hackを作成する
        self.hack_file_path = f"./{asm_file_name.replace('asm', 'hack')}"
        with open(self.hack_file_path, "w") as fp:
            fp.write("")
            
    def do_binary_conversion(self) -> None:
        """
        バイナリーコードへ変換
        """
        self.convert_asm_to_hack()

    def convert_asm_to_hack(self) -> None:
        # 各行(アセンブリ命令)を反復処理する
        # C命令については、各フィールドをバイナリーコードに変換して、連結する
        # A命令については、xxxをバイナリーコードに変換する
        while self.parser.has_more_lines():
            self.parser.advance()
            if self.parser.order is None:
                continue

            binary_code = ""
            if self.parser.instruction_type() == Instruction.A:
                symbol_int = int(self.parser.symbol())
                binary_16bit_str = f"{symbol_int:016b}"
                binary_code += binary_16bit_str
            elif self.parser.instruction_type() == Instruction.C:
                dest_asm = self.parser.dest()
                comp_asm = self.parser.comp()
                jump_asm = self.parser.jump()
                
                dest_binary = Code.dest(dest_asm)
                comp_binary = Code.comp(comp_asm)
                jump_binary = Code.jump(jump_asm)
                
                binary_code += "111"
                is_a = "1" if "M" in comp_asm else "0"
                binary_code += is_a
                binary_code += comp_binary
                binary_code += dest_binary
                binary_code += jump_binary
            # elif parser.instruction_type() == Instruction.L:
            #     pass

            with open(self.hack_file_path, "a") as fp:
                fp.write(binary_code)
                fp.write("\n")


def main():
    # コマンドライン引数で入力ファイルの名前を受け取る
    args = sys.argv
    if len(args) < 2:
        print("ファイル名を入力してください。")
        return
    asm_file_name = args[1]

    hack = Hack(asm_file_name=asm_file_name)
    # asmファイルをhackファイルへ (アセンブリ2バイナリ)
    hack.do_binary_conversion()


if __name__ == "__main__":
    main()