//+------------------------------------------------------------------+
//|                                              SimpleTest.mq5     |
//|                                    Simple UI syntax test        |
//+------------------------------------------------------------------+
#property copyright "2024"
#property version   "1.00"

// Test UI includes
#include "UIComponents.mqh"

//+------------------------------------------------------------------+
//| Script program start function                                   |
//+------------------------------------------------------------------+
void OnStart()
{
    Print("=== SIMPLE UI SYNTAX TEST ===");

    // Test component creation
    CStatusDisplay* statusDisplay = new CStatusDisplay();
    if(statusDisplay != NULL) {
        Print("✅ CStatusDisplay created successfully");
        delete statusDisplay;
    }

    CAccountInfoDisplay* accountInfo = new CAccountInfoDisplay();
    if(accountInfo != NULL) {
        Print("✅ CAccountInfoDisplay created successfully");
        delete accountInfo;
    }

    Print("=== SYNTAX TEST COMPLETED ===");
}