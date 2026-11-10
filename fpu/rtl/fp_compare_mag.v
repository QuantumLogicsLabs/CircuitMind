`timescale 1ns / 1ps
//=============================================================================
// fp_compare_mag - exponent comparison for IEEE-754 binary32
//
// Subnormals share exponent field 0 but belong to the 2^-126 binade, so they
// are compared with effective exponent 1 and an implicit leading 0.  The
// returned exp_diff is always (larger exp - smaller exp), independent of the
// input ordering.
//=============================================================================
module fp_compare_mag (
    input  wire [7:0]  exp_a,
    input  wire [22:0] frac_a,
    input  wire [7:0]  exp_b,
    input  wire [22:0] frac_b,
    output wire        a_ge_b,
    output wire        mag_equal,
    output wire [7:0]  exp_diff
);

    wire [7:0]  eff_exp_a = (exp_a == 8'd0) ? 8'd1 : exp_a;
    wire [7:0]  eff_exp_b = (exp_b == 8'd0) ? 8'd1 : exp_b;
    wire [23:0] mant_a    = {(exp_a != 8'd0), frac_a};
    wire [23:0] mant_b    = {(exp_b != 8'd0), frac_b};
    wire [31:0] mag_a     = {eff_exp_a, mant_a};
    wire [31:0] mag_b     = {eff_exp_b, mant_b};

    assign a_ge_b    = (mag_a >= mag_b);
    assign mag_equal = (mag_a == mag_b);
    assign exp_diff  = a_ge_b ? (eff_exp_a - eff_exp_b)
                              : (eff_exp_b - eff_exp_a);

endmodule
