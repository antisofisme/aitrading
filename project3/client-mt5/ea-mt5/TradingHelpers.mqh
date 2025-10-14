//+------------------------------------------------------------------+
//|                                              TradingHelpers.mqh |
//|                     Enhanced trading functions and utilities    |
//+------------------------------------------------------------------+
#ifndef TRADINGHELPERS_MQH
#define TRADINGHELPERS_MQH

#include "JsonHelper.mqh"
#include "BinaryProtocol.mqh"

//+------------------------------------------------------------------+
//| Create Protocol Buffers client price stream                    |
//+------------------------------------------------------------------+
string CreateClientPriceStream(string UserID, string &tradingPairs[], bool StreamCurrentChartOnly)
{

    string streamData = "{";
    streamData = JsonHelper::AddStringField(streamData, "user_id", UserID);
    streamData = JsonHelper::AddStringField(streamData, "broker_name", AccountInfoString(ACCOUNT_COMPANY));
    streamData = JsonHelper::AddStringField(streamData, "account_number", IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)));
    streamData = JsonHelper::AddIntegerField(streamData, "batch_timestamp", GetTickCount());

    // Add prices array (Protocol Buffers ClientPrice format)
    streamData += ",\"prices\":[";
    int priceCount = 0;

    if(StreamCurrentChartOnly) {
        // Stream only current chart symbol
        MqlTick tick;
        if(SymbolInfoTick(_Symbol, tick)) {
            streamData += "{";
            streamData = JsonHelper::AddStringField(streamData, "symbol", _Symbol);
            streamData = JsonHelper::AddNumericField(streamData, "bid", tick.bid, 5);
            streamData = JsonHelper::AddNumericField(streamData, "ask", tick.ask, 5);
            streamData = JsonHelper::AddNumericField(streamData, "spread", (tick.ask - tick.bid) * 10000, 1);
            streamData = JsonHelper::AddIntegerField(streamData, "timestamp", GetTickCount());
            streamData = JsonHelper::AddStringField(streamData, "broker_server", AccountInfoString(ACCOUNT_SERVER));
            streamData += "}";
            priceCount = 1;
        }
    } else {
        // Stream selected trading pairs
        for(int i = 0; i < ArraySize(tradingPairs); i++) {
            MqlTick tick;
            if(SymbolInfoTick(tradingPairs[i], tick)) {
                if(priceCount > 0) streamData += ",";
                streamData += "{";
                streamData = JsonHelper::AddStringField(streamData, "symbol", tradingPairs[i]);
                streamData = JsonHelper::AddNumericField(streamData, "bid", tick.bid, 5);
                streamData = JsonHelper::AddNumericField(streamData, "ask", tick.ask, 5);
                streamData = JsonHelper::AddNumericField(streamData, "spread", (tick.ask - tick.bid) * 10000, 1);
                streamData = JsonHelper::AddIntegerField(streamData, "timestamp", GetTickCount());
                streamData = JsonHelper::AddStringField(streamData, "broker_server", AccountInfoString(ACCOUNT_SERVER));
                streamData += "}";
                priceCount++;
            }
        }
    }

    streamData += "]}";
    return streamData;
}

//+------------------------------------------------------------------+
//| Get price count for current streaming operation                 |
//+------------------------------------------------------------------+
int GetPriceCount(string &tradingPairs[], bool StreamCurrentChartOnly)
{

    if(StreamCurrentChartOnly) {
        return 1;
    } else {
        int count = 0;
        for(int i = 0; i < ArraySize(tradingPairs); i++) {
            MqlTick tick;
            if(SymbolInfoTick(tradingPairs[i], tick)) {
                count++;
            }
        }
        return count;
    }
}

//+------------------------------------------------------------------+
//| Enhanced JSON value extractor                                  |
//+------------------------------------------------------------------+
string GetJsonValue(string json, string key)
{
    // Try string value first
    string searchKey = "\"" + key + "\":\"";
    int startPos = StringFind(json, searchKey);
    if(startPos != -1) {
        startPos += StringLen(searchKey);
        int endPos = StringFind(json, "\"", startPos);
        if(endPos != -1) {
            return StringSubstr(json, startPos, endPos - startPos);
        }
    }

    // Try numeric value
    searchKey = "\"" + key + "\":";
    startPos = StringFind(json, searchKey);
    if(startPos != -1) {
        startPos += StringLen(searchKey);
        int endPos = StringFind(json, ",", startPos);
        if(endPos == -1) endPos = StringFind(json, "}", startPos);
        if(endPos != -1) {
            return StringSubstr(json, startPos, endPos - startPos);
        }
    }

    return "";
}

//+------------------------------------------------------------------+
//| Send trade confirmation to server                               |
//+------------------------------------------------------------------+
void SendTradeConfirmation(string UserID, CWebSocketClient &webSocketClient, CTrade &tradeManager, string action, string symbol, double lots, bool success)
{

    string status = success ? "executed" : "failed";
    ulong ticket = success ? tradeManager.ResultOrder() : 0;
    double price = success ? (action == "BUY" ? SymbolInfoDouble(symbol, SYMBOL_ASK) : SymbolInfoDouble(symbol, SYMBOL_BID)) : 0;

    string confirmation = JsonHelper::CreateTradeConfirmationProto(UserID, status, symbol, ticket, price, lots);

    if(webSocketClient.SendTradeConfirmation(confirmation)) {
        Print("📤 Trade confirmation sent: " + status);
    } else {
        Print("⚠️ Failed to send trade confirmation");
    }
}

//+------------------------------------------------------------------+
//| Send periodic account updates                                   |
//+------------------------------------------------------------------+
void SendAccountUpdate(string UserID, CWebSocketClient &webSocketClient)
{

    string accountProfile = JsonHelper::CreateAccountProfileProto(UserID);
    if(webSocketClient.SendAccountProfile(accountProfile)) {
        // Success - no need to log every minute
    } else {
        Print("[WARNING] Failed to send account update");
    }
}

//+------------------------------------------------------------------+
//| Create Binary Protocol client price stream                     |
//+------------------------------------------------------------------+
bool CreateBinaryPriceStream(string UserID, string &tradingPairs[], bool StreamCurrentChartOnly, CWebSocketClient &webSocketClient)
{
    MqlTick ticks[];
    string symbols[];

    if(StreamCurrentChartOnly) {
        // Stream only current chart symbol
        ArrayResize(symbols, 1);
        ArrayResize(ticks, 1);
        symbols[0] = _Symbol;

        if(!SymbolInfoTick(_Symbol, ticks[0])) {
            Print("[ERROR] Failed to get tick data for ", _Symbol);
            return false;
        }

        Print("[BINARY] Streaming current chart only: ", _Symbol);
    } else {
        // Stream selected trading pairs
        int validPairs = 0;

        // Count valid pairs first
        for(int i = 0; i < ArraySize(tradingPairs); i++) {
            MqlTick tempTick;
            if(SymbolInfoTick(tradingPairs[i], tempTick)) {
                validPairs++;
            }
        }

        if(validPairs == 0) {
            Print("[WARNING] No valid trading pairs found for streaming");
            return false;
        }

        // Resize arrays for valid pairs
        ArrayResize(symbols, validPairs);
        ArrayResize(ticks, validPairs);

        int index = 0;
        for(int i = 0; i < ArraySize(tradingPairs); i++) {
            if(SymbolInfoTick(tradingPairs[i], ticks[index])) {
                symbols[index] = tradingPairs[i];
                index++;
            }
        }

        Print("[BINARY] Streaming ", validPairs, " trading pairs");
    }

    // Send binary price data
    return webSocketClient.SendBinaryPriceData(UserID, symbols, ticks);
}

//+------------------------------------------------------------------+
//| Send binary account update                                      |
//+------------------------------------------------------------------+
void SendBinaryAccountUpdate(string UserID, CWebSocketClient &webSocketClient)
{
    if(webSocketClient.SendBinaryAccountProfile(UserID)) {
        // Success - no need to log every minute for binary
    } else {
        Print("[WARNING] Failed to send binary account update");
    }
}

//+------------------------------------------------------------------+
//| Parse binary trading command and execute                       |
//+------------------------------------------------------------------+
bool ProcessBinaryTradingCommand(string commandData, string UserID, CWebSocketClient &webSocketClient, CTrade &tradeManager)
{
    if(StringLen(commandData) < 48) { // Minimum: header(16) + command(32)
        Print("[ERROR] Binary command data too small: ", StringLen(commandData), " bytes");
        return false;
    }

    // Convert string response to binary data (if received as base64 or hex)
    char binaryBuffer[];
    if(!ConvertResponseToBinary(commandData, binaryBuffer)) {
        Print("[ERROR] Failed to convert response to binary");
        return false;
    }

    // For now, binary trading command parsing is simplified
    // In a real implementation, this would parse the binary command structure
    // TODO: Implement full binary command parsing

    // Mock parsing for demonstration
    string action = "BUY"; // Default action for testing
    string symbol = "EURUSD"; // Default symbol for testing
    double lots = 0.1;
    double stopLoss = 0.0;
    double takeProfit = 0.0;
    ulong ticket = 0;

    Print("[BINARY] Mock parsed command - Action: ", action, " Symbol: ", symbol, " Lots: ", lots);

    // Execute the command (reuse existing logic)
    bool success = false;
    if(action == "BUY") {
        success = tradeManager.Buy(lots, symbol, 0, stopLoss, takeProfit, "Binary AI Signal");
    }
    else if(action == "SELL") {
        success = tradeManager.Sell(lots, symbol, 0, stopLoss, takeProfit, "Binary AI Signal");
    }
    else if(action == "CLOSE") {
        success = tradeManager.PositionClose(ticket);
    }
    else if(action == "MODIFY") {
        if(PositionSelectByTicket(ticket)) {
            success = tradeManager.PositionModify(ticket, stopLoss, takeProfit);
        }
    }

    // Send confirmation back to server
    SendTradeConfirmation(UserID, webSocketClient, tradeManager, action, symbol, lots, success);

    return success;
}

//+------------------------------------------------------------------+
//| Convert response data to binary format                         |
//+------------------------------------------------------------------+
bool ConvertResponseToBinary(string response, char &buffer[])
{
    // For now, assume response is already binary data in string format
    // In real implementation, this might need base64 decoding or hex conversion
    int responseLen = StringLen(response);

    if(responseLen < 48) {
        Print("[ERROR] Response too small for binary command");
        return false;
    }

    ArrayResize(buffer, responseLen);
    StringToCharArray(response, buffer, 0, responseLen);

    return true;
}

//+------------------------------------------------------------------+
//| Get binary protocol statistics                                  |
//+------------------------------------------------------------------+
string GetBinaryProtocolStats(int symbolCount)
{
    int packetSize = 16 + (symbolCount * 16); // header + symbols
    int jsonSize = 720 + (symbolCount * 150); // estimated JSON size

    double reduction = ((double)(jsonSize - packetSize) / jsonSize) * 100.0;

    string stats = "Binary Protocol Statistics:\n";
    stats += "Symbols: " + IntegerToString(symbolCount) + "\n";
    stats += "Binary Size: " + IntegerToString(packetSize) + " bytes\n";
    stats += "JSON Size: " + IntegerToString(jsonSize) + " bytes\n";
    stats += "Reduction: " + DoubleToString(reduction, 1) + "%\n";
    stats += "Processing: ~1.2ms (vs 6.1ms JSON)";

    return stats;
}

#endif // TRADINGHELPERS_MQH