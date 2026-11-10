`timescale 1ns / 1ps
//=============================================================================
// fpu_top - integrated 32-bit IEEE-754 floating-point unit
//
//   op = 00 : ADD   (fp_add, sub = 0)
//   op = 01 : SUB   (fp_add, sub = 1)
//   op = 10 : MUL   (fp_mul_stub until Member 2's module lands)
//   op = 11 : DIV   (fp_div_stub until Member 2's module lands)
//
// Combinational, single-cycle.  The stub sockets keep the integration path
// simulatable; stub_active is asserted whenever a stubbed op produced the
// result, so tests and callers can never mistake it for a real product.
//=============================================================================
module fpu_top (
    input  wire [1:0]  op,
    input  wire [31:0] a,
    input  wire [31:0] b,
    output reg  [31:0] result,
    output reg         invalid,
    output reg         overflow,
    output reg         underflow,
    output reg         inexact,
    output reg         stub_active
);

    wire addsub_en;
    wire sub_sel;
    wire mul_en;
    wire div_en;

    fpu_control u_ctl (
        .op       (op),
        .addsub_en(addsub_en),
        .sub_sel  (sub_sel),
        .mul_en   (mul_en),
        .div_en   (div_en)
    );

    wire [31:0] add_result;
    wire        add_inv;
    wire        add_ovf;
    wire        add_unf;
    wire        add_inx;

    fp_add u_add (
        .a        (a),
        .b        (b),
        .sub      (sub_sel),
        .result   (add_result),
        .invalid  (add_inv),
        .overflow (add_ovf),
        .underflow(add_unf),
        .inexact  (add_inx)
    );

    wire [31:0] mul_result;
    wire        mul_inv;
    wire        mul_ovf;
    wire        mul_unf;
    wire        mul_inx;
    wire        mul_stub;

    fp_mul_stub u_mul (
        .a          (a),
        .b          (b),
        .result     (mul_result),
        .invalid    (mul_inv),
        .overflow   (mul_ovf),
        .underflow  (mul_unf),
        .inexact    (mul_inx),
        .stub_active(mul_stub)
    );

    wire [31:0] div_result;
    wire        div_inv;
    wire        div_ovf;
    wire        div_unf;
    wire        div_inx;
    wire        div_stub;

    fp_div_stub u_div (
        .a          (a),
        .b          (b),
        .result     (div_result),
        .invalid    (div_inv),
        .overflow   (div_ovf),
        .underflow  (div_unf),
        .inexact    (div_inx),
        .stub_active(div_stub)
    );

    always @(*) begin
        result    = 32'd0;
        invalid   = 1'b0;
        overflow  = 1'b0;
        underflow = 1'b0;
        inexact   = 1'b0;
        stub_active = 1'b0;

        if (addsub_en) begin
            result    = add_result;
            invalid   = add_inv;
            overflow  = add_ovf;
            underflow = add_unf;
            inexact   = add_inx;
        end else if (mul_en) begin
            result      = mul_result;
            invalid     = mul_inv;
            overflow    = mul_ovf;
            underflow   = mul_unf;
            inexact     = mul_inx;
            stub_active = mul_stub;
        end else begin
            result      = div_result;
            invalid     = div_inv;
            overflow    = div_ovf;
            underflow   = div_unf;
            inexact     = div_inx;
            stub_active = div_stub;
        end
    end

endmodule
