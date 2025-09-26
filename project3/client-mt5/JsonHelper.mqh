//+------------------------------------------------------------------+
//|                                                  JsonHelper.mqh |
//|                           Manual JSON construction helper for MT5 |
//+------------------------------------------------------------------+

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
    //| Protocol Buffers Helper Functions                               |
    //+------------------------------------------------------------------+

    //+------------------------------------------------------------------+
    //| Create Protocol Buffers-style market data                       |
    //+------------------------------------------------------------------+
    static string CreateMarketDataProto(string userID, string symbol, double bid, double ask, datetime timestamp)
    {
        string proto = "{";
        proto = AddStringField(proto, "user_id", userID);
        proto = AddStringField(proto, "symbol", symbol);
        proto = AddNumericField(proto, "bid", bid, 5);
        proto = AddNumericField(proto, "ask", ask, 5);
        proto = AddIntegerField(proto, "timestamp", timestamp);
        proto = AddStringField(proto, "data_type", "market_price");
        proto = AddStringField(proto, "source", "MT5_CLIENT");
        proto += "}";
        return proto;
    }

    //+------------------------------------------------------------------+
    //| Create Protocol Buffers-style account profile                   |
    //+------------------------------------------------------------------+
    static string CreateAccountProfileProto(string userID)
    {
        string proto = "{";
        proto = AddStringField(proto, "user_id", userID);
        proto = AddStringField(proto, "account_number", IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)));
        proto = AddStringField(proto, "broker_name", AccountInfoString(ACCOUNT_COMPANY));
        proto = AddStringField(proto, "server_name", AccountInfoString(ACCOUNT_SERVER));
        proto = AddStringField(proto, "base_currency", AccountInfoString(ACCOUNT_CURRENCY));
        proto = AddNumericField(proto, "balance", AccountInfoDouble(ACCOUNT_BALANCE));
        proto = AddNumericField(proto, "equity", AccountInfoDouble(ACCOUNT_EQUITY));
        proto = AddNumericField(proto, "margin_used", AccountInfoDouble(ACCOUNT_MARGIN));
        proto = AddNumericField(proto, "margin_free", AccountInfoDouble(ACCOUNT_MARGIN_FREE));
        proto = AddIntegerField(proto, "leverage", AccountInfoInteger(ACCOUNT_LEVERAGE));
        proto = AddStringField(proto, "platform", "MT5");
        proto = AddStringField(proto, "ea_version", "1.00");
        proto = AddIntegerField(proto, "timestamp", TimeCurrent());
        proto += "}";
        return proto;
    }

    //+------------------------------------------------------------------+
    //| Parse trading command from Protocol Buffers JSON               |
    //+------------------------------------------------------------------+
    static bool ParseTradingCommand(string protoJson, string &action, string &symbol, double &lots, double &sl, double &tp)
    {
        if(StringLen(protoJson) == 0) return false;

        action = GetJsonValue(protoJson, "action");
        symbol = GetJsonValue(protoJson, "symbol");
        lots = StringToDouble(GetJsonValue(protoJson, "lots"));
        sl = StringToDouble(GetJsonValue(protoJson, "stop_loss"));
        tp = StringToDouble(GetJsonValue(protoJson, "take_profit"));

        return (StringLen(action) > 0 && StringLen(symbol) > 0 && lots > 0);
    }

    //+------------------------------------------------------------------+
    //| Create trade confirmation Protocol Buffers format               |
    //+------------------------------------------------------------------+
    static string CreateTradeConfirmationProto(string userID, string status, string symbol, ulong ticket, double price, double lots)
    {
        string proto = "{";
        proto = AddStringField(proto, "user_id", userID);
        proto = AddStringField(proto, "status", status);
        proto = AddStringField(proto, "symbol", symbol);
        proto = AddIntegerField(proto, "ticket", ticket);
        proto = AddNumericField(proto, "price", price, 5);
        proto = AddNumericField(proto, "lots", lots, 2);
        proto = AddIntegerField(proto, "timestamp", TimeCurrent());
        proto += "}";
        return proto;
    }
}