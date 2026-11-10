`timescale 1ns / 1ps
//=============================================================================
// fp_addsub_core - significand addition circuit
//
// |A| >= |B| is guaranteed by fp_add.  For subtraction the aligned B has been
// truncated and its remainder is flagged by sticky_b; the true difference is
// therefore (A - B_trunc) - f with 0 < f < 1, so one extra LSB is subtracted.
// The fractional remainder stays represented by the sticky flag that
// fp_normalize receives.
//=============================================================================
module fp_addsub_core (
    input  wire [26:0] mant_a,    // larger magnitude, {mant24, 3'b000}
    input  wire [26:0] mant_b,    // smaller magnitude, aligned
    input  wire        do_sub,
    input  wire        sticky_b,
    output wire [27:0] sum
);

    wire [27:0] a_ext = {1'b0, mant_a};
    wire [27:0] b_ext = {1'b0, mant_b};

    reg  [27:0] diff;

    always @(*) begin
        if (do_sub)
            diff = a_ext - b_ext - (sticky_b ? 28'd1 : 28'd0);
        else
            diff = a_ext + b_ext;
    end

    assign sum = diff;

endmodule
