//+------------------------------------------------------------------+
//|                                              Suho - AI Trading.mq5 |
//|                                    Copyright 2024, AI Trading Platform |
//|                                       https://aitrading.suho.platform |
//+------------------------------------------------------------------+
#property copyright "2024, AI Trading Platform"
#property link      "https://aitrading.suho.platform"
#property version   "1.00"
#property description "Suho AI Trading - Professional AI-Powered Trading Expert Advisor"
#property description "Dual functionality: Account Profile Management + Real-time Price Streaming"
#property description "Server-side AI analysis with client-side execution for optimal performance"
#property description ""
#property description "Features:"
#property description "- Real-time AI trading signals from centralized server"
#property description "- Automatic price adjustment for broker differences"
#property description "- Professional risk management and position sizing"
#property description "- Multi-pair correlation analysis support"
#property description "- Zero-latency execution with local MT5 integration"
#property description ""
#property description "Support: support@suho.platform"

//+------------------------------------------------------------------+
//| Include Libraries                                                |
//+------------------------------------------------------------------+
#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>
#include <Trade\SymbolInfo.mqh>
#include <Trade\DealInfo.mqh>
#include <Trade\HistoryOrderInfo.mqh>
#include "WebSocketClient.mqh"
#include "JsonHelper.mqh"

//+------------------------------------------------------------------+
//| Input Parameters - Professional Settings Interface              |
//+------------------------------------------------------------------+

// === ENHANCED SERVER CONNECTION ===
// Enhanced Server Connection Settings
input string    InpServerURL = "ws://localhost:8001/ws/trading";    // Trading WebSocket URL
input string    InpAuthToken = "";                                    // JWT Authentication Token
input string    InpUserID = "user123";                             // Your unique User ID
input int       InpMagicNumber = 20241226;                           // EA Magic Number
input bool      InpTestingMode = true;                               // Enable for localhost testing

// === TRADING PREFERENCES ===
input group "TRADING SETTINGS"
input bool      InpAutoTrading = true;                                // Enable automatic trading
input double    InpMaxRiskPerTrade = 2.0;                            // Maximum risk % per trade
input double    InpMaxDailyLoss = 1000.0;                            // Maximum daily loss (USD)
input int       InpMaxOpenPositions = 3;                             // Maximum simultaneous positions
input double    InpPreferredLotSize = 0.1;                           // Preferred position size

// === MAJOR PAIRS SELECTION (Trading + Analysis) ===
input group "MAJOR PAIRS - Trading & AI Analysis"
input bool      InpTrade_EURUSD = true;                              // EUR/USD - Euro vs US Dollar
input bool      InpTrade_GBPUSD = true;                              // GBP/USD - British Pound vs US Dollar
input bool      InpTrade_USDJPY = true;                              // USD/JPY - US Dollar vs Japanese Yen
input bool      InpTrade_USDCHF = false;                             // USD/CHF - US Dollar vs Swiss Franc
input bool      InpTrade_AUDUSD = false;                             // AUD/USD - Australian Dollar vs US Dollar
input bool      InpTrade_USDCAD = false;                             // USD/CAD - US Dollar vs Canadian Dollar
input bool      InpTrade_NZDUSD = false;                             // NZD/USD - New Zealand Dollar vs US Dollar

// === PRECIOUS METALS (Trading + Analysis) ===
input group "PRECIOUS METALS - Trading & AI Analysis"
input bool      InpTrade_XAUUSD = false;                             // XAU/USD - Gold vs US Dollar
input bool      InpTrade_XAGUSD = false;                             // XAG/USD - Silver vs US Dollar


// === DATA STREAMING ===
input group "DATA STREAMING"
input int       InpStreamingInterval = 1000;                         // Streaming interval (ms)
input bool      InpStreamCurrentChartOnly = false;                   // Stream only current chart (ignore selections above)

// === ADVANCED SETTINGS ===
input group "ADVANCED SETTINGS"
input bool      InpConservativeMode = false;                         // Conservative trading mode
input double    InpMaxDrawdown = 15.0;                               // Maximum drawdown %
input bool      InpAutoCloseOnFriday = true;                         // Auto-close positions on Friday
input bool      InpAllowNewsTrading = false;                         // Allow trading during news

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
CTrade trade;
CPositionInfo positionInfo;
CAccountInfo accountInfo;
CSymbolInfo symbolInfo;
CWebSocketClient wsClient;

// Connection status
datetime LastConnectionCheck = 0;
datetime LastPriceStream = 0;
datetime LastCommandCheck = 0;

// Trading symbols array
string TradingSymbols[];        // Selected major pairs + metals for trading & streaming

// Performance tracking
int TotalTrades = 0;
double TotalProfit = 0.0;
datetime StartTime = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("[INIT] Suho AI Trading EA - Initializing...");

    // Record start time
    StartTime = TimeCurrent();

    // Initialize trading objects
    trade.SetExpertMagicNumber(InpMagicNumber);  // Use configured magic number
    trade.SetDeviationInPoints(10);
    trade.SetTypeFilling(ORDER_FILLING_FOK);

    // Initialize symbols
    if(!InitializeTradingSymbols()) {
        Print("[ERROR] Failed to initialize trading symbols");
        return INIT_FAILED;
    }

    // Initialize WebSocket client
    wsClient.SetServer(InpServerURL, InpAuthToken, InpUserID);

    // Test server connection
    if(!ConnectToServer()) {
        Print("[WARNING] Initial server connection failed - will retry");
        // Don't fail initialization, continue with retry logic
    }

    // Send account profile on startup
    if(wsClient.IsConnected()) {
        SendAccountProfile();
    }

    Print("[SUCCESS] Suho AI Trading EA - Initialization completed successfully");
    Print("[INFO] Monitoring " + IntegerToString(ArraySize(TradingSymbols)) + " trading pairs");
    Print("Server connection: " + (wsClient.IsConnected() ? "Connected" : "Disconnected"));

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                               |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("[SHUTDOWN] Suho AI Trading EA - Shutting down...");

    // Send shutdown notification
    if(wsClient.IsConnected()) {
        SendShutdownNotification();
    }

    // Print performance summary
    PrintPerformanceSummary();

    Print("[SHUTDOWN] Suho AI Trading EA - Shutdown completed");
}

//+------------------------------------------------------------------+
//| Expert tick function                                            |
//+------------------------------------------------------------------+
void OnTick()
{
    // Connection maintenance
    if(TimeCurrent() - LastConnectionCheck > 30) { // Check every 30 seconds
        CheckServerConnection();
        LastConnectionCheck = TimeCurrent();
    }

    // Price streaming - automatically stream selected pairs
    if(wsClient.IsConnected()) {
        if(TimeCurrent() - LastPriceStream >= InpStreamingInterval / 1000) {
            StreamPricesToServer();
        }
    }

    // Process any pending server commands (check every 5 seconds)
    if(TimeCurrent() - LastCommandCheck >= 5) {
        ProcessServerCommands();
        LastCommandCheck = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Initialize Trading Symbols                                      |
//+------------------------------------------------------------------+
bool InitializeTradingSymbols()
{
    // Initialize trading symbols (majors + metals)
    string tradingPairs[];
    int tradingCount = 0;

    // Major pairs
    if(InpTrade_EURUSD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "EURUSD"; tradingCount++; }
    if(InpTrade_GBPUSD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "GBPUSD"; tradingCount++; }
    if(InpTrade_USDJPY) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "USDJPY"; tradingCount++; }
    if(InpTrade_USDCHF) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "USDCHF"; tradingCount++; }
    if(InpTrade_AUDUSD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "AUDUSD"; tradingCount++; }
    if(InpTrade_USDCAD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "USDCAD"; tradingCount++; }
    if(InpTrade_NZDUSD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "NZDUSD"; tradingCount++; }

    // Precious metals
    if(InpTrade_XAUUSD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "XAUUSD"; tradingCount++; }
    if(InpTrade_XAGUSD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "XAGUSD"; tradingCount++; }

    // Validate and setup trading symbols
    if(tradingCount == 0) {
        Print("[WARNING] No trading pairs selected - EA will run in monitoring mode only");
    } else {
        ArrayResize(TradingSymbols, tradingCount);
        for(int i = 0; i < tradingCount; i++) {
            TradingSymbols[i] = tradingPairs[i];

            if(!SymbolSelect(tradingPairs[i], true)) {
                Print("[WARNING] Trading symbol not available: " + tradingPairs[i]);
            } else {
                Print("[SUCCESS] Trading symbol initialized: " + tradingPairs[i]);
            }
        }
    }

    Print("[INFO] Trading pairs initialized: " + IntegerToString(tradingCount) + " pairs (streaming bid/ask only)");

    return true; // Always return true, allow monitoring mode even without trading pairs
}

//+------------------------------------------------------------------+
//| Connect to Server                                              |
//+------------------------------------------------------------------+
bool ConnectToServer()
{
    // Validate configuration
    if(StringLen(InpUserID) == 0) {
        Print("[ERROR] User ID not configured");
        return false;
    }

    if(InpTestingMode) {
        Print("[TEST] Test mode: Connecting to localhost server");
        // Update URL for localhost testing
        string testUrl = "http://localhost:8000";
        wsClient.SetServer(testUrl, InpAuthToken, InpUserID);
    } else {
        if(StringLen(InpAuthToken) == 0) {
            Print("[ERROR] Auth token not configured for production");
            return false;
        }
    }

    Print("[CONNECT] Attempting connection to server...");

    // Use actual HTTP client connection
    bool connected = wsClient.TestConnection();

    if(connected) {
        Print("[SUCCESS] Connected to server successfully");
    } else {
        Print("[ERROR] Server connection failed");
    }

    return connected;
}

//+------------------------------------------------------------------+
//| Check Server Connection                                        |
//+------------------------------------------------------------------+
void CheckServerConnection()
{
    if(!wsClient.IsHealthy()) {
        Print("[RECONNECT] Connection unhealthy, attempting to reconnect...");
        ConnectToServer();
    }

    // Log connection statistics for debugging
    if(wsClient.GetRetryCount() > 0) {
        Print("[INFO] Connection retries: " + IntegerToString(wsClient.GetRetryCount()));
    }
}

//+------------------------------------------------------------------+
//| Send Account Profile to Server                                 |
//+------------------------------------------------------------------+
bool SendAccountProfile()
{
    if(!wsClient.IsConnected()) return false;

    Print("[SEND] Sending account profile to server...");

    // Create Protocol Buffers format profile data
    string profileProto = JsonHelper::CreateAccountProfileProto(InpUserID);

    // Add selected trading pairs to the proto
    if(ArraySize(TradingSymbols) > 0) {
        // Remove closing bracket temporarily
        StringReplace(profileProto, "}", "");

        // Add trading pairs array
        profileProto += ",\"trading_pairs\":[";
        for(int i = 0; i < ArraySize(TradingSymbols); i++) {
            if(i > 0) profileProto += ",";
            profileProto += "\"" + TradingSymbols[i] + "\"";
        }
        profileProto += "]}";
    }

    Print("[INFO] Profile data (Protocol Buffers): " + IntegerToString(StringLen(profileProto)) + " characters");

    // Send via HTTP client
    return wsClient.SendAccountProfile(profileProto);
}

//+------------------------------------------------------------------+
//| Stream Current Prices to Server                                |
//+------------------------------------------------------------------+
bool StreamPricesToServer()
{
    if(!wsClient.IsConnected()) return false;

    // Create Protocol Buffers format price stream
    string priceStreamData = "{\"user_id\":\"" + InpUserID + "\",\"timestamp\":" + IntegerToString(TimeCurrent()) + ",\"prices\":[";
    int priceCount = 0;

    if(InpStreamCurrentChartOnly) {
        // Stream only current chart symbol using Protocol Buffers format
        MqlTick tick;
        if(SymbolInfoTick(_Symbol, tick)) {
            string marketData = JsonHelper::CreateMarketDataProto(InpUserID, _Symbol, tick.bid, tick.ask, TimeCurrent());
            priceStreamData += marketData;
            priceCount = 1;
        }
    } else {
        // Stream selected trading pairs using Protocol Buffers format
        for(int i = 0; i < ArraySize(TradingSymbols); i++) {
            MqlTick tick;
            if(SymbolInfoTick(TradingSymbols[i], tick)) {
                if(priceCount > 0) priceStreamData += ",";
                string marketData = JsonHelper::CreateMarketDataProto(InpUserID, TradingSymbols[i], tick.bid, tick.ask, TimeCurrent());
                priceStreamData += marketData;
                priceCount++;
            }
        }
    }

    priceStreamData += "]}";

    // Update last stream time
    LastPriceStream = TimeCurrent();

    // Send via HTTP client (only if we have data)
    if(priceCount > 0) {
        return wsClient.SendPriceData(priceStreamData);
    }

    return true;
}

//+------------------------------------------------------------------+
//| Process Server Commands                                         |
//+------------------------------------------------------------------+
void ProcessServerCommands()
{
    if(!wsClient.IsConnected()) return;

    // Get pending commands from server
    string commandsResponse = wsClient.GetServerCommands();

    if(StringLen(commandsResponse) > 0) {
        Print("[RECV] Received server commands: " + IntegerToString(StringLen(commandsResponse)) + " characters");

        // TODO: Parse JSON commands and execute trades
        // For now, just log that we received commands
        ParseAndExecuteCommands(commandsResponse);
    }
}

//+------------------------------------------------------------------+
//| Parse and execute trading commands from server                  |
//+------------------------------------------------------------------+
void ParseAndExecuteCommands(string commandsJson)
{
    Print("[PROCESS] Processing AI trading commands (Protocol Buffers)...");

    // Parse Protocol Buffers command using JsonHelper
    string action = "", symbol = "";
    double lots = 0.0, stopLoss = 0.0, takeProfit = 0.0;

    if(JsonHelper::ParseTradingCommand(commandsJson, action, symbol, lots, stopLoss, takeProfit)) {
        Print("[PARSED] Command parsed - Action: " + action + ", Symbol: " + symbol + ", Lots: " + DoubleToString(lots, 2));

        if(action == "BUY") {
            Print("[BUY] AI Signal: BUY " + symbol + " " + DoubleToString(lots, 2) + " lots");
            ExecuteBuyOrder(symbol, lots, stopLoss, takeProfit);
        }
        else if(action == "SELL") {
            Print("[SELL] AI Signal: SELL " + symbol + " " + DoubleToString(lots, 2) + " lots");
            ExecuteSellOrder(symbol, lots, stopLoss, takeProfit);
        }
        else if(action == "CLOSE") {
            Print("[CLOSE] AI Signal: CLOSE " + symbol + " positions");
            ClosePositions(symbol);
        }
        else {
            Print("[WARNING] Unknown command action: " + action);
        }
    } else {
        Print("[ERROR] Failed to parse Protocol Buffers command");
    }

    // Send acknowledgment back to server in Protocol Buffers format
    string ackData = JsonHelper::CreateTradeConfirmationProto(InpUserID, "RECEIVED", "", 0, 0, 0);
    wsClient.SendTradeConfirmation(ackData);
}

//+------------------------------------------------------------------+
//| Execute Buy Order (Placeholder for next phase)                 |
//+------------------------------------------------------------------+
void ExecuteBuyOrder(string symbol, double lots, double stopLoss, double takeProfit)
{
    Print("[TODO] Execute BUY order for " + symbol);
    // TODO: Implement actual order execution in next phase
}

//+------------------------------------------------------------------+
//| Execute Sell Order (Placeholder for next phase)                |
//+------------------------------------------------------------------+
void ExecuteSellOrder(string symbol, double lots, double stopLoss, double takeProfit)
{
    Print("[TODO] Execute SELL order for " + symbol);
    // TODO: Implement actual order execution in next phase
}

//+------------------------------------------------------------------+
//| Close Positions (Placeholder for next phase)                   |
//+------------------------------------------------------------------+
void ClosePositions(string symbol)
{
    Print("[TODO] Close positions for " + symbol);
    // TODO: Implement position closing in next phase
}

//+------------------------------------------------------------------+
//| Send Shutdown Notification                                     |
//+------------------------------------------------------------------+
void SendShutdownNotification()
{
    if(!wsClient.IsConnected()) return;

    Print("[SEND] Sending shutdown notification...");

    // Create Protocol Buffers format shutdown notification
    string shutdownProto = "{";
    shutdownProto = JsonHelper::AddStringField(shutdownProto, "user_id", InpUserID);
    shutdownProto = JsonHelper::AddStringField(shutdownProto, "event", "EA_SHUTDOWN");
    shutdownProto = JsonHelper::AddIntegerField(shutdownProto, "timestamp", TimeCurrent());
    shutdownProto = JsonHelper::AddNumericField(shutdownProto, "final_balance", AccountInfoDouble(ACCOUNT_BALANCE));
    shutdownProto = JsonHelper::AddNumericField(shutdownProto, "final_equity", AccountInfoDouble(ACCOUNT_EQUITY));
    shutdownProto = JsonHelper::AddIntegerField(shutdownProto, "open_positions", PositionsTotal());
    shutdownProto = JsonHelper::AddIntegerField(shutdownProto, "total_trades", TotalTrades);
    shutdownProto = JsonHelper::AddNumericField(shutdownProto, "total_profit", TotalProfit);
    shutdownProto += "}";

    // Send via HTTP client
    wsClient.SendTradeConfirmation(shutdownProto);
    Print("[INFO] Shutdown notification sent (Protocol Buffers)");
}

//+------------------------------------------------------------------+
//| Print Performance Summary                                       |
//+------------------------------------------------------------------+
void PrintPerformanceSummary()
{
    datetime runtime = TimeCurrent() - StartTime;

    Print("[SUMMARY] === SUHO AI TRADING PERFORMANCE SUMMARY ===");
    Print("[RUNTIME] Runtime: " + IntegerToString(runtime) + " seconds (" +
          DoubleToString(runtime / 3600.0, 1) + " hours)");
    Print("[TRADES] Total trades executed: " + IntegerToString(TotalTrades));
    Print("[PROFIT] Total profit/loss: $" + DoubleToString(TotalProfit, 2));
    Print("[BALANCE] Starting balance: $" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2));
    Print("[BALANCE] Current balance: $" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2));
    Print("[CONNECTION] Server connection status: " + (wsClient.IsConnected() ? "Connected" : "Disconnected"));
    Print("===============================================");
}

//+------------------------------------------------------------------+
//| Handle Emergency Stop                                          |
//+------------------------------------------------------------------+
void HandleEmergencyStop(string reason)
{
    Print("[EMERGENCY] EMERGENCY STOP TRIGGERED: " + reason);

    // Close all open positions immediately
    for(int i = 0; i < PositionsTotal(); i++) {
        if(positionInfo.SelectByIndex(i)) {
            if(positionInfo.Symbol() == _Symbol || !InpStreamCurrentChartOnly) {
                trade.PositionClose(positionInfo.Ticket());
                Print("[EMERGENCY] Emergency close: " + positionInfo.Symbol() + " - " + DoubleToString(positionInfo.Volume(), 2) + " lots");
            }
        }
    }

    // Cancel all pending orders
    for(int i = 0; i < OrdersTotal(); i++) {
        ulong ticket = OrderGetTicket(i);
        if(ticket > 0) {
            trade.OrderDelete(ticket);
            Print("[EMERGENCY] Emergency cancel order: " + IntegerToString(ticket));
        }
    }

    Print("[EMERGENCY] Emergency stop completed - All positions closed");
}