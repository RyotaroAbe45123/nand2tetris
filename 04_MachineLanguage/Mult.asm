// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
// The algorithm is based on repetitive addition.
    // result, loop_counterのようなシンボルは適当な数字に置き換えられるので気にしなくて良い。
    @result
    M=0
    @loop_counter
    M=0
    // R2が0になっていることを保証する
    @R2
    M=0
(LOOP)
    // R1の値をデータレジスタに書き込む
    @R1
    D=M
    // loop_counterの値を読み取り、上記から引き算することで、残りの回数を計算する。それをデータレジスタに書き込む。
    @loop_counter
    D=D-M
    // データレジスタの値が0以下ならLOOP_ENDへジャンプ
    @LOOP_END
    D;JLE
    // R0をR1個足すことで掛け算を実現
    @R0
    D=M
    // resultにR0を足す
    @result
    M=M+D
    // loop_counterに1を足す
    @loop_counter
    M=M+1
    // ループへ戻る
    @LOOP
    0;JMP
(LOOP_END)
    @result
    D=M
    @R2
    M=D