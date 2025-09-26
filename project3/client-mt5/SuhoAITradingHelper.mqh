//+------------------------------------------------------------------+
//|                                           SuhoAITradingHelper.mqh |
//|                          Helper functions for SuhoAI Trading EA |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Create Protocol Buffers client price stream                    |
//+------------------------------------------------------------------+
string CreateClientPriceStream()
{
    extern string UserID;
    extern string TradingSymbols[];

    string data = "{";
    data += "\"user_id\":\"" + UserID + "\"";
    data += ",\"broker_name\":\"" + AccountInfoString(ACCOUNT_COMPANY) + "\"";
    data += ",\"account_number\":\"" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "\"";
    data += ",\"batch_timestamp\":" + IntegerToString(GetTickCount());
    data += ",\"prices\":[";

    int count = 0;
    for(int i = 0; i < ArraySize(TradingSymbols); i++) {
        MqlTick tick;
        if(SymbolInfoTick(TradingSymbols[i], tick)) {
            if(count > 0) data += ",";
            data += "{\"symbol\":\"" + TradingSymbols[i] + "\"";
            data += ",\"bid\":" + DoubleToString(tick.bid, 5);
            data += ",\"ask\":" + DoubleToString(tick.ask, 5);
            data += ",\"spread\":" + DoubleToString((tick.ask - tick.bid) * 10000, 1);
            data += ",\"timestamp\":" + IntegerToString(GetTickCount());
            data += ",\"broker_server\":\"" + AccountInfoString(ACCOUNT_SERVER) + "\"}";
            count++;
        }
    }

    data += "]}";
    return data;
}

//+------------------------------------------------------------------+
//| Get price count for streaming                                   |
//+------------------------------------------------------------------+
int GetPriceCount()
{
    extern string TradingSymbols[];
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
            string value = StringSubstr(json, startPos, endPos - startPos);
            // Remove quotes and whitespace
            StringReplace(value, "\"", "");
            StringReplace(value, " ", "");
            return value;
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
    double price = 0;

    if(success) {
        if(action == "BUY") {
            price = SymbolInfoDouble(symbol, SYMBOL_ASK);
        } else {
            price = SymbolInfoDouble(symbol, SYMBOL_BID);
        }
    }

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
        static datetime lastLog = 0;
        if(TimeCurrent() - lastLog > 300) { // Log every 5 minutes
            Print("📤 Account update sent successfully");
            lastLog = TimeCurrent();
        }
    } else {
        Print("⚠️ Failed to send account update");
    }
}