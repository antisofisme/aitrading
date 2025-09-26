//+------------------------------------------------------------------+
//|                                              TradingHelpers.mqh |
//|                     Enhanced trading functions and utilities    |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Create Protocol Buffers client price stream                    |
//+------------------------------------------------------------------+
string CreateClientPriceStream()
{
    extern string UserID;
    extern string TradingSymbols[];
    extern bool StreamCurrentChartOnly;

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
        for(int i = 0; i < ArraySize(TradingSymbols); i++) {
            MqlTick tick;
            if(SymbolInfoTick(TradingSymbols[i], tick)) {
                if(priceCount > 0) streamData += ",";
                streamData += "{";
                streamData = JsonHelper::AddStringField(streamData, "symbol", TradingSymbols[i]);
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
int GetPriceCount()
{
    extern string TradingSymbols[];
    extern bool StreamCurrentChartOnly;

    if(StreamCurrentChartOnly) {
        return 1;
    } else {
        int count = 0;
        for(int i = 0; i < ArraySize(TradingSymbols); i++) {
            MqlTick tick;
            if(SymbolInfoTick(TradingSymbols[i], tick)) {
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
void SendTradeConfirmation(string action, string symbol, double lots, bool success)
{
    extern string UserID;
    extern CWebSocketClient wsClient;
    extern CTrade trade;

    string status = success ? "executed" : "failed";
    ulong ticket = success ? trade.ResultOrder() : 0;
    double price = success ? (action == "BUY" ? SymbolInfoDouble(symbol, SYMBOL_ASK) : SymbolInfoDouble(symbol, SYMBOL_BID)) : 0;

    string confirmation = JsonHelper::CreateTradeConfirmationProto(UserID, status, symbol, ticket, price, lots);

    if(wsClient.SendTradeConfirmation(confirmation)) {
        Print("📤 Trade confirmation sent: " + status);
    } else {
        Print("⚠️ Failed to send trade confirmation");
    }
}

//+------------------------------------------------------------------+
//| Send periodic account updates                                   |
//+------------------------------------------------------------------+
void SendAccountUpdate()
{
    extern string UserID;
    extern CWebSocketClient wsClient;

    string accountProfile = JsonHelper::CreateAccountProfileProto(UserID);
    if(wsClient.SendAccountProfile(accountProfile)) {
        // Success - no need to log every minute
    } else {
        Print("⚠️ Failed to send account update");
    }
}