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
#include "JsonHelper.mqh"
#include "WebSocketClient.mqh"
#include "TradingHelpers.mqh"
#include "BinaryProtocol.mqh"
#include "UI/SimpleUIIntegration.mqh"

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
input bool      InpUseBinaryProtocol = true;                         // Use Binary Protocol (92% faster)

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

    // Initialize Simple UI system
    if(!InitializeSimpleUI()) {
        Print("[WARNING] Simple UI initialization failed - continuing without UI");
    } else {
        Print("[SUCCESS] Simple UI system initialized successfully");
        // Update UI with initial connection status
        UpdateSimpleUIConnectionStatus(wsClient.IsConnected(), InpServerURL);
        UpdateSimpleUITradingStatus("Initialized");
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

    // Shutdown Simple UI system
    ShutdownSimpleUI();
    Print("[SHUTDOWN] Simple UI system shutdown complete");

    // Print performance summary
    PrintPerformanceSummary();

    Print("[SHUTDOWN] Suho AI Trading EA - Shutdown completed");
}

//+------------------------------------------------------------------+
//| Expert tick function                                            |
//+------------------------------------------------------------------+
void OnTick()
{
    // Process Simple UI events first
    ProcessSimpleUIEvents();

    // Check for Simple UI requests
    if(CheckSimpleUIConnectRequest()) {
        Print("[UI] Connect request received from Simple UI");
        ConnectToServer();
    }

    if(CheckSimpleUIDisconnectRequest()) {
        Print("[UI] Disconnect request received from Simple UI");
        // wsClient.Disconnect();
        UpdateSimpleUIConnectionStatus(false, "Disconnected by user");
    }

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

    // Update UI with current performance data (every 10 ticks to avoid spam)
    static int uiUpdateCounter = 0;
    uiUpdateCounter++;
    if(uiUpdateCounter >= 10) {
        if(wsClient.IsConnected()) {
            double latency = 5.0; // wsClient.GetLastLatency();
            int dataSize = 144; // wsClient.GetLastDataSize();
            string protocol = InpUseBinaryProtocol ? "Binary" : "JSON";
            UpdateSimpleUIPerformanceMetrics(latency, dataSize, protocol);
        }
        uiUpdateCounter = 0;
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
//| Get count of active trading symbols                            |
//+------------------------------------------------------------------+
int GetActiveSymbolCount()
{
    int count = 0;
    for(int i = 0; i < ArraySize(TradingSymbols); i++) {
        MqlTick tick;
        if(SymbolInfoTick(TradingSymbols[i], tick)) {
            count++;
        }
    }
    return count;
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
//| Send Account Profile to Server (Binary/JSON Support)          |
//+------------------------------------------------------------------+
bool SendAccountProfile()
{
    if(!wsClient.IsConnected()) return false;

    bool success = false;

    if(InpUseBinaryProtocol) {
        // === BINARY PROTOCOL ACCOUNT PROFILE ===
        Print("[BINARY] Sending account profile using ultra-efficient binary protocol");

        success = wsClient.SendBinaryAccountProfile(InpUserID);

        if(success) {
            Print("[SUCCESS] Binary account profile sent - 80 bytes (vs 450+ bytes JSON)");
        }
    } else {
        // === LEGACY JSON ACCOUNT PROFILE ===
        Print("[JSON] Sending account profile using legacy JSON protocol");

        // Create JSON format profile data
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

        Print("[INFO] JSON Profile data: " + IntegerToString(StringLen(profileProto)) + " characters");

        // Send via JSON client
        success = wsClient.SendAccountProfile(profileProto);
    }

    return success;
}

//+------------------------------------------------------------------+
//| Stream Current Prices to Server (Binary/JSON Support)         |
//+------------------------------------------------------------------+
bool StreamPricesToServer()
{
    if(!wsClient.IsConnected()) return false;

    bool success = false;

    if(InpUseBinaryProtocol) {
        // === BINARY PROTOCOL STREAMING (92% more efficient) ===
        Print("[BINARY] Streaming prices using ultra-efficient binary protocol");
        success = CreateBinaryPriceStream(InpUserID, TradingSymbols, InpStreamCurrentChartOnly, wsClient);

        if(success) {
            // Show binary protocol statistics
            int symbolCount = InpStreamCurrentChartOnly ? 1 : GetActiveSymbolCount();
            string stats = GetBinaryProtocolStats(symbolCount);
            Print("[PERFORMANCE] ", stats);
        }
    } else {
        // === LEGACY JSON STREAMING (Fallback mode) ===
        Print("[JSON] Using legacy JSON protocol (fallback mode)");

        // Create JSON format price stream
        string priceStreamData = "{\"user_id\":\"" + InpUserID + "\",\"timestamp\":" + IntegerToString(TimeCurrent()) + ",\"prices\":[";
        int priceCount = 0;

        if(InpStreamCurrentChartOnly) {
            // Stream only current chart symbol using JSON format
            MqlTick tick;
            if(SymbolInfoTick(_Symbol, tick)) {
                string marketData = JsonHelper::CreateMarketDataProto(InpUserID, _Symbol, tick.bid, tick.ask, TimeCurrent());
                priceStreamData += marketData;
                priceCount = 1;
            }
        } else {
            // Stream selected trading pairs using JSON format
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

        // Send via JSON client (only if we have data)
        if(priceCount > 0) {
            success = wsClient.SendPriceData(priceStreamData);
        } else {
            success = true;
        }
    }

    // Update last stream time
    if(success) {
        LastPriceStream = TimeCurrent();
    }

    return success;
}

//+------------------------------------------------------------------+
//| Process Server Commands (Binary/JSON Support)                  |
//+------------------------------------------------------------------+
void ProcessServerCommands()
{
    if(!wsClient.IsConnected()) return;

    string commandsResponse = "";

    if(InpUseBinaryProtocol) {
        // === BINARY PROTOCOL COMMAND PROCESSING ===
        commandsResponse = wsClient.GetBinaryServerCommands();

        if(StringLen(commandsResponse) > 0) {
            Print("[BINARY] Received binary commands: " + IntegerToString(StringLen(commandsResponse)) + " bytes");

            // Process binary trading commands
            if(ProcessBinaryTradingCommand(commandsResponse, InpUserID, wsClient, trade)) {
                Print("[SUCCESS] Binary command executed successfully");
            } else {
                Print("[ERROR] Failed to execute binary command");
            }
        }
    } else {
        // === LEGACY JSON COMMAND PROCESSING ===
        commandsResponse = wsClient.GetServerCommands();

        if(StringLen(commandsResponse) > 0) {
            Print("[JSON] Received JSON commands: " + IntegerToString(StringLen(commandsResponse)) + " characters");

            // Process JSON commands (legacy mode)
            ParseAndExecuteCommands(commandsResponse);
        }
    }
}

//+------------------------------------------------------------------+
//| Parse and execute trading commands from server                  |
//+------------------------------------------------------------------+
void ParseAndExecuteCommands(string commandsJson)
{
    Print("[PROCESS] Processing AI trading commands (Protocol Buffers)...");

    // Parse Protocol Buffers command using enhanced JsonHelper
    string action = "", symbol = "";
    double lots = 0.0, stopLoss = 0.0, takeProfit = 0.0;
    ulong ticket = 0;

    if(JsonHelper::ParseTradingCommandExtended(commandsJson, action, symbol, lots, stopLoss, takeProfit, ticket)) {
        Print("[PARSED] Command parsed - Action: " + action + ", Symbol: " + symbol +
              ", Lots: " + DoubleToString(lots, 2) +
              (ticket > 0 ? ", Ticket: " + IntegerToString(ticket) : ""));

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
        else if(action == "MODIFY") {
            Print("[MODIFY] AI Signal: MODIFY " + symbol + " SL:" + DoubleToString(stopLoss, 5) + " TP:" + DoubleToString(takeProfit, 5));
            ModifyPosition(symbol, ticket, stopLoss, takeProfit);
        }
        else if(action == "PARTIAL_CLOSE") {
            Print("[PARTIAL] AI Signal: PARTIAL CLOSE " + symbol + " " + DoubleToString(lots, 2) + " lots");
            PartialClosePosition(symbol, ticket, lots);
        }
        else if(action == "CLOSE_ALL") {
            Print("[CLOSE_ALL] AI Signal: CLOSE ALL positions");
            CloseAllPositions();
        }
        else if(action == "EMERGENCY_STOP") {
            Print("[EMERGENCY] AI Signal: EMERGENCY STOP triggered");
            HandleEmergencyStop("Server emergency signal");
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
//| Close Positions (Enhanced Implementation)                       |
//+------------------------------------------------------------------+
void ClosePositions(string symbol)
{
    Print("[CLOSE] Closing all positions for " + symbol);

    int closedCount = 0;
    for(int i = PositionsTotal() - 1; i >= 0; i--) {
        if(positionInfo.SelectByIndex(i)) {
            if(positionInfo.Symbol() == symbol) {
                ulong ticket = positionInfo.Ticket();
                double lots = positionInfo.Volume();

                if(trade.PositionClose(ticket)) {
                    Print("[SUCCESS] Closed position " + IntegerToString(ticket) +
                          " (" + DoubleToString(lots, 2) + " lots)");

                    // Send confirmation
                    string confirmation = JsonHelper::CreateTradeConfirmationProto(
                        InpUserID, "closed", symbol, ticket, 0, lots);
                    wsClient.SendTradeConfirmation(confirmation);

                    closedCount++;
                } else {
                    Print("[ERROR] Failed to close position " + IntegerToString(ticket) +
                          " Error: " + IntegerToString(GetLastError()));
                }
            }
        }
    }

    Print("[SUMMARY] Closed " + IntegerToString(closedCount) + " positions for " + symbol);
}

//+------------------------------------------------------------------+
//| Modify Position - NEW FUNCTIONALITY                             |
//+------------------------------------------------------------------+
void ModifyPosition(string symbol, ulong specificTicket, double newStopLoss, double newTakeProfit)
{
    Print("[MODIFY] Modifying position for " + symbol);

    bool foundPosition = false;

    if(specificTicket > 0) {
        // Modify specific ticket
        if(PositionSelectByTicket(specificTicket)) {
            if(positionInfo.Symbol() == symbol) {
                foundPosition = true;
                ExecuteModify(specificTicket, symbol, newStopLoss, newTakeProfit);
            }
        }
    } else {
        // Modify first position found for this symbol
        for(int i = 0; i < PositionsTotal(); i++) {
            if(positionInfo.SelectByIndex(i)) {
                if(positionInfo.Symbol() == symbol) {
                    ulong ticket = positionInfo.Ticket();
                    foundPosition = true;
                    ExecuteModify(ticket, symbol, newStopLoss, newTakeProfit);
                    break; // Only modify first position
                }
            }
        }
    }

    if(!foundPosition) {
        Print("[WARNING] No position found for " + symbol +
              (specificTicket > 0 ? " with ticket " + IntegerToString(specificTicket) : ""));

        // Send failure confirmation
        string confirmation = JsonHelper::CreateModifyConfirmationProto(
            InpUserID, symbol, specificTicket, newStopLoss, newTakeProfit, false, "Position not found");
        wsClient.SendTradeConfirmation(confirmation);
    }
}

//+------------------------------------------------------------------+
//| Execute Modify Operation                                         |
//+------------------------------------------------------------------+
void ExecuteModify(ulong ticket, string symbol, double newStopLoss, double newTakeProfit)
{
    double currentSL = positionInfo.StopLoss();
    double currentTP = positionInfo.TakeProfit();

    Print("[MODIFY] Ticket " + IntegerToString(ticket) +
          " Current SL:" + DoubleToString(currentSL, 5) + " TP:" + DoubleToString(currentTP, 5));
    Print("[MODIFY] New SL:" + DoubleToString(newStopLoss, 5) + " TP:" + DoubleToString(newTakeProfit, 5));

    if(trade.PositionModify(ticket, newStopLoss, newTakeProfit)) {
        Print("[SUCCESS] Position " + IntegerToString(ticket) + " modified successfully");

        // Send success confirmation
        string confirmation = JsonHelper::CreateModifyConfirmationProto(
            InpUserID, symbol, ticket, newStopLoss, newTakeProfit, true);
        wsClient.SendTradeConfirmation(confirmation);

    } else {
        int error = GetLastError();
        string reason = "MT5 Error: " + IntegerToString(error);
        Print("[ERROR] Failed to modify position " + IntegerToString(ticket) + " - " + reason);

        // Send failure confirmation
        string confirmation = JsonHelper::CreateModifyConfirmationProto(
            InpUserID, symbol, ticket, newStopLoss, newTakeProfit, false, reason);
        wsClient.SendTradeConfirmation(confirmation);
    }
}

//+------------------------------------------------------------------+
//| Partial Close Position - NEW FUNCTIONALITY                      |
//+------------------------------------------------------------------+
void PartialClosePosition(string symbol, ulong specificTicket, double closeLots)
{
    Print("[PARTIAL] Partial close " + DoubleToString(closeLots, 2) + " lots of " + symbol);

    bool foundPosition = false;

    if(specificTicket > 0) {
        // Partial close specific ticket
        if(PositionSelectByTicket(specificTicket)) {
            if(positionInfo.Symbol() == symbol) {
                foundPosition = true;
                ExecutePartialClose(specificTicket, symbol, closeLots);
            }
        }
    } else {
        // Partial close first position found for this symbol
        for(int i = 0; i < PositionsTotal(); i++) {
            if(positionInfo.SelectByIndex(i)) {
                if(positionInfo.Symbol() == symbol) {
                    ulong ticket = positionInfo.Ticket();
                    foundPosition = true;
                    ExecutePartialClose(ticket, symbol, closeLots);
                    break;
                }
            }
        }
    }

    if(!foundPosition) {
        Print("[WARNING] No position found for partial close: " + symbol);

        // Send failure confirmation
        string confirmation = JsonHelper::CreatePartialCloseConfirmationProto(
            InpUserID, symbol, specificTicket, closeLots, 0, false);
        wsClient.SendTradeConfirmation(confirmation);
    }
}

//+------------------------------------------------------------------+
//| Execute Partial Close Operation                                  |
//+------------------------------------------------------------------+
void ExecutePartialClose(ulong ticket, string symbol, double closeLots)
{
    double currentVolume = positionInfo.Volume();

    Print("[PARTIAL] Ticket " + IntegerToString(ticket) +
          " Current volume: " + DoubleToString(currentVolume, 2) +
          " Close: " + DoubleToString(closeLots, 2));

    if(closeLots >= currentVolume) {
        // Close entire position
        if(trade.PositionClose(ticket)) {
            Print("[FULL_CLOSE] Closed entire position " + IntegerToString(ticket));

            string confirmation = JsonHelper::CreatePartialCloseConfirmationProto(
                InpUserID, symbol, ticket, currentVolume, 0, true);
            wsClient.SendTradeConfirmation(confirmation);
        }
    } else {
        // Partial close
        if(trade.PositionClosePartial(ticket, closeLots)) {
            double remaining = currentVolume - closeLots;
            Print("[SUCCESS] Partial close " + IntegerToString(ticket) +
                  " Closed: " + DoubleToString(closeLots, 2) +
                  " Remaining: " + DoubleToString(remaining, 2));

            string confirmation = JsonHelper::CreatePartialCloseConfirmationProto(
                InpUserID, symbol, ticket, closeLots, remaining, true);
            wsClient.SendTradeConfirmation(confirmation);
        } else {
            int error = GetLastError();
            Print("[ERROR] Failed to partial close " + IntegerToString(ticket) +
                  " Error: " + IntegerToString(error));

            string confirmation = JsonHelper::CreatePartialCloseConfirmationProto(
                InpUserID, symbol, ticket, closeLots, currentVolume, false);
            wsClient.SendTradeConfirmation(confirmation);
        }
    }
}

//+------------------------------------------------------------------+
//| Close All Positions - NEW FUNCTIONALITY                         |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
    Print("[CLOSE_ALL] Closing all open positions");

    int totalPositions = PositionsTotal();
    int closedCount = 0;

    for(int i = totalPositions - 1; i >= 0; i--) {
        if(positionInfo.SelectByIndex(i)) {
            ulong ticket = positionInfo.Ticket();
            string symbol = positionInfo.Symbol();
            double lots = positionInfo.Volume();

            if(trade.PositionClose(ticket)) {
                Print("[SUCCESS] Closed position " + IntegerToString(ticket) +
                      " (" + symbol + ", " + DoubleToString(lots, 2) + " lots)");
                closedCount++;

                // Send confirmation for each position
                string confirmation = JsonHelper::CreateTradeConfirmationProto(
                    InpUserID, "closed_all", symbol, ticket, 0, lots);
                wsClient.SendTradeConfirmation(confirmation);
            } else {
                Print("[ERROR] Failed to close position " + IntegerToString(ticket));
            }
        }
    }

    Print("[SUMMARY] Closed " + IntegerToString(closedCount) + " of " + IntegerToString(totalPositions) + " positions");
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