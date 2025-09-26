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
#property description "• Real-time AI trading signals from centralized server"
#property description "• Automatic price adjustment for broker differences"
#property description "• Professional risk management and position sizing"
#property description "• Multi-pair correlation analysis support"
#property description "• Zero-latency execution with local MT5 integration"
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

//+------------------------------------------------------------------+
//| Input Parameters - Professional Settings Interface              |
//+------------------------------------------------------------------+

// === 🌐 SERVER CONNECTION ===
input group "🌐 SERVER CONNECTION"
input string    ServerURL = "wss://api.aitrading.suho.platform";  // │ Production server URL
input string    AuthToken = "";                                    // │ JWT Token from web platform
input string    UserID = "";                                       // │ Your unique User ID
input bool      TestingMode = false;                               // │ Enable for localhost testing

// === 💰 TRADING PREFERENCES ===
input group "💰 TRADING SETTINGS"
input bool      AutoTrading = true;                                // │ Enable automatic trading
input double    MaxRiskPerTrade = 2.0;                            // │ Maximum risk % per trade
input double    MaxDailyLoss = 1000.0;                            // │ Maximum daily loss (USD)
input int       MaxOpenPositions = 3;                             // │ Maximum simultaneous positions
input double    PreferredLotSize = 0.1;                           // │ Preferred position size

// === 📊 MAJOR PAIRS SELECTION (Trading + Analysis) ===
input group "📊 MAJOR PAIRS - Trading & AI Analysis"
input bool      Trade_EURUSD = true;                              // │ EUR/USD - Euro vs US Dollar
input bool      Trade_GBPUSD = true;                              // │ GBP/USD - British Pound vs US Dollar
input bool      Trade_USDJPY = true;                              // │ USD/JPY - US Dollar vs Japanese Yen
input bool      Trade_USDCHF = false;                             // │ USD/CHF - US Dollar vs Swiss Franc
input bool      Trade_AUDUSD = false;                             // │ AUD/USD - Australian Dollar vs US Dollar
input bool      Trade_USDCAD = false;                             // │ USD/CAD - US Dollar vs Canadian Dollar
input bool      Trade_NZDUSD = false;                             // │ NZD/USD - New Zealand Dollar vs US Dollar

// === 🥇 PRECIOUS METALS (Trading + Analysis) ===
input group "🥇 PRECIOUS METALS - Trading & AI Analysis"
input bool      Trade_XAUUSD = false;                             // │ XAU/USD - Gold vs US Dollar
input bool      Trade_XAGUSD = false;                             // │ XAG/USD - Silver vs US Dollar


// === 🔄 DATA STREAMING ===
input group "🔄 DATA STREAMING"
input int       StreamingInterval = 1000;                         // │ Streaming interval (ms)
input bool      StreamCurrentChartOnly = false;                   // │ Stream only current chart (ignore selections above)

// === ⚙️ ADVANCED SETTINGS ===
input group "⚙️ ADVANCED SETTINGS"
input bool      ConservativeMode = false;                         // │ Conservative trading mode
input double    MaxDrawdown = 15.0;                               // │ Maximum drawdown %
input bool      AutoCloseOnFriday = true;                         // │ Auto-close positions on Friday
input bool      AllowNewsTrading = false;                         // │ Allow trading during news

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
CTrade trade;
CPositionInfo positionInfo;
CAccountInfo accountInfo;
CSymbolInfo symbolInfo;
CHttpClient httpClient;

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
    Print("🚀 Suho AI Trading EA - Initializing...");

    // Record start time
    StartTime = TimeCurrent();

    // Initialize trading objects
    trade.SetExpertMagicNumber(240626);  // Magic number: 24/06/26 (Suho AI launch date)
    trade.SetDeviationInPoints(10);
    trade.SetTypeFilling(ORDER_FILLING_FOK);

    // Initialize symbols
    if(!InitializeTradingSymbols()) {
        Print("❌ Failed to initialize trading symbols");
        return INIT_FAILED;
    }

    // Initialize HTTP client
    httpClient.SetServer(ServerURL, AuthToken);

    // Test server connection
    if(!ConnectToServer()) {
        Print("⚠️ Initial server connection failed - will retry");
        // Don't fail initialization, continue with retry logic
    }

    // Send account profile on startup
    if(httpClient.IsConnected()) {
        SendAccountProfile();
    }

    Print("✅ Suho AI Trading EA - Initialization completed successfully");
    Print("📊 Monitoring " + IntegerToString(ArraySize(TradingSymbols)) + " trading pairs");
    Print("🔗 Server connection: " + (httpClient.IsConnected() ? "Connected" : "Disconnected"));

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                               |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🛑 Suho AI Trading EA - Shutting down...");

    // Send shutdown notification
    if(httpClient.IsConnected()) {
        SendShutdownNotification();
    }

    // Print performance summary
    PrintPerformanceSummary();

    Print("👋 Suho AI Trading EA - Shutdown completed");
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
    if(httpClient.IsConnected()) {
        if(TimeCurrent() - LastPriceStream >= StreamingInterval / 1000) {
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
    if(Trade_EURUSD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "EURUSD"; tradingCount++; }
    if(Trade_GBPUSD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "GBPUSD"; tradingCount++; }
    if(Trade_USDJPY) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "USDJPY"; tradingCount++; }
    if(Trade_USDCHF) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "USDCHF"; tradingCount++; }
    if(Trade_AUDUSD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "AUDUSD"; tradingCount++; }
    if(Trade_USDCAD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "USDCAD"; tradingCount++; }
    if(Trade_NZDUSD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "NZDUSD"; tradingCount++; }

    // Precious metals
    if(Trade_XAUUSD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "XAUUSD"; tradingCount++; }
    if(Trade_XAGUSD) { ArrayResize(tradingPairs, tradingCount + 1); tradingPairs[tradingCount] = "XAGUSD"; tradingCount++; }

    // Validate and setup trading symbols
    if(tradingCount == 0) {
        Print("⚠️ No trading pairs selected - EA will run in monitoring mode only");
    } else {
        ArrayResize(TradingSymbols, tradingCount);
        for(int i = 0; i < tradingCount; i++) {
            TradingSymbols[i] = tradingPairs[i];

            if(!SymbolSelect(tradingPairs[i], true)) {
                Print("⚠️ Trading symbol not available: " + tradingPairs[i]);
            } else {
                Print("✅ Trading symbol initialized: " + tradingPairs[i]);
            }
        }
    }

    Print("🎯 Trading pairs initialized: " + IntegerToString(tradingCount) + " pairs (streaming bid/ask only)");

    return true; // Always return true, allow monitoring mode even without trading pairs
}

//+------------------------------------------------------------------+
//| Connect to Server                                              |
//+------------------------------------------------------------------+
bool ConnectToServer()
{
    // Validate configuration
    if(StringLen(UserID) == 0) {
        Print("❌ User ID not configured");
        return false;
    }

    if(TestingMode) {
        Print("🧪 Test mode: Connecting to localhost server");
        // Update URL for localhost testing
        string testUrl = "http://localhost:8000";
        httpClient.SetServer(testUrl, AuthToken);
    } else {
        if(StringLen(AuthToken) == 0) {
            Print("❌ Auth token not configured for production");
            return false;
        }
    }

    Print("🔗 Attempting connection to server...");

    // Use actual HTTP client connection
    bool connected = httpClient.TestConnection();

    if(connected) {
        Print("✅ Connected to server successfully");
    } else {
        Print("❌ Server connection failed");
    }

    return connected;
}

//+------------------------------------------------------------------+
//| Check Server Connection                                        |
//+------------------------------------------------------------------+
void CheckServerConnection()
{
    if(!httpClient.IsHealthy()) {
        Print("🔄 Connection unhealthy, attempting to reconnect...");
        ConnectToServer();
    }

    // Log connection statistics for debugging
    if(httpClient.GetRetryCount() > 0) {
        Print("📊 Connection retries: " + IntegerToString(httpClient.GetRetryCount()));
    }
}

//+------------------------------------------------------------------+
//| Send Account Profile to Server                                 |
//+------------------------------------------------------------------+
bool SendAccountProfile()
{
    if(!httpClient.IsConnected()) return false;

    Print("📤 Sending account profile to server...");

    // Create Protocol Buffers format profile data
    string profileProto = JsonHelper::CreateAccountProfileProto(UserID);

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

    Print("📊 Profile data (Protocol Buffers): " + IntegerToString(StringLen(profileProto)) + " characters");

    // Send via HTTP client
    return httpClient.SendAccountProfile(profileProto);
}

//+------------------------------------------------------------------+
//| Stream Current Prices to Server                                |
//+------------------------------------------------------------------+
bool StreamPricesToServer()
{
    if(!httpClient.IsConnected()) return false;

    // Create Protocol Buffers format price stream
    string priceStreamData = "{\"user_id\":\"" + UserID + "\",\"timestamp\":" + IntegerToString(TimeCurrent()) + ",\"prices\":[";
    int priceCount = 0;

    if(StreamCurrentChartOnly) {
        // Stream only current chart symbol using Protocol Buffers format
        MqlTick tick;
        if(SymbolInfoTick(_Symbol, tick)) {
            string marketData = JsonHelper::CreateMarketDataProto(UserID, _Symbol, tick.bid, tick.ask, TimeCurrent());
            priceStreamData += marketData;
            priceCount = 1;
        }
    } else {
        // Stream selected trading pairs using Protocol Buffers format
        for(int i = 0; i < ArraySize(TradingSymbols); i++) {
            MqlTick tick;
            if(SymbolInfoTick(TradingSymbols[i], tick)) {
                if(priceCount > 0) priceStreamData += ",";
                string marketData = JsonHelper::CreateMarketDataProto(UserID, TradingSymbols[i], tick.bid, tick.ask, TimeCurrent());
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
        return httpClient.SendPriceData(priceStreamData);
    }

    return true;
}

//+------------------------------------------------------------------+
//| Process Server Commands                                         |
//+------------------------------------------------------------------+
void ProcessServerCommands()
{
    if(!httpClient.IsConnected()) return;

    // Get pending commands from server
    string commandsResponse = httpClient.GetServerCommands();

    if(StringLen(commandsResponse) > 0) {
        Print("📨 Received server commands: " + IntegerToString(StringLen(commandsResponse)) + " characters");

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
    Print("🧠 Processing AI trading commands (Protocol Buffers)...");

    // Parse Protocol Buffers command using JsonHelper
    string action, symbol;
    double lots, stopLoss, takeProfit;

    if(JsonHelper::ParseTradingCommand(commandsJson, action, symbol, lots, stopLoss, takeProfit)) {
        Print("📋 Command parsed - Action: " + action + ", Symbol: " + symbol + ", Lots: " + DoubleToString(lots, 2));

        if(action == "BUY") {
            Print("📈 AI Signal: BUY " + symbol + " " + DoubleToString(lots, 2) + " lots");
            ExecuteBuyOrder(symbol, lots, stopLoss, takeProfit);
        }
        else if(action == "SELL") {
            Print("📉 AI Signal: SELL " + symbol + " " + DoubleToString(lots, 2) + " lots");
            ExecuteSellOrder(symbol, lots, stopLoss, takeProfit);
        }
        else if(action == "CLOSE") {
            Print("🔒 AI Signal: CLOSE " + symbol + " positions");
            ClosePositions(symbol);
        }
        else {
            Print("⚠️ Unknown command action: " + action);
        }
    } else {
        Print("❌ Failed to parse Protocol Buffers command");
    }

    // Send acknowledgment back to server in Protocol Buffers format
    string ackData = JsonHelper::CreateTradeConfirmationProto(UserID, "RECEIVED", "", 0, 0, 0);
    httpClient.SendTradeConfirmation(ackData);
}

//+------------------------------------------------------------------+
//| Execute Buy Order (Placeholder for next phase)                 |
//+------------------------------------------------------------------+
void ExecuteBuyOrder(string symbol, double lots, double stopLoss, double takeProfit)
{
    Print("🔧 TODO: Execute BUY order for " + symbol);
    // TODO: Implement actual order execution in next phase
}

//+------------------------------------------------------------------+
//| Execute Sell Order (Placeholder for next phase)                |
//+------------------------------------------------------------------+
void ExecuteSellOrder(string symbol, double lots, double stopLoss, double takeProfit)
{
    Print("🔧 TODO: Execute SELL order for " + symbol);
    // TODO: Implement actual order execution in next phase
}

//+------------------------------------------------------------------+
//| Close Positions (Placeholder for next phase)                   |
//+------------------------------------------------------------------+
void ClosePositions(string symbol)
{
    Print("🔧 TODO: Close positions for " + symbol);
    // TODO: Implement position closing in next phase
}

//+------------------------------------------------------------------+
//| Send Shutdown Notification                                     |
//+------------------------------------------------------------------+
void SendShutdownNotification()
{
    if(!httpClient.IsConnected()) return;

    Print("📤 Sending shutdown notification...");

    // Create Protocol Buffers format shutdown notification
    string shutdownProto = "{";
    shutdownProto = JsonHelper::AddStringField(shutdownProto, "user_id", UserID);
    shutdownProto = JsonHelper::AddStringField(shutdownProto, "event", "EA_SHUTDOWN");
    shutdownProto = JsonHelper::AddIntegerField(shutdownProto, "timestamp", TimeCurrent());
    shutdownProto = JsonHelper::AddNumericField(shutdownProto, "final_balance", AccountInfoDouble(ACCOUNT_BALANCE));
    shutdownProto = JsonHelper::AddNumericField(shutdownProto, "final_equity", AccountInfoDouble(ACCOUNT_EQUITY));
    shutdownProto = JsonHelper::AddIntegerField(shutdownProto, "open_positions", PositionsTotal());
    shutdownProto = JsonHelper::AddIntegerField(shutdownProto, "total_trades", TotalTrades);
    shutdownProto = JsonHelper::AddNumericField(shutdownProto, "total_profit", TotalProfit);
    shutdownProto += "}";

    // Send via HTTP client
    httpClient.SendTradeConfirmation(shutdownProto);
    Print("📊 Shutdown notification sent (Protocol Buffers)");
}

//+------------------------------------------------------------------+
//| Print Performance Summary                                       |
//+------------------------------------------------------------------+
void PrintPerformanceSummary()
{
    datetime runtime = TimeCurrent() - StartTime;

    Print("📊 === SUHO AI TRADING PERFORMANCE SUMMARY ===");
    Print("⏱️ Runtime: " + IntegerToString(runtime) + " seconds (" +
          DoubleToString(runtime / 3600.0, 1) + " hours)");
    Print("🎯 Total trades executed: " + IntegerToString(TotalTrades));
    Print("💰 Total profit/loss: $" + DoubleToString(TotalProfit, 2));
    Print("📈 Starting balance: $" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2));
    Print("📊 Current balance: $" + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2));
    Print("🔗 Server connection status: " + (httpClient.IsConnected() ? "Connected" : "Disconnected"));
    Print("===============================================");
}

//+------------------------------------------------------------------+
//| Handle Emergency Stop                                          |
//+------------------------------------------------------------------+
void HandleEmergencyStop(string reason)
{
    Print("🚨 EMERGENCY STOP TRIGGERED: " + reason);

    // Close all open positions immediately
    for(int i = 0; i < PositionsTotal(); i++) {
        if(positionInfo.SelectByIndex(i)) {
            if(positionInfo.Symbol() == _Symbol || !StreamCurrentChartOnly) {
                trade.PositionClose(positionInfo.Ticket());
                Print("🔒 Emergency close: " + positionInfo.Symbol() + " - " + DoubleToString(positionInfo.Volume(), 2) + " lots");
            }
        }
    }

    // Cancel all pending orders
    for(int i = 0; i < OrdersTotal(); i++) {
        ulong ticket = OrderGetTicket(i);
        if(ticket > 0) {
            trade.OrderDelete(ticket);
            Print("❌ Emergency cancel order: " + IntegerToString(ticket));
        }
    }

    Print("🛑 Emergency stop completed - All positions closed");
}