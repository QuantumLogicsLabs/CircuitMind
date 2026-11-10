`timescale 1ns / 1ps
//=============================================================================
// fp_add - IEEE-754 binary32 addition / subtraction
//
// sub = 1 computes a - b by flipping b's sign before the datapath.  This is
// the integration-lead addition path: exponent comparison, mantissa
// alignment, the significand addition circuit, and normalization/rounding,
// with IEEE special-case control (NaN, infinity, signed zero) on top.
//
// Rounding mode: round-to-nearest, ties-to-even only.
//=============================================================================
module fp_add (
    input  wire [31:0] a,
    input  wire [31:0] b,
    input  wire        sub,
    output reg  [31:0] result,
    output reg         invalid,
    output reg         overflow,
    output reg         underflow,
    output reg         inexact
);

    wire        sa = a[31];
    wire [7:0]  ea = a[30:23];
    wire [22:0] fa = a[22:0];

    wire        sb = b[31] ^ sub;
    wire [7:0]  eb = b[30:23];
    wire [22:0] fb = b[22:0];

    wire        nan_a = (ea == 8'hFF) && (fa != 23'd0);
    wire        nan_b = (eb == 8'hFF) && (fb != 23'd0);
    wire        snan_a = nan_a && !fa[22];
    wire        snan_b = nan_b && !fb[22];
    wire        inf_a = (ea == 8'hFF) && (fa == 23'd0);
    wire        inf_b = (eb == 8'hFF) && (fb == 23'd0);
    wire        zero_a = (ea == 8'd0) && (fa == 23'd0);
    wire        zero_b = (eb == 8'd0) && (fb == 23'd0);

    //-------------------------------------------------------------------------
    // Magnitude comparison and operand ordering
    //-------------------------------------------------------------------------
    wire        a_ge_b;
    wire        mag_equal;
    wire [7:0]  exp_diff;

    fp_compare_mag u_cmp (
        .exp_a    (ea),
        .frac_a   (fa),
        .exp_b    (eb),
        .frac_b   (fb),
        .a_ge_b   (a_ge_b),
        .mag_equal(mag_equal),
        .exp_diff (exp_diff)
    );

    wire [7:0]  eff_exp_a = (ea == 8'd0) ? 8'd1 : ea;
    wire [7:0]  eff_exp_b = (eb == 8'd0) ? 8'd1 : eb;

    wire [7:0]  exp_l  = a_ge_b ? eff_exp_a : eff_exp_b;
    wire [23:0] mant_l = a_ge_b ? {(ea != 8'd0), fa} : {(eb != 8'd0), fb};
    wire [23:0] mant_s = a_ge_b ? {(eb != 8'd0), fb} : {(ea != 8'd0), fa};
    wire        sign_l = a_ge_b ? sa : sb;

    //-------------------------------------------------------------------------
    // Mantissa alignment
    //-------------------------------------------------------------------------
    wire [26:0] aligned_s;
    wire        sticky_s;

    fp_align u_align (
        .mant   (mant_s),
        .shift  (exp_diff),
        .aligned(aligned_s),
        .sticky (sticky_s)
    );

    //-------------------------------------------------------------------------
    // Addition circuit
    //-------------------------------------------------------------------------
    wire [27:0] sum;

    fp_addsub_core u_core (
        .mant_a  ({mant_l, 3'b000}),
        .mant_b  (aligned_s),
        .do_sub  (sa != sb),
        .sticky_b(sticky_s),
        .sum     (sum)
    );

    //-------------------------------------------------------------------------
    // Normalization and rounding
    //-------------------------------------------------------------------------
    wire [31:0] alu_result;
    wire        alu_ovf;
    wire        alu_unf;
    wire        alu_inx;
    wire        alu_zero;

    fp_normalize u_norm (
        .sum       (sum),
        .sticky_in (sticky_s),
        .exp_in    (exp_l),
        .sign_in   (sign_l),
        .result    (alu_result),
        .inexact   (alu_inx),
        .overflow  (alu_ovf),
        .underflow (alu_unf),
        .is_zero   (alu_zero)
    );

    //-------------------------------------------------------------------------
    // Control logic: special cases take priority over the datapath
    //-------------------------------------------------------------------------
    always @(*) begin
        result    = 32'h7FC00000;   // canonical quiet NaN
        invalid   = 1'b0;
        overflow  = 1'b0;
        underflow = 1'b0;
        inexact   = 1'b0;

        if (nan_a || nan_b) begin
            result  = 32'h7FC00000;
            invalid = snan_a | snan_b;
        end else if (inf_a && inf_b) begin
            if (sa != sb) begin
                result  = 32'h7FC00000;
                invalid = 1'b1;
            end else begin
                result = {sa, 8'hFF, 23'd0};
            end
        end else if (inf_a) begin
            result = {sa, 8'hFF, 23'd0};
        end else if (inf_b) begin
            result = {sb, 8'hFF, 23'd0};
        end else if (zero_a && zero_b) begin
            // -0 + -0 = -0; every other zero combination is +0.
            result = {sa & sb, 31'd0};
        end else if (zero_a) begin
            result = {sb, b[30:0]};
        end else if (zero_b) begin
            result = {sa, a[30:0]};
        end else begin
            result    = alu_result;
            overflow  = alu_ovf;
            underflow = alu_unf;
            inexact   = alu_inx;

            if (alu_zero) begin
                result = 32'd0;     // exact cancellation produces +0
            end
        end
    end

endmodule
