`timescale 1ns / 1ps
//=============================================================================
// tb_fp_add - self-checking testbench for the addition/subtraction path
//
// Reads vectors produced by scripts/gen_vectors.py.  Each vector carries the
// expected 32-bit result and the four IEEE exception flags.
//=============================================================================
module tb_fp_add;

    reg  [31:0] a;
    reg  [31:0] b;
    reg         sub;

    wire [31:0] result;
    wire        invalid;
    wire        overflow;
    wire        underflow;
    wire        inexact;
    wire [3:0]  got_flags = {invalid, overflow, underflow, inexact};

    integer total;
    integer errors;

    fp_add dut (
        .a        (a),
        .b        (b),
        .sub      (sub),
        .result   (result),
        .invalid  (invalid),
        .overflow (overflow),
        .underflow(underflow),
        .inexact  (inexact)
    );

    task run_vectors;
        input [8*32-1:0] fname;
        input            sub_mode;
        integer fd;
        integer rc;
        reg [31:0] va;
        reg [31:0] vb;
        reg [31:0] vy;
        reg [3:0]  vf;
        begin
            fd = $fopen(fname, "r");
            if (fd == 0) begin
                $display("TB_FP_ADD: ERROR cannot open %0s", fname);
                errors = errors + 1;
            end else begin
                while (!$feof(fd)) begin
                    rc = $fscanf(fd, "%h %h %h %h", va, vb, vy, vf);
                    if (rc == 4) begin
                        a   = va;
                        b   = vb;
                        sub = sub_mode;
                        #1;
                        total = total + 1;
                        if ((result !== vy) || (got_flags !== vf)) begin
                            errors = errors + 1;
                            if (errors <= 20)
                                $display("MISMATCH a=%08x b=%08x sub=%0d got=%08x flags=%b exp=%08x flags=%b",
                                         a, b, sub, result, got_flags, vy, vf);
                        end
                    end
                end
                $fclose(fd);
            end
        end
    endtask

    initial begin
        total  = 0;
        errors = 0;
        a = 32'd0;
        b = 32'd0;
        sub = 1'b0;

        run_vectors("add_vectors.txt", 1'b0);
        run_vectors("sub_vectors.txt", 1'b1);

        if (errors == 0)
            $display("RESULT: PASS (%0d vectors)", total);
        else
            $display("RESULT: FAIL (%0d errors in %0d vectors)", errors, total);

        $finish;
    end

endmodule
