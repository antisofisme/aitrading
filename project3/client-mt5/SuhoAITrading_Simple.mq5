//+------------------------------------------------------------------+
//|                                     Suho AI Trading - Simple.mq5 |
//|                                    Copyright 2024, AI Trading Platform |
//|                                       https://aitrading.suho.platform |
//+------------------------------------------------------------------+
#property copyright "2024, AI Trading Platform"
#property link      "https://aitrading.suho.platform"
#property version   "2.00"
#property description "Suho AI Trading - Enhanced Dual WebSocket Trading System"
#property description "Server-side AI analysis with client-side execution"

//+------------------------------------------------------------------+
//| Include Libraries                                                |
//+------------------------------------------------------------------+
#include <Trade/Trade.mqh>
#include "WebSocketClient.mqh"
#include "JsonHelper.mqh"

//+------------------------------------------------------------------+
//| Input Parameters                                                 |
//+------------------------------------------------------------------+
input group "🌐 ENHANCED SERVER CONNECTION"
input string    ServerURL     = "ws://localhost:8001/ws/trading";    // Trading WebSocket URL
input string    AuthToken     = "";                                  // JWT Authentication Token
input string    UserID        = "user123";                           // User Identifier
input int       MagicNumber   = 20241226;                           // EA Magic Number
input bool      TestingMode   = true;                               // Enable for localhost testing

input group "💰 TRADING SETTINGS"
input bool      AutoTrading   = true;                               // Enable automatic trading
input double    MaxRiskPerTrade = 2.0;                              // Maximum risk % per trade
input int       MaxOpenPositions = 3;                               // Maximum simultaneous positions

input group "📊 MAJOR PAIRS - Trading & AI Analysis"
input bool      Trade_EURUSD  = true;                               // EUR/USD - Euro vs US Dollar
input bool      Trade_GBPUSD  = true;                               // GBP/USD - British Pound vs US Dollar
input bool      Trade_USDJPY  = true;                               // USD/JPY - US Dollar vs Japanese Yen
input bool      Trade_USDCHF  = false;                              // USD/CHF - US Dollar vs Swiss Franc
input bool      Trade_AUDUSD  = false;                              // AUD/USD - Australian Dollar vs US Dollar

input group "🔄 DATA STREAMING"
input int       StreamingInterval = 1000;                           // Streaming interval (ms)
input bool      StreamCurrentChartOnly = false;                     // Stream only current chart

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
CTrade trade;
CWebSocketClient wsClient;

string TradingSymbols[];
datetime LastConnectionCheck = 0;
datetime LastPriceStream = 0;
datetime LastCommandCheck = 0;
int TotalTrades = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("🚀 Suho AI Trading v2.00 - Initializing...");

    // Initialize trading object
    trade.SetExpertMagicNumber(MagicNumber);
    trade.SetDeviationInPoints(10);

    // Initialize trading symbols
    InitializeTradingSymbols();

    // Initialize WebSocket client
    wsClient.SetServer(ServerURL, AuthToken, UserID);

    // Connect to server
    if(wsClient.ConnectToServer()) {
        Print("✅ Dual WebSocket connections established");
        SendAccountProfile();
    } else {
        Print("⚠️ Connection failed - will retry");
    }

    Print("✅ Initialization completed");
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                               |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("🛑 Suho AI Trading v2.00 - Shutting down...");

    if(wsClient.IsConnected()) {
        SendShutdownNotification();
    }

    if(AutoTrading) {
        CloseAllPositions("EA Shutdown");
    }

    Print("👋 Shutdown completed");
}

//+------------------------------------------------------------------+
//| Expert tick function                                            |
//+------------------------------------------------------------------+
void OnTick()
{
    // Health check every 30 seconds
    if(TimeCurrent() - LastConnectionCheck > 30) {
        CheckServerConnection();
        LastConnectionCheck = TimeCurrent();
    }

    // Process trading commands
    ProcessTradingCommands();

    // Price streaming every second
    if(wsClient.IsPriceStreamConnected() && TimeCurrent() - LastPriceStream >= StreamingInterval / 1000) {
        StreamPricesToServer();
        LastPriceStream = TimeCurrent();
    }

    // Check for new commands every 2 seconds
    if(TimeCurrent() - LastCommandCheck >= 2) {
        CheckForServerCommands();
        LastCommandCheck = TimeCurrent();
    }
}

//+------------------------------------------------------------------+
//| Initialize Trading Symbols                                      |
//+------------------------------------------------------------------+
void InitializeTradingSymbols()
{
    string tempSymbols[];
    int count = 0;

    if(Trade_EURUSD) { ArrayResize(tempSymbols, count + 1); tempSymbols[count] = "EURUSD"; count++; }
    if(Trade_GBPUSD) { ArrayResize(tempSymbols, count + 1); tempSymbols[count] = "GBPUSD"; count++; }
    if(Trade_USDJPY) { ArrayResize(tempSymbols, count + 1); tempSymbols[count] = "USDJPY"; count++; }
    if(Trade_USDCHF) { ArrayResize(tempSymbols, count + 1); tempSymbols[count] = "USDCHF"; count++; }
    if(Trade_AUDUSD) { ArrayResize(tempSymbols, count + 1); tempSymbols[count] = "AUDUSD"; count++; }

    ArrayResize(TradingSymbols, count);
    for(int i = 0; i < count; i++) {
        TradingSymbols[i] = tempSymbols[i];
        SymbolSelect(tempSymbols[i], true);
    }

    Print("🎯 Trading pairs initialized: " + IntegerToString(count) + " pairs");
}

//+------------------------------------------------------------------+
//| Check Server Connection                                         |
//+------------------------------------------------------------------+
void CheckServerConnection()
{
    if(!wsClient.IsHealthy()) {
        Print("🔄 Connection unhealthy, reconnecting...");
        wsClient.ConnectToServer();
    }
}

//+------------------------------------------------------------------+
//| Send Account Profile                                            |
//+------------------------------------------------------------------+
void SendAccountProfile()
{
    if(!wsClient.IsConnected()) return;

    string profileProto = JsonHelper::CreateAccountProfileProto(UserID);
    if(wsClient.SendAccountProfile(profileProto)) {
        Print("📤 Account profile sent");
    }
}

//+------------------------------------------------------------------+
//| Stream Prices to Server                                         |
//+------------------------------------------------------------------+
void StreamPricesToServer()
{
    if(!wsClient.IsPriceStreamConnected()) return;

    string priceData = CreatePriceStream();
    if(wsClient.StreamPriceData(priceData)) {
        static datetime lastLog = 0;
        if(TimeCurrent() - lastLog > 60) {
            Print("📡 Price streaming active");
            lastLog = TimeCurrent();
        }
    }
}

//+------------------------------------------------------------------+
//| Create Price Stream Data                                        |
//+------------------------------------------------------------------+
string CreatePriceStream()
{
    string data = "{\"user_id\":\"" + UserID + "\",\"prices\":[";
    int count = 0;

    for(int i = 0; i < ArraySize(TradingSymbols); i++) {
        MqlTick tick;
        if(SymbolInfoTick(TradingSymbols[i], tick)) {
            if(count > 0) data += ",";
            data += "{\"symbol\":\"" + TradingSymbols[i] + "\"";
            data += ",\"bid\":" + DoubleToString(tick.bid, 5);
            data += ",\"ask\":" + DoubleToString(tick.ask, 5) + "}";
            count++;
        }
    }

    data += "]}";
    return data;
}

//+------------------------------------------------------------------+
//| Process Trading Commands                                        |
//+------------------------------------------------------------------+
void ProcessTradingCommands()
{
    string command = wsClient.GetNextCommand();
    if(StringLen(command) > 0) {
        ExecuteTradingCommand(command);
    }
}

//+------------------------------------------------------------------+
//| Check for Server Commands                                       |
//+------------------------------------------------------------------+
void CheckForServerCommands()
{
    if(!wsClient.IsConnected()) return;

    string response = wsClient.GetServerCommands();
    if(StringLen(response) > 0) {
        ExecuteTradingCommand(response);
    }
}

//+------------------------------------------------------------------+
//| Execute Trading Command                                         |
//+------------------------------------------------------------------+
void ExecuteTradingCommand(string commandJson)
{
    if(StringLen(commandJson) == 0) return;

    Print("🧠 Processing AI command");

    // Simple JSON parsing
    string action = "", symbol = "";
    double lots = 0;

    if(StringFind(commandJson, "BUY") != -1) action = "BUY";
    else if(StringFind(commandJson, "SELL") != -1) action = "SELL";
    else if(StringFind(commandJson, "CLOSE") != -1) action = "CLOSE";

    if(StringFind(commandJson, "EURUSD") != -1) symbol = "EURUSD";
    else if(StringFind(commandJson, "GBPUSD") != -1) symbol = "GBPUSD";
    else if(StringFind(commandJson, "USDJPY") != -1) symbol = "USDJPY";

    lots = 0.1; // Default lot size

    bool success = false;
    if(action == "BUY") {
        success = ExecuteBuyOrder(symbol, lots);
    } else if(action == "SELL") {
        success = ExecuteSellOrder(symbol, lots);
    } else if(action == "CLOSE") {
        success = ClosePositions(symbol);
    }

    SendTradeConfirmation(action, symbol, lots, success);
}

//+------------------------------------------------------------------+
//| Execute Buy Order                                               |
//+------------------------------------------------------------------+
bool ExecuteBuyOrder(string symbol, double lots)
{
    if(!AutoTrading || !IsTradeAllowed()) return false;

    double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
    if(ask <= 0) return false;

    bool result = trade.Buy(lots, symbol, ask, 0, 0, "Suho AI Buy");
    if(result) {
        Print("✅ BUY executed: " + symbol + " " + DoubleToString(lots, 2));
        TotalTrades++;
    }
    return result;
}

//+------------------------------------------------------------------+
//| Execute Sell Order                                              |
//+------------------------------------------------------------------+
bool ExecuteSellOrder(string symbol, double lots)
{
    if(!AutoTrading || !IsTradeAllowed()) return false;

    double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
    if(bid <= 0) return false;

    bool result = trade.Sell(lots, symbol, bid, 0, 0, "Suho AI Sell");
    if(result) {
        Print("✅ SELL executed: " + symbol + " " + DoubleToString(lots, 2));
        TotalTrades++;
    }
    return result;
}

//+------------------------------------------------------------------+
//| Close Positions                                                 |
//+------------------------------------------------------------------+
bool ClosePositions(string symbol)
{
    bool success = true;
    int closed = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--) {
        if(PositionGetSymbol(i) == symbol && PositionGetInteger(POSITION_MAGIC) == MagicNumber) {
            ulong ticket = PositionGetInteger(POSITION_TICKET);
            if(trade.PositionClose(ticket)) {
                closed++;
            } else {
                success = false;
            }
        }
    }

    if(closed > 0) {
        Print("🔒 Closed " + IntegerToString(closed) + " positions for " + symbol);
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
    int closed = 0;

    for(int i = PositionsTotal() - 1; i >= 0; i--) {
        if(PositionGetInteger(POSITION_MAGIC) == MagicNumber) {
            ulong ticket = PositionGetInteger(POSITION_TICKET);
            if(trade.PositionClose(ticket)) {
                closed++;
            } else {
                success = false;
            }
        }
    }

    Print("🔒 Total positions closed: " + IntegerToString(closed));
    return success;
}

//+------------------------------------------------------------------+
//| Send Trade Confirmation                                         |
//+------------------------------------------------------------------+
void SendTradeConfirmation(string action, string symbol, double lots, bool success)
{
    string status = success ? "executed" : "failed";
    ulong ticket = success ? trade.ResultOrder() : 0;

    string confirmation = JsonHelper::CreateTradeConfirmationProto(UserID, status, symbol, ticket, 0, lots);
    wsClient.SendTradeConfirmation(confirmation);

    Print("📤 Confirmation sent: " + action + " " + symbol + " - " + status);
}

//+------------------------------------------------------------------+
//| Send Shutdown Notification                                      |
//+------------------------------------------------------------------+
void SendShutdownNotification()
{
    string shutdownData = "{\"user_id\":\"" + UserID + "\",\"event\":\"EA_SHUTDOWN\",\"total_trades\":" + IntegerToString(TotalTrades) + "}";
    wsClient.SendTradeConfirmation(shutdownData);
    Print("📤 Shutdown notification sent");
}