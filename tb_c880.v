`timescale 1ns / 1ps

module tb_c880;

    // Inputs
    reg G1,G2,G3,G4,G5,G6,G7,G8,G9,G10,G11,G12,G13,G14,G15,G16,G17,G18,G19,G20,G21,G22,G23,G24,G25,G26,G27,G28,G29,G30,G31,G32,G33,G34,G35,G36,G37,G38,G39,G40,G41,G42,G43,G44,G45,G46,G47,G48,G49,G50,G51,G52,G53,G54,G55,G56,G57,G58,G59,G60;


    // Instantiate the Unit Under Test (UUT)
    c880 uut (
       .G1(G1), .G2(G2), .G3(G3), .G4(G4), .G5(G5), .G6(G6), .G7(G7), .G8(G8), .G9(G9), .G10(G10),
       .G11(G11), .G12(G12), .G13(G13), .G14(G14), .G15(G15), .G16(G16), .G17(G17), .G18(G18), .G19(G19), .G20(G20),
       .G21(G21), .G22(G22), .G23(G23), .G24(G24), .G25(G25), .G26(G26), .G27(G27), .G28(G28), .G29(G29), .G30(G30),
       .G31(G31), .G32(G32), .G33(G33), .G34(G34), .G35(G35), .G36(G36), .G37(G37), .G38(G38), .G39(G39), .G40(G40),
       .G41(G41), .G42(G42), .G43(G43), .G44(G44), .G45(G45), .G46(G46), .G47(G47), .G48(G48), .G49(G49), .G50(G50),
       .G51(G51), .G52(G52), .G53(G53), .G54(G54), .G55(G55), .G56(G56), .G57(G57), .G58(G58), .G59(G59), .G60(G60),
       .G855(), .G856(), .G857(), .G858(), .G859(), .G860(),
       .G861(), .G862(), .G863(), .G864(), .G865(), .G866(), 
       .G867(), .G868(), .G869(), .G870(), .G871(), .G872(),
       .G873(), .G874(), .G875(), .G876(), .G877(), .G878(), 
       .G879(), .G880()
);


    // Clock Generation
    reg CK;
    always #10 CK = ~CK; // Generate a clock with 20ns period

    initial begin
        CK = 0;
        $set_gate_level_monitoring("on");
        $set_toggle_region("tb_c880");
        $toggle_start;
        G1 = 1;
        G2 = 1;
        G3 = 1;
        G4 = 1;
        G5 = 0;
        G6 = 1;
        G7 = 0;
        G8 = 1;
        G9 = 1;
        G10 = 1;
        G11 = 0;
        G12 = 1;
        G13 = 1;
        G14 = 0;
        G15 = 1;
        G16 = 0;
        G17 = 0;
        G18 = 1;
        G19 = 0;
        G20 = 1;
        G21 = 0;
        G22 = 1;
        G23 = 0;
        G24 = 1;
        G25 = 0;
        G26 = 0;
        G27 = 0;
        G28 = 0;
        G29 = 1;
        G30 = 1;
        G31 = 1;
        G32 = 0;
        G33 = 0;
        G34 = 0;
        G35 = 1;
        G36 = 1;
        G37 = 0;
        G38 = 1;
        G39 = 1;
        G40 = 0;
        G41 = 1;
        G42 = 1;
        G43 = 0;
        G44 = 1;
        G45 = 1;
        G46 = 1;
        G47 = 1;
        G48 = 1;
        G49 = 1;
        G50 = 1;
        G51 = 1;
        G52 = 1;
        G53 = 0;
        G54 = 1;
        G55 = 0;
        G56 = 1;
        G57 = 0;
        G58 = 0;
        G59 = 1;
        G60 = 0;
        #20;
        $toggle_stop;

        // Generate SAIF file
        $toggle_report("c880.saif", 1e-09, "tb_c880");

        $finish;
    end

endmodule

