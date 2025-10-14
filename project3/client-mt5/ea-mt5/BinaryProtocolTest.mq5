//+------------------------------------------------------------------+
//|                                           BinaryProtocolTest.mq5 |
//|                                          Test binary protocol implementation |
//+------------------------------------------------------------------+
#property copyright "2024, AI Trading Platform"
#property link      "https://aitrading.suho.platform"
#property version   "1.00"
#property script_show_inputs

#include "BinaryProtocol.mqh"

//+------------------------------------------------------------------+
//| Script program start function                                   |
//+------------------------------------------------------------------+
void OnStart()
{
    Print("=== BINARY PROTOCOL TEST SUITE ===");

    // Test 1: Symbol ID conversion
    TestSymbolConversion();

    // Test 2: Price conversion
    TestPriceConversion();

    // Test 3: Binary packet creation
    TestPacketCreation();

    // Test 4: Packet validation
    TestPacketValidation();

    Print("=== ALL TESTS COMPLETED ===");
}

//+------------------------------------------------------------------+
//| Test symbol ID conversion                                       |
//+------------------------------------------------------------------+
void TestSymbolConversion()
{
    Print("\n[TEST 1] Symbol ID Conversion:");

    string testSymbols[] = {"EURUSD", "GBPUSD", "XAUUSD", "INVALID"};

    for(int i = 0; i < ArraySize(testSymbols); i++) {
        ENUM_SYMBOL_ID id = CBinaryProtocol::GetSymbolID(testSymbols[i]);
        string backToString = CBinaryProtocol::GetSymbolString(id);

        Print("Symbol: " + testSymbols[i] + " -> ID: " + IntegerToString(id) + " -> Back: " + backToString);

        if(testSymbols[i] != "INVALID" && testSymbols[i] == backToString) {
            Print("✅ PASS: " + testSymbols[i]);
        } else if(testSymbols[i] == "INVALID" && id == SYMBOL_UNKNOWN) {
            Print("✅ PASS: Invalid symbol correctly identified");
        } else {
            Print("❌ FAIL: " + testSymbols[i]);
        }
    }
}

//+------------------------------------------------------------------+
//| Test price conversion                                           |
//+------------------------------------------------------------------+
void TestPriceConversion()
{
    Print("\n[TEST 2] Price Conversion:");

    double testPrices[] = {1.09551, 1.27082, 150.123, 0.00001};

    for(int i = 0; i < ArraySize(testPrices); i++) {
        uint fixedPoint = CBinaryProtocol::PriceToFixedPoint(testPrices[i]);
        double backToDouble = CBinaryProtocol::FixedPointToPrice(fixedPoint);

        double difference = MathAbs(testPrices[i] - backToDouble);

        Print("Price: " + DoubleToString(testPrices[i], 5) + " -> Fixed: " + IntegerToString(fixedPoint) +
              " -> Back: " + DoubleToString(backToDouble, 5) + " (diff: " + DoubleToString(difference, 8) + ")");

        if(difference < 0.000001) {  // Less than 0.1 pip difference
            Print("✅ PASS: Price conversion accurate");
        } else {
            Print("❌ FAIL: Price conversion inaccurate");
        }
    }
}

//+------------------------------------------------------------------+
//| Test binary packet creation                                     |
//+------------------------------------------------------------------+
void TestPacketCreation()
{
    Print("\n[TEST 3] Binary Packet Creation:");

    // Test price stream packet
    string symbols[] = {"EURUSD", "GBPUSD"};
    MqlTick ticks[];
    ArrayResize(ticks, 2);

    // Set fake tick data
    ticks[0].bid = 1.09551;
    ticks[0].ask = 1.09553;
    ticks[1].bid = 1.27082;
    ticks[1].ask = 1.27085;

    char buffer[];
    int packetSize = CBinaryProtocol::CreatePriceStreamPacket("test_user", symbols, ticks, buffer);

    Print("Price stream packet size: " + IntegerToString(packetSize) + " bytes");
    Print("Expected size: " + IntegerToString(16 + (2 * 16)) + " bytes (header + 2 prices)");

    if(packetSize == 48) {  // 16 byte header + 2*16 byte prices
        Print("✅ PASS: Packet size correct");
    } else {
        Print("❌ FAIL: Incorrect packet size");
    }

    // Test packet validation
    if(CBinaryProtocol::ValidatePacket(buffer, packetSize)) {
        Print("✅ PASS: Packet validation successful");
    } else {
        Print("❌ FAIL: Packet validation failed");
    }

    // Show packet info
    string info = CBinaryProtocol::GetPacketInfo(buffer, packetSize);
    Print("Packet Info:\n" + info);
}

//+------------------------------------------------------------------+
//| Test packet validation                                          |
//+------------------------------------------------------------------+
void TestPacketValidation()
{
    Print("\n[TEST 4] Packet Validation:");

    // Create corrupted packet
    char corruptedBuffer[];
    ArrayResize(corruptedBuffer, 16);
    ArrayInitialize(corruptedBuffer, 0);

    // Set invalid magic number
    corruptedBuffer[0] = 0xFF;
    corruptedBuffer[1] = 0xFF;
    corruptedBuffer[2] = 0xFF;
    corruptedBuffer[3] = 0xFF;

    if(!CBinaryProtocol::ValidatePacket(corruptedBuffer, 16)) {
        Print("✅ PASS: Corrupted packet correctly rejected");
    } else {
        Print("❌ FAIL: Corrupted packet incorrectly accepted");
    }

    // Test undersized packet
    char smallBuffer[];
    ArrayResize(smallBuffer, 8);

    if(!CBinaryProtocol::ValidatePacket(smallBuffer, 8)) {
        Print("✅ PASS: Undersized packet correctly rejected");
    } else {
        Print("❌ FAIL: Undersized packet incorrectly accepted");
    }
}