`timescale 1ns / 1ps
//=============================================================================
// fpu_control - operation decode for the integrated FPU
//
//   op = 00 : ADD
//   op = 01 : SUB
//   op = 10 : MUL (module supplied by Member 2)
//   op = 11 : DIV (module supplied by Member 2)
//=============================================================================
module fpu_control (
    input  wire [1:0] op,
    output wire       addsub_en,
    output wire       sub_sel,
    output wire       mul_en,
    output wire       div_en
);

    assign addsub_en = (op == 2'b00) || (op == 2'b01);
    assign sub_sel   = (op == 2'b01);
    assign mul_en    = (op == 2'b10);
    assign div_en    = (op == 2'b11);

endmodule
