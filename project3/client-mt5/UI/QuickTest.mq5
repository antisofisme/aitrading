//+------------------------------------------------------------------+
//|                                              QuickTest.mq5      |
//|                                    Quick test for UI compilation |
//+------------------------------------------------------------------+
#property copyright "2024, Test"
#property version   "1.00"
#property script_show_inputs

#include "UIIntegrationHelper.mqh"

//+------------------------------------------------------------------+
//| Script program start function                                   |
//+------------------------------------------------------------------+
void OnStart()
{
    Print("=== UI COMPILATION TEST ===");

    // Test UI manager creation
    if(InitializeUI()) {
        Print("✅ UI initialization successful");

        // Test UI updates
        UpdateEAUIConnectionStatus(true, "Test Server");
        UpdateEAUITradingStatus("Testing");
        UpdateEAUIPerformanceMetrics(5.2, 144, "Binary");

        Print("✅ UI update functions work");

        // Test UI requests
        bool connectReq = CheckUIConnectRequest();
        bool disconnectReq = CheckUIDisconnectRequest();
        bool binaryPref = GetUIBinaryProtocolPreference();

        Print("✅ UI request functions work");
        Print("Binary Protocol Preference: ", binaryPref ? "TRUE" : "FALSE");

        // Cleanup
        ShutdownUI();
        Print("✅ UI shutdown successful");
    } else {
        Print("❌ UI initialization failed");
    }

    Print("=== TEST COMPLETED ===");
}