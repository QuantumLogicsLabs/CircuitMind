`timescale 1ns / 1ps
//=============================================================================
// tb_fpu_top - integration test for the top-level FPU
//
// Runs the add/sub vectors through fpu_top's op decode, then checks that the
// MUL/DIV sockets are wired and flagged as stubs (stub_active = 1).
//=============================================================================
module tb_fpu_top;

    reg  [1:0]  op;
    reg  [31:0] a;
    reg  [31:0] b;

    wire [31:0] result;
    wire        invalid;
    wire        overflow;
    wire        underflow;
    wire        inexact;
    wire        stub_active;
    wire [3:0]  got_flags = {invalid, overflow, underflow, inexact};

    integer total;
    integer errors;

    fpu_top dut (
        .op         (op),
        .a          (a),
        .b          (b),
        .result     (result),
        .invalid    (invalid),
        .overflow   (overflow),
        .underflow  (underflow),
        .inexact    (inexact),
        .stub_active(stub_active)
    );

    task run_vectors;
        input [8*32-1:0] fname;
        input [1:0]      op_mode;
        integer fd;
        integer rc;
        reg [31:0] va;
        reg [31:0] vb;
        reg [31:0] vy;
        reg [3:0]  vf;
        begin
            fd = $fopen(fname, "r");
            if (fd == 0) begin
                $display("TB_FPU_TOP: ERROR cannot open %0s", fname);
                errors = errors + 1;
            end else begin
                while (!$feof(fd)) begin
                    rc = $fscanf(fd, "%h %h %h %h", va, vb, vy, vf);
                    if (rc == 4) begin
                        op = op_mode;
                        a  = va;
                        b  = vb;
                        #1;
                        total = total + 1;
                        if ((result !== vy) || (got_flags !== vf) || stub_active) begin
                            errors = errors + 1;
                            if (errors <= 20)
                                $display("MISMATCH op=%b a=%08x b=%08x got=%08x flags=%b stub=%b exp=%08x flags=%b",
                                         op, a, b, result, got_flags, stub_active, vy, vf);
                        end
                    end
                end
                $fclose(fd);
            end
        end
    endtask

    task check_stub;
        input [1:0] op_mode;
        begin
            op = op_mode;
            a  = 32'h3F800000;
            b  = 32'h40000000;
            #1;
            total = total + 1;
            if ((result !== 32'h7FC00000) || (stub_active !== 1'b1) ||
                (got_flags !== 4'b0000)) begin
                errors = errors + 1;
                $display("STUB MISMATCH op=%b result=%08x stub=%b flags=%b",
                         op, result, stub_active, got_flags);
            end
        end
    endtask

    initial begin
        total  = 0;
        errors = 0;
        op = 2'b00;
        a  = 32'd0;
        b  = 32'd0;

        run_vectors("add_vectors.txt", 2'b00);
        run_vectors("sub_vectors.txt", 2'b01);

        check_stub(2'b10);
        check_stub(2'b11);

        if (errors == 0)
            $display("RESULT: PASS (%0d vectors)", total);
        else
            $display("RESULT: FAIL (%0d errors in %0d vectors)", errors, total);

        $finish;
    end

endmodule
