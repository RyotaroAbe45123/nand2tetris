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
        self.order = self.order.replace(" ", "")
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
        if self.instruction_type() == Instruction.L:
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
    
    
class SymbolTable:
    def __init__(self):
        self.table = {}
        self.table["R0"] = 0
        self.table["R1"] = 1
        self.table["R2"] = 2
        self.table["R3"] = 3
        self.table["R4"] = 4
        self.table["R5"] = 5
        self.table["R6"] = 6
        self.table["R7"] = 7
        self.table["R8"] = 8
        self.table["R9"] = 9
        self.table["R10"] = 10
        self.table["R11"] = 11
        self.table["R12"] = 12
        self.table["R13"] = 13
        self.table["R14"] = 14
        self.table["R15"] = 15
        self.table["SP"] = 0
        self.table["LCL"] = 1
        self.table["ARG"] = 2
        self.table["THIS"] = 3
        self.table["THAT"] = 4
        self.table["SCREEN"] = 16384
        self.table["KBD"] = 24576
        
    def addEntry(self, symbol: str, address: int):
        self.table[symbol] = address
    
    def contains(self, symbol: str) -> bool:
        return True if symbol in self.table else False
    
    def getAddress(self, symbol: str) -> int:
        return self.table[symbol]


class Hack:
    def __init__(self, asm_file_name: str) -> None:
        self.asm_file_path = f"./{asm_file_name}"
        self.parser = Parser(asm_file_path=self.asm_file_path)
        self.symbol_table = SymbolTable()
        # 出力ファイルのProg.hackを作成する
        self.hack_file_path = f"./{asm_file_name.replace('asm', 'hack')}"
        with open(self.hack_file_path, "w") as fp:
            fp.write("")

        self.val_address = 16

    def do_binary_conversion(self) -> None:
        """
        第1パスでシンボルテーブルを作成
        第2パスでバイナリコードへ変換
        """
        self.create_symbol_table()
        self.convert_asm_to_hack()
        
    def create_symbol_table(self) -> None:
        """
        第1パスで用いられる。ここでは、すべてのラベルシンボルがテーブルへ追加される。
        変数シンボルについては、第2パスで追加される。
        """
        # ラベル宣言を格納するための行番号記録用
        line_number = 0
        tmp_parser = Parser(asm_file_path=self.asm_file_path)
        # tmp_parserを用いて、命令を一周し、シンボルテーブルを作成する
        while tmp_parser.has_more_lines():
            tmp_parser.advance()
            if tmp_parser.order is None:
                continue
            if tmp_parser.instruction_type() == Instruction.L:
                symbol = tmp_parser.symbol()
                self.symbol_table.addEntry(symbol=symbol, address=line_number)
                continue
            line_number += 1
        del tmp_parser

    def convert_asm_to_hack(self) -> None:
        # 各行(アセンブリ命令)を反復処理する
        # C命令については、各フィールドをバイナリーコードに変換して、連結する
        # A命令については、xxxをバイナリーコードに変換する
        # 変数シンボル参照をもつA命令については、シンボルテーブルでシンボルを検索し、なければ追加する。
        # 変数シンボルを格納するためのRAM番号記録用(val_number>=16)
        val_number = 16
        
        while self.parser.has_more_lines():
            self.parser.advance()
            if self.parser.order is None:
                continue

            binary_code = ""
            if self.parser.instruction_type() == Instruction.A:
                symbol = self.parser.symbol()
                # A命令のxxxが整数かどうかで変数シンボルかを判定する
                # symbol_is_intがFalseならば、変数シンボル
                symbol_is_int = symbol.isdigit()
                if symbol_is_int:
                    symbol_int = int(symbol)
                else:
                    # 変数シンボルの場合
                    if self.symbol_table.contains(symbol=symbol):
                        address = self.symbol_table.getAddress(symbol=symbol)
                        symbol_int = int(address)
                    else:
                        # self.val_address += 1
                        self.symbol_table.addEntry(symbol=symbol, address=val_number)
                        symbol_int = int(val_number)
                        val_number += 1
                # 0埋めの16bitバイナリへ変換
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
            elif self.parser.instruction_type() == Instruction.L:
                # 何もせず書き込まない
                continue

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