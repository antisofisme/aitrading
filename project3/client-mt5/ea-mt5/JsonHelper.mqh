//+------------------------------------------------------------------+
//|                                                  JsonHelper.mqh |
//|                           Manual JSON construction helper for MT5 |
//+------------------------------------------------------------------+
#ifndef JSONHELPER_MQH
#define JSONHELPER_MQH

class JsonHelper
{
public:
    //+------------------------------------------------------------------+
    //| Create JSON string from key-value pairs                         |
    //+------------------------------------------------------------------+
    static string CreateJson(string &keys[], string &values[], int count)
    {
        if(count <= 0) return "{}";

        string json = "{";
        for(int i = 0; i < count; i++) {
            if(i > 0) json += ",";
            json += "\"" + keys[i] + "\":\"" + values[i] + "\"";
        }
        json += "}";
        return json;
    }

    //+------------------------------------------------------------------+
    //| Escape JSON string                                              |
    //+------------------------------------------------------------------+
    static string EscapeJson(string value)
    {
        StringReplace(value, "\\", "\\\\");
        StringReplace(value, "\"", "\\\"");
        StringReplace(value, "\r", "\\r");
        StringReplace(value, "\n", "\\n");
        StringReplace(value, "\t", "\\t");
        return value;
    }

    //+------------------------------------------------------------------+
    //| Add string field to JSON                                        |
    //+------------------------------------------------------------------+
    static string AddStringField(string json, string key, string value, bool isLast = false)
    {
        if(StringLen(json) > 1) json += ",";
        json += "\"" + key + "\":\"" + EscapeJson(value) + "\"";
        return json;
    }

    //+------------------------------------------------------------------+
    //| Add numeric field to JSON                                       |
    //+------------------------------------------------------------------+
    static string AddNumericField(string json, string key, double value, int digits = 2, bool isLast = false)
    {
        if(StringLen(json) > 1) json += ",";
        json += "\"" + key + "\":" + DoubleToString(value, digits);
        return json;
    }

    //+------------------------------------------------------------------+
    //| Add integer field to JSON                                       |
    //+------------------------------------------------------------------+
    static string AddIntegerField(string json, string key, long value, bool isLast = false)
    {
        if(StringLen(json) > 1) json += ",";
        json += "\"" + key + "\":" + IntegerToString(value);
        return json;
    }

    //+------------------------------------------------------------------+
    //| Add boolean field to JSON                                       |
    //+------------------------------------------------------------------+
    static string AddBooleanField(string json, string key, bool value, bool isLast = false)
    {
        if(StringLen(json) > 1) json += ",";
        json += "\"" + key + "\":" + (value ? "true" : "false");
        return json;
    }

    //+------------------------------------------------------------------+
    //| Add string array field to JSON                                  |
    //+------------------------------------------------------------------+
    static string AddStringArrayField(string json, string key, string &values[], int count, bool isLast = false)
    {
        if(StringLen(json) > 1) json += ",";
        json += "\"" + key + "\":[";
        for(int i = 0; i < count; i++) {
            if(i > 0) json += ",";
            json += "\"" + EscapeJson(values[i]) + "\"";
        }
        json += "]";
        return json;
    }

    //+------------------------------------------------------------------+
    //| Create Account Profile Protocol Buffer Format                   |
    //+------------------------------------------------------------------+
    static string CreateAccountProfileProto(string userId)
    {
        string profile = "{";
        profile = AddStringField(profile, "user_id", userId);
        profile = AddStringField(profile, "broker_name", AccountInfoString(ACCOUNT_COMPANY));
        profile = AddStringField(profile, "account_number", IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)));
        profile = AddStringField(profile, "server", AccountInfoString(ACCOUNT_SERVER));
        profile = AddNumericField(profile, "balance", AccountInfoDouble(ACCOUNT_BALANCE), 2);
        profile = AddNumericField(profile, "equity", AccountInfoDouble(ACCOUNT_EQUITY), 2);
        profile = AddNumericField(profile, "margin", AccountInfoDouble(ACCOUNT_MARGIN), 2);
        profile = AddNumericField(profile, "free_margin", AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2);
        profile = AddIntegerField(profile, "leverage", AccountInfoInteger(ACCOUNT_LEVERAGE));
        profile = AddStringField(profile, "currency", AccountInfoString(ACCOUNT_CURRENCY));
        profile = AddIntegerField(profile, "timestamp", TimeCurrent());
        profile += "}";
        return profile;
    }

    //+------------------------------------------------------------------+
    //| Create Market Data Protocol Buffer Format                       |
    //+------------------------------------------------------------------+
    static string CreateMarketDataProto(string userId, string symbol, double bid, double ask, datetime timestamp)
    {
        string marketData = "{";
        marketData = AddStringField(marketData, "symbol", symbol);
        marketData = AddNumericField(marketData, "bid", bid, 5);
        marketData = AddNumericField(marketData, "ask", ask, 5);
        marketData = AddNumericField(marketData, "spread", (ask - bid) * MathPow(10, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)), 1);
        marketData = AddIntegerField(marketData, "timestamp", timestamp);
        marketData = AddStringField(marketData, "broker_server", AccountInfoString(ACCOUNT_SERVER));
        marketData += "}";
        return marketData;
    }

    //+------------------------------------------------------------------+
    //| Parse Trading Command from JSON                                 |
    //+------------------------------------------------------------------+
    static bool ParseTradingCommand(string commandJson, string &action, string &symbol, double &lots, double &stopLoss, double &takeProfit)
    {
        ulong dummy_ticket = 0;
        return ParseTradingCommandExtended(commandJson, action, symbol, lots, stopLoss, takeProfit, dummy_ticket);
    }

    //+------------------------------------------------------------------+
    //| Parse Extended Trading Command with Ticket Support              |
    //+------------------------------------------------------------------+
    static bool ParseTradingCommandExtended(string commandJson, string &action, string &symbol, double &lots, double &stopLoss, double &takeProfit, ulong &ticket)
    {
        // Initialize variables
        action = "";
        symbol = "";
        lots = 0.0;
        stopLoss = 0.0;
        takeProfit = 0.0;
        ticket = 0;

        // Simple JSON parsing
        string searchKey;
        int startPos, endPos;

        // Parse action
        searchKey = "\"action\":\"";
        startPos = StringFind(commandJson, searchKey);
        if(startPos != -1) {
            startPos += StringLen(searchKey);
            endPos = StringFind(commandJson, "\"", startPos);
            if(endPos != -1) {
                action = StringSubstr(commandJson, startPos, endPos - startPos);
            }
        }

        // Parse symbol
        searchKey = "\"symbol\":\"";
        startPos = StringFind(commandJson, searchKey);
        if(startPos != -1) {
            startPos += StringLen(searchKey);
            endPos = StringFind(commandJson, "\"", startPos);
            if(endPos != -1) {
                symbol = StringSubstr(commandJson, startPos, endPos - startPos);
            }
        }

        // Parse lots
        searchKey = "\"lots\":";
        startPos = StringFind(commandJson, searchKey);
        if(startPos != -1) {
            startPos += StringLen(searchKey);
            endPos = StringFind(commandJson, ",", startPos);
            if(endPos == -1) endPos = StringFind(commandJson, "}", startPos);
            if(endPos != -1) {
                string lotsStr = StringSubstr(commandJson, startPos, endPos - startPos);
                lots = StringToDouble(lotsStr);
            }
        }

        // Parse stop loss
        searchKey = "\"stop_loss\":";
        startPos = StringFind(commandJson, searchKey);
        if(startPos != -1) {
            startPos += StringLen(searchKey);
            endPos = StringFind(commandJson, ",", startPos);
            if(endPos == -1) endPos = StringFind(commandJson, "}", startPos);
            if(endPos != -1) {
                string slStr = StringSubstr(commandJson, startPos, endPos - startPos);
                stopLoss = StringToDouble(slStr);
            }
        }

        // Parse take profit
        searchKey = "\"take_profit\":";
        startPos = StringFind(commandJson, searchKey);
        if(startPos != -1) {
            startPos += StringLen(searchKey);
            endPos = StringFind(commandJson, ",", startPos);
            if(endPos == -1) endPos = StringFind(commandJson, "}", startPos);
            if(endPos != -1) {
                string tpStr = StringSubstr(commandJson, startPos, endPos - startPos);
                takeProfit = StringToDouble(tpStr);
            }
        }

        // Parse ticket (for modify/close commands)
        searchKey = "\"ticket\":";
        startPos = StringFind(commandJson, searchKey);
        if(startPos != -1) {
            startPos += StringLen(searchKey);
            endPos = StringFind(commandJson, ",", startPos);
            if(endPos == -1) endPos = StringFind(commandJson, "}", startPos);
            if(endPos != -1) {
                string ticketStr = StringSubstr(commandJson, startPos, endPos - startPos);
                ticket = StringToInteger(ticketStr);
            }
        }

        return StringLen(action) > 0 && StringLen(symbol) > 0;
    }

    //+------------------------------------------------------------------+
    //| Create Trade Confirmation Protocol Buffer Format                |
    //+------------------------------------------------------------------+
    static string CreateTradeConfirmationProto(string userId, string status, string symbol, ulong ticket, double price, double lots)
    {
        string confirmation = "{";
        confirmation = AddStringField(confirmation, "user_id", userId);
        confirmation = AddStringField(confirmation, "status", status);
        confirmation = AddStringField(confirmation, "symbol", symbol);
        confirmation = AddIntegerField(confirmation, "ticket", ticket);
        confirmation = AddNumericField(confirmation, "price", price, 5);
        confirmation = AddNumericField(confirmation, "lots", lots, 2);
        confirmation = AddIntegerField(confirmation, "timestamp", TimeCurrent());
        confirmation += "}";
        return confirmation;
    }

    //+------------------------------------------------------------------+
    //| Create Modify Confirmation Protocol Buffer Format               |
    //+------------------------------------------------------------------+
    static string CreateModifyConfirmationProto(string userId, string symbol, ulong ticket, double newSL, double newTP, bool success, string reason = "")
    {
        string confirmation = "{";
        confirmation = AddStringField(confirmation, "user_id", userId);
        confirmation = AddStringField(confirmation, "action", "MODIFY_RESULT");
        confirmation = AddStringField(confirmation, "symbol", symbol);
        confirmation = AddIntegerField(confirmation, "ticket", ticket);
        confirmation = AddNumericField(confirmation, "new_stop_loss", newSL, 5);
        confirmation = AddNumericField(confirmation, "new_take_profit", newTP, 5);
        confirmation = AddStringField(confirmation, "status", success ? "success" : "failed");
        if(StringLen(reason) > 0) {
            confirmation = AddStringField(confirmation, "reason", reason);
        }
        confirmation = AddIntegerField(confirmation, "timestamp", TimeCurrent());
        confirmation += "}";
        return confirmation;
    }

    //+------------------------------------------------------------------+
    //| Create Partial Close Confirmation Protocol Buffer Format        |
    //+------------------------------------------------------------------+
    static string CreatePartialCloseConfirmationProto(string userId, string symbol, ulong ticket, double closedLots, double remainingLots, bool success)
    {
        string confirmation = "{";
        confirmation = AddStringField(confirmation, "user_id", userId);
        confirmation = AddStringField(confirmation, "action", "PARTIAL_CLOSE_RESULT");
        confirmation = AddStringField(confirmation, "symbol", symbol);
        confirmation = AddIntegerField(confirmation, "ticket", ticket);
        confirmation = AddNumericField(confirmation, "closed_lots", closedLots, 2);
        confirmation = AddNumericField(confirmation, "remaining_lots", remainingLots, 2);
        confirmation = AddStringField(confirmation, "status", success ? "success" : "failed");
        confirmation = AddIntegerField(confirmation, "timestamp", TimeCurrent());
        confirmation += "}";
        return confirmation;
    }
};

#endif // JSONHELPER_MQH