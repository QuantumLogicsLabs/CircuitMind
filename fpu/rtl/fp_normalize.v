`timescale 1ns / 1ps
//=============================================================================
// fp_normalize - normalization and round-to-nearest-even for binary32
//
// Input is the 28-bit significand produced by fp_addsub_core:
//   sum[26:3] = 24-bit significand (hidden bit included)
//   sum[2]    = guard, sum[1] = round, sum[0] = integer LSB
// plus a separate sticky bit for everything below sum[0].
//
// No clock: the whole FPU is a combinational single-cycle design.
//=============================================================================
module fp_normalize (
    input  wire [27:0] sum,
    input  wire        sticky_in,
    input  wire [7:0]  exp_in,
    input  wire        sign_in,
    output reg  [31:0] result,
    output reg         inexact,
    output reg         overflow,
    output reg         underflow,
    output reg         is_zero
);

    reg [25:0] mant;      // {significand[23:0], guard, round}
    reg        sticky;    // bits below the round bit
    reg [7:0]  exp;
    reg [4:0]  z;
    reg        rnd_up;
    reg [24:0] rounded;
    reg [7:0]  field;
    reg [22:0] frac;

    function [4:0] leading_zeros;
        input [25:0] v;
        integer i;
        reg seen;
        begin
            leading_zeros = 5'd0;
            seen = 1'b0;
            for (i = 25; i >= 0; i = i - 1) begin
                if (!seen && !v[i])
                    leading_zeros = leading_zeros + 5'd1;
                else
                    seen = 1'b1;
            end
        end
    endfunction

    always @(*) begin
        mant     = sum[26:1];
        sticky   = sticky_in | sum[0];
        exp      = exp_in;
        rnd_up   = 1'b0;
        rounded  = 25'd0;
        field    = 8'd0;
        frac     = 23'd0;
        inexact  = 1'b0;
        overflow = 1'b0;
        underflow = 1'b0;
        is_zero  = 1'b0;

        if (sum == 28'd0) begin
            // Exact cancellation: fp_add forces the +0 sign.
            is_zero = 1'b1;
        end else begin
            // Carry out of the significand add: renormalize once.  The carry
            // becomes the new hidden bit.
            if (sum[27]) begin
                sticky = sticky | mant[0];
                mant   = {1'b1, mant[25:1]};
                exp    = exp + 8'd1;
            end

            if (mant == 26'd0) begin
                // Only sub-LSB information is left; rounds to zero.
                is_zero   = 1'b1;
                inexact   = sticky;
                underflow = sticky;
            end else begin
                z = leading_zeros(mant);

                if (z != 5'd0) begin
                    if (exp > z) begin
                        mant = mant << z;
                        exp  = exp - z;
                    end else begin
                        // Clamp at the subnormal boundary; remaining leading
                        // zeros stay in the fraction (exponent field 0).
                        mant = mant << (exp - 8'd1);
                        exp  = 8'd1;
                    end
                end

                // Round to nearest, ties to even.
                rnd_up  = mant[1] & (mant[0] | sticky | mant[2]);
                inexact = |{mant[1:0], sticky};
                rounded = {1'b0, mant[25:2]} + (rnd_up ? 25'd1 : 25'd0);

                if (exp == 8'd255) begin
                    // Exponent already exceeded the finite range.
                    field    = 8'd255;
                    frac     = 23'd0;
                    overflow = 1'b1;
                    inexact  = 1'b1;
                end else if (rounded[24]) begin
                    // Mantissa carried after rounding: 1.0 * 2^(exp+1).
                    if (exp == 8'd254) begin
                        field    = 8'd255;
                        frac     = 23'd0;
                        overflow = 1'b1;
                        inexact  = 1'b1;
                    end else begin
                        field = exp + 8'd1;
                        frac  = 23'd0;
                    end
                end else if (rounded[23]) begin
                    field = exp;
                    frac  = rounded[22:0];
                end else begin
                    // exp == 1 with a zero hidden bit is a subnormal result.
                    field = 8'd0;
                    frac  = rounded[22:0];
                end

                underflow = (field == 8'd0) && inexact;
            end
        end

        result = {sign_in, field, frac};
    end

endmodule
