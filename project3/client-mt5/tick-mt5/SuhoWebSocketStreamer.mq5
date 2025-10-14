//+------------------------------------------------------------------+
//|                                   SuhoWebSocketStreamer.mq5      |
//|                        Copyright 2024, Suho AI Trading Platform |
//|                              https://aitrading.suho.platform     |
//+------------------------------------------------------------------+
#property copyright "2024, Suho AI Trading Platform"
#property link      "https://aitrading.suho.platform"
#property version   "1.00"
#property description "Suho Tick Data Collector - NOT A TRADING EA!"
#property description "ONE-WAY: Streams tick data to server (upload only)"
#property description "Uses Suho Binary Protocol (32 bytes per tick)"
#property description "Does NOT receive trading commands or execute trades"

#include "OptimizedWebSocket.mqh"
#include "BinaryProtocol.mqh"

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
input string InpWebSocketUrl = "ws://localhost:8001/ws/ticks";  // WebSocket URL
input string InpBrokerName = "FBS";                              // Your broker name
input string InpAccountId = "101632934";                         // Your MT5 account number
input bool   InpUseAsync = false;                                // Use async queue (false = real-time)
input int    InpPingInterval = 30;                               // Ping interval (seconds)
input bool   InpEnableLogs = true;                               // Enable detailed logging

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+

// 14 Trading pairs (as per project specification)
string TradingPairs[] = {
    "EURUSD",  // 1. EUR/USD
    "GBPUSD",  // 2. GBP/USD
    "USDJPY",  // 3. USD/JPY
    "USDCHF",  // 4. USD/CHF
    "AUDUSD",  // 5. AUD/USD
    "USDCAD",  // 6. USD/CAD
    "NZDUSD",  // 7. NZD/USD
    "EURGBP",  // 8. EUR/GBP
    "EURJPY",  // 9. EUR/JPY
    "GBPJPY",  // 10. GBP/JPY
    "AUDJPY",  // 11. AUD/JPY
    "NZDJPY",  // 12. NZD/JPY
    "CHFJPY",  // 13. CHF/JPY
    "XAUUSD"   // 14. XAU/USD (Gold)
};

// WebSocket client
OptimizedWebSocketClient ws;

// Statistics
ulong TotalTicksSent = 0;
ulong TotalErrors = 0;
datetime StartTime = 0;
datetime LastPingTime = 0;

// Performance tracking
ulong LastTickCount = 0;
datetime LastStatsTime = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("═══════════════════════════════════════════════════════");
    Print("🚀 Suho Tick Data Collector - Starting...");
    Print("⚠️  NOTE: This is NOT a trading EA!");
    Print("📤 ONE-WAY: Upload tick data only (no commands received)");
    Print("═══════════════════════════════════════════════════════");

    StartTime = TimeCurrent();
    LastPingTime = TimeCurrent();
    LastStatsTime = TimeCurrent();
    LastTickCount = 0;

    // Verify symbols are available
    int availableCount = 0;
    for(int i = 0; i < ArraySize(TradingPairs); i++) {
        if(SymbolSelect(TradingPairs[i], true)) {
            if(InpEnableLogs) {
                Print("✅ Symbol available: ", TradingPairs[i]);
            }
            availableCount++;
        } else {
            Print("⚠️  Symbol NOT available: ", TradingPairs[i]);
        }
    }

    if(availableCount == 0) {
        Print("❌ ERROR: No trading pairs available!");
        return INIT_FAILED;
    }

    // Binary mode is always enabled for Suho Binary Protocol

    // Connect to WebSocket server
    if(!ws.Connect(InpWebSocketUrl)) {
        Print("❌ Failed to connect to WebSocket server");
        return INIT_FAILED;
    }

    Print("───────────────────────────────────────────────────────");
    Print("📊 Configuration:");
    Print("   WebSocket URL: ", InpWebSocketUrl);
    Print("   Broker: ", InpBrokerName);
    Print("   Account: ", InpAccountId);
    Print("   Protocol: Suho Binary (32 bytes per tick)");
    Print("   Async Mode: ", InpUseAsync ? "Enabled (non-blocking)" : "Disabled (real-time)");
    Print("   Ping Interval: ", InpPingInterval, "s");
    Print("   Available Pairs: ", availableCount, "/", ArraySize(TradingPairs));
    Print("═══════════════════════════════════════════════════════");
    Print("✅ Tick Data Collector initialized successfully!");
    Print("📤 ONE-WAY Upload: Streaming ", availableCount, " pairs");
    Print("⚡ Suho Binary Protocol - 32 bytes per tick");
    Print("🚫 Does NOT execute trades or receive commands");
    Print("═══════════════════════════════════════════════════════");

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // Process remaining queue
    if(InpUseAsync) {
        Print("📤 Flushing send queue: ", ws.GetQueueSize(), " messages");
        while(ws.GetQueueSize() > 0) {
            ws.ProcessSendQueue();
            Sleep(10);
        }
    }

    // Disconnect WebSocket
    ws.Disconnect();

    PrintStatistics();

    Print("═══════════════════════════════════════════════════════");
    Print("👋 Suho Tick Data Collector - Shutdown completed");
    Print("═══════════════════════════════════════════════════════");
}

//+------------------------------------------------------------------+
//| Expert tick function                                            |
//+------------------------------------------------------------------+
void OnTick()
{
    // Check connection status
    if(!ws.IsConnected()) {
        Print("⚠️  WebSocket disconnected, attempting reconnect...");
        if(!ws.Connect(InpWebSocketUrl)) {
            Print("❌ Reconnection failed, will retry on next tick");
            return;
        }
        Print("✅ Reconnected successfully");
    }

    // Stream all ticks immediately (no batching for real-time)
    StreamAllTicks();

    // Process async send queue (if enabled)
    if(InpUseAsync) {
        ws.ProcessSendQueue();
    }

    // Send periodic ping for keep-alive
    if((TimeCurrent() - LastPingTime) >= InpPingInterval) {
        ws.SendPing();
        LastPingTime = TimeCurrent();
    }

    // Print statistics every 10 seconds
    if((TimeCurrent() - LastStatsTime) >= 10) {
        if(InpEnableLogs) {
            ulong ticksPerSecond = (TotalTicksSent - LastTickCount) / 10;
            Print("📊 Stats: ", ws.GetStatistics(), " | Ticks/sec: ", ticksPerSecond);
        }
        LastTickCount = TotalTicksSent;
        LastStatsTime = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Stream all ticks immediately (real-time, no buffering)         |
//+------------------------------------------------------------------+
void StreamAllTicks()
{
    for(int i = 0; i < ArraySize(TradingPairs); i++) {
        MqlTick tick;
        if(SymbolInfoTick(TradingPairs[i], tick)) {
            SendTickToServer(TradingPairs[i], tick);
        }
    }
}

//+------------------------------------------------------------------+
//| Send tick to WebSocket server using Suho Binary Protocol       |
//+------------------------------------------------------------------+
void SendTickToServer(string symbol, MqlTick &tick)
{
    // Encode tick to Suho Binary Protocol (32 bytes)
    char binaryData[];
    int size = CBinaryProtocol::CreateSingleTickPacket(symbol, tick, binaryData);

    // Send binary frame via WebSocket
    bool success = ws.SendBinary(binaryData, size);

    if(success) {
        TotalTicksSent++;
    } else {
        TotalErrors++;
        if(InpEnableLogs && (TotalErrors % 100 == 0)) {
            Print("⚠️  Send errors: ", TotalErrors, " (disconnected or network issue)");
        }
    }
}

//+------------------------------------------------------------------+
//| Print session statistics                                        |
//+------------------------------------------------------------------+
void PrintStatistics()
{
    datetime runtime = TimeCurrent() - StartTime;
    double ticksPerSecond = runtime > 0 ? (double)TotalTicksSent / runtime : 0;

    Print("═══════════════════════════════════════════════════════");
    Print("📊 SUHO TICK DATA COLLECTOR - SESSION SUMMARY");
    Print("═══════════════════════════════════════════════════════");
    Print("⏱️  Runtime: ", runtime, " seconds (", DoubleToString(runtime/3600.0, 2), " hours)");
    Print("📡 Total ticks sent: ", TotalTicksSent);
    Print("❌ Total errors: ", TotalErrors);
    Print("📈 Ticks per second: ", DoubleToString(ticksPerSecond, 2));
    Print("✅ Success rate: ", DoubleToString(100.0 * TotalTicksSent / (TotalTicksSent + TotalErrors), 2), "%");
    Print("");
    Print("🔌 WebSocket Statistics:");
    Print("   ", ws.GetStatistics());
    Print("═══════════════════════════════════════════════════════");
}
//+------------------------------------------------------------------+
