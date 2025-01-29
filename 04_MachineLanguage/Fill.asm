// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

(ON)
    @KBD
    D=M
    @OFF
    D;JEQ
    @DRAW
    0;JMP
(OFF)
    @KBD
    D=M
    @ON
    D;JNE
    @CLEAR
    0;JMP
(DRAW)
    @SCREEN
    M=-1
    A=A+1
    M=-1
    A=A+1
    M=-1
    A=A+1
    M=-1
    A=A+1
    M=-1
    @ON
    0;JMP
(CLEAR)
    @SCREEN
    M=0
    A=A+1
    M=0
    A=A+1
    M=0
    A=A+1
    M=0
    A=A+1
    M=0
    @OFF
    0;JMP