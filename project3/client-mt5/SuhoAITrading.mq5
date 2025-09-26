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
#include "JsonHelper.mqh"

//+------------------------------------------------------------------+
//| Input Parameters - Professional Settings Interface              |
//+------------------------------------------------------------------+

// === 🌐 SERVER CONNECTION ===
input group "🌐 ENHANCED SERVER CONNECTION"
input string    ServerURL = "ws://localhost:8001/ws/trading";    // │ Trading WebSocket URL
input string    AuthToken = "";                                    // │ JWT Authentication Token
input string    UserID = "user123";                             // │ Your unique User ID
input int       MagicNumber = 20241226;                           // │ EA Magic Number
input bool      TestingMode = true;                               // │ Enable for localhost testing

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

    // Initialize enhanced WebSocket client
    wsClient.SetServer(ServerURL, AuthToken, UserID);

    // Test dual connection
    if(!ConnectToServer()) {
        Print("⚠️ Initial dual connection failed - will retry");
        // Don't fail initialization, continue with retry logic
    }

    // Send account profile on startup
    if(wsClient.IsConnected()) {
        SendAccountProfile();
    }

    Print("✅ Suho AI Trading EA - Initialization completed successfully");
    Print("📊 Monitoring " + IntegerToString(ArraySize(TradingSymbols)) + " trading pairs");
    Print("🔗 Trading WebSocket: " + (wsClient.IsConnected() ? "Connected" : "Disconnected"));
    Print("📡 Price WebSocket: " + (wsClient.IsPriceStreamConnected() ? "Connected" : "Disconnected"));

    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                               |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🛑 Suho AI Trading EA - Shutting down...");

    // Send shutdown notification
    if(wsClient.IsConnected()) {
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
    // Enhanced dual connection health check
    if(TimeCurrent() - LastConnectionCheck > 30) {
        CheckServerConnection();
        LastConnectionCheck = TimeCurrent();
    }

    // Process incoming trading commands
    ProcessTradingCommands();

    // Price streaming via dedicated WebSocket
    if(wsClient.IsPriceStreamConnected()) {
        if(TimeCurrent() - LastPriceStream >= StreamingInterval / 1000) {
            StreamPricesToServer();
        }
    }

    // Check server for new commands (every 2 seconds)
    if(TimeCurrent() - LastCommandCheck >= 2) {
        CheckForServerCommands();
        LastCommandCheck = TimeCurrent();
    }

    // Periodic account updates
    static datetime lastAccountUpdate = 0;
    if(TimeCurrent() - lastAccountUpdate > 60) {
        SendAccountUpdate();
        lastAccountUpdate = TimeCurrent();
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
        string testUrl = "ws://localhost:8001/ws/trading";
        wsClient.SetServer(testUrl, AuthToken, UserID);
    } else {
        if(StringLen(AuthToken) == 0) {
            Print("❌ Auth token not configured for production");
            return false;
        }
    }

    Print("🔗 Attempting connection to server...");

    // Use enhanced WebSocket client connections
    bool connected = wsClient.ConnectToServer();

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
    if(!wsClient.IsHealthy()) {
        Print("🔄 Dual connection unhealthy, attempting to reconnect...");
        ConnectToServer();
    }

    // Log connection statistics for debugging
    if(wsClient.GetRetryCount() > 0) {
        Print("📊 Connection retries: " + IntegerToString(wsClient.GetRetryCount()));
    }

    // Show status periodically
    static datetime lastStatusLog = 0;
    if(TimeCurrent() - lastStatusLog > 300) {
        Print(wsClient.GetConnectionStats());
        lastStatusLog = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Send Account Profile to Server                                 |
//+------------------------------------------------------------------+
bool SendAccountProfile()
{
    if(!wsClient.IsConnected()) return false;

    Print("📤 Sending account profile via WebSocket...");

    // Create Protocol Buffers format profile data
    string profileProto = JsonHelper::CreateAccountProfileProto(UserID);

    // Add selected trading pairs to the proto
    if(ArraySize(TradingSymbols) > 0) {
        StringReplace(profileProto, "}", "");
        profileProto += ",\"trading_pairs\":[";
        for(int i = 0; i < ArraySize(TradingSymbols); i++) {
            if(i > 0) profileProto += ",";
            profileProto += "\"" + TradingSymbols[i] + "\"";
        }
        profileProto += "]}";
    }

    Print("📊 Profile data (Protocol Buffers): " + IntegerToString(StringLen(profileProto)) + " characters");

    // Send via enhanced WebSocket client
    return wsClient.SendAccountProfile(profileProto);
}

//+------------------------------------------------------------------+
//| Stream Current Prices to Server                                |
//+------------------------------------------------------------------+
bool StreamPricesToServer()
{
    if(!wsClient.IsPriceStreamConnected()) return false;

    // Create Protocol Buffers client price stream
    string priceStreamData = CreateClientPriceStream();
    int priceCount = GetPriceCount();

    // Update last stream time
    LastPriceStream = TimeCurrent();

    // Send via dedicated price WebSocket
    if(priceCount > 0) {
        bool success = wsClient.StreamPriceData(priceStreamData);
        if(success) {
            // Reduce log frequency
            static datetime lastLog = 0;
            if(TimeCurrent() - lastLog > 60) {
                Print("📡 Streaming " + IntegerToString(priceCount) + " pairs via price WebSocket");
                lastLog = TimeCurrent();
            }
        }
        return success;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Process queued trading commands                                 |
//+------------------------------------------------------------------+
void ProcessTradingCommands()
{
    // Process commands from WebSocket queue
    string command = wsClient.GetNextCommand();
    if(StringLen(command) > 0) {
        ExecuteTradingCommand(command);
    }
}

//+------------------------------------------------------------------+
//| Check server for new commands                                   |
//+------------------------------------------------------------------+
void CheckForServerCommands()
{
    if(!wsClient.IsConnected()) return;

    // Get new commands from server
    string commandsResponse = wsClient.GetServerCommands();

    if(StringLen(commandsResponse) > 0) {
        Print("📨 New server commands received");
        ExecuteTradingCommand(commandsResponse);
    }
}

//+------------------------------------------------------------------+
//| Execute AI trading command from server                          |
//+------------------------------------------------------------------+
void ExecuteTradingCommand(string commandJson)
{
    if(StringLen(commandJson) == 0) return;

    Print("🧠 Processing AI trading command (Protocol Buffers)...");

    // Parse Protocol Buffers command
    string action, symbol;
    double lots, stopLoss, takeProfit;

    if(JsonHelper::ParseTradingCommand(commandJson, action, symbol, lots, stopLoss, takeProfit)) {
        Print("📋 Command: " + action + " " + symbol + " " + DoubleToString(lots, 2) + " lots");

        // Check for price adjustment info
        string originalEntry = GetJsonValue(commandJson, "original_entry");
        string priceAdjustment = GetJsonValue(commandJson, "price_adjustment");

        if(StringLen(originalEntry) > 0 && StringLen(priceAdjustment) > 0) {
            Print("💱 Price adjusted from OANDA " + originalEntry + " (adjustment: " + priceAdjustment + ")");
        }

        // Execute command
        bool success = false;
        if(action == "BUY") {
            success = ExecuteBuyOrder(symbol, lots, stopLoss, takeProfit);
        } else if(action == "SELL") {
            success = ExecuteSellOrder(symbol, lots, stopLoss, takeProfit);
        } else if(action == "CLOSE") {
            success = ClosePositions(symbol);
        } else if(action == "CLOSE_ALL") {
            success = CloseAllPositions("Server Command");
        }

        // Send execution confirmation
        SendTradeConfirmation(action, symbol, lots, success);
    } else {
        Print("❌ Failed to parse Protocol Buffers command");
    }
}

//+------------------------------------------------------------------+
//| Execute Buy Order                                               |
//+------------------------------------------------------------------+
bool ExecuteBuyOrder(string symbol, double lots, double stopLoss, double takeProfit)
{
    if(!IsTradeAllowed() || !AutoTrading) {
        Print("❌ Trading not allowed");
        return false;
    }

    // Validate lot size
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
    lots = MathMax(minLot, MathMin(maxLot, lots));

    // Get current ask price
    double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
    if(ask <= 0) {
        Print("❌ Invalid ask price for " + symbol);
        return false;
    }

    // Execute buy order
    bool result = trade.Buy(lots, symbol, ask, stopLoss, takeProfit, "Suho AI Buy");

    if(result) {
        Print("✅ BUY executed: " + symbol + " " + DoubleToString(lots, 2) + " @ " + DoubleToString(ask, 5));
        TotalTrades++;
        return true;
    } else {
        Print("❌ BUY failed: " + symbol + " - Code " + IntegerToString(trade.ResultRetcode()));
        return false;
    }
}

//+------------------------------------------------------------------+
//| Execute Sell Order                                              |
//+------------------------------------------------------------------+
bool ExecuteSellOrder(string symbol, double lots, double stopLoss, double takeProfit)
{
    if(!IsTradeAllowed() || !AutoTrading) {
        Print("❌ Trading not allowed");
        return false;
    }

    // Validate lot size
    double minLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
    double maxLot = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
    lots = MathMax(minLot, MathMin(maxLot, lots));

    // Get current bid price
    double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
    if(bid <= 0) {
        Print("❌ Invalid bid price for " + symbol);
        return false;
    }

    // Execute sell order
    bool result = trade.Sell(lots, symbol, bid, stopLoss, takeProfit, "Suho AI Sell");

    if(result) {
        Print("✅ SELL executed: " + symbol + " " + DoubleToString(lots, 2) + " @ " + DoubleToString(bid, 5));
        TotalTrades++;
        return true;
    } else {
        Print("❌ SELL failed: " + symbol + " - Code " + IntegerToString(trade.ResultRetcode()));
        return false;
    }
}

//+------------------------------------------------------------------+
//| Close Positions for Symbol                                      |
//+------------------------------------------------------------------+
bool ClosePositions(string symbol)
{
    bool success = true;
    int closedCount = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--) {
        if(PositionGetSymbol(i) == symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber) {
            ulong ticket = PositionGetInteger(POSITION_TICKET);
            if(trade.PositionClose(ticket)) {
                Print("✅ Closed position " + IntegerToString(ticket) + " for " + symbol);
                closedCount++;
            } else {
                Print("❌ Failed to close position " + IntegerToString(ticket));
                success = false;
            }
        }
    }

    if(closedCount > 0) {
        Print("🔒 Closed " + IntegerToString(closedCount) + " positions for " + symbol);
    }

    return success;
}

//+------------------------------------------------------------------+
//| Close All Positions                                             |
//+------------------------------------------------------------------+
bool CloseAllPositions(string reason)
{
    Print("🚨 Closing all positions: " + reason);
    bool success = true;
    int closedCount = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--) {
        if(PositionGetInteger(POSITION_MAGIC) == MagicNumber) {
            ulong ticket = PositionGetInteger(POSITION_TICKET);
            string symbol = PositionGetString(POSITION_SYMBOL);
            if(trade.PositionClose(ticket)) {
                Print("✅ Closed position " + IntegerToString(ticket) + " (" + symbol + ")");
                closedCount++;
            } else {
                Print("❌ Failed to close position " + IntegerToString(ticket));
                success = false;
            }
        }
    }

    Print("🔒 Total positions closed: " + IntegerToString(closedCount));
    return success;
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

    // Send via WebSocket client
    wsClient.SendTradeConfirmation(shutdownProto);
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
    Print("🔗 Trading WebSocket: " + (wsClient.IsConnected() ? "Connected" : "Disconnected"));
    Print("📡 Price WebSocket: " + (wsClient.IsPriceStreamConnected() ? "Connected" : "Disconnected"));
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