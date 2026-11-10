`timescale 1ns / 1ps
//=============================================================================
// fp_div_stub - replace with Member 2's division module
//
// Same port list as the real module so fpu_top elaborates and the integration
// path can be simulated today.  stub_active marks the result as unimplemented.
// Contract for the real module:
//   result = a / b (binary32, round-to-nearest-even), flags per IEEE-754,
//   including divide-by-zero once that flag exists on the integrated FPU.
//=============================================================================
module fp_div_stub (
    input  wire [31:0] a,
    input  wire [31:0] b,
    output wire [31:0] result,
    output wire        invalid,
    output wire        overflow,
    output wire        underflow,
    output wire        inexact,
    output wire        stub_active
);

    assign result      = 32'h7FC00000;
    assign invalid     = 1'b0;
    assign overflow    = 1'b0;
    assign underflow   = 1'b0;
    assign inexact     = 1'b0;
    assign stub_active = 1'b1;

endmodule
