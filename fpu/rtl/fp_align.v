`timescale 1ns / 1ps
//=============================================================================
// fp_align - mantissa alignment for IEEE-754 binary32 addition
//
// The significand is presented in a 27-bit fixed-point field with three
// fractional bits: {mant[23:0], guard, round, lsb}.  Aligning shifts the
// significand right and reports, separately, whether any nonzero bit fell
// below the LSB.  The sticky bit is kept out of the arithmetic value so that
// the exact sum/difference can be formed in fp_addsub_core and rounded once
// in fp_normalize.
//=============================================================================
module fp_align (
    input  wire [23:0] mant,
    input  wire [7:0]  shift,
    output wire [26:0] aligned,
    output wire        sticky
);

    wire [26:0] base = {mant, 3'b000};

    reg  [26:0] shifted;
    reg         st;

    always @(*) begin
        if (shift >= 8'd27) begin
            // Everything falls below the LSB; only the sticky bit survives.
            shifted = 27'd0;
            st      = |base;
        end else begin
            shifted = base >> shift;
            st      = |(base & ((27'd1 << shift) - 27'd1));
        end
    end

    assign aligned = shifted;
    assign sticky  = st;

endmodule
