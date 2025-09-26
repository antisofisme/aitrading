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
}