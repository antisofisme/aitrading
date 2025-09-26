//+------------------------------------------------------------------+
//|                                             WebSocketClient.mqh |
//|                     HTTP/WebSocket client implementation for MT5 |
//+------------------------------------------------------------------+

#include <Trade\Trade.mqh>

//+------------------------------------------------------------------+
//| HTTP Client for Server Communication                            |
//+------------------------------------------------------------------+
class CHttpClient
{
private:
    string m_serverUrl;
    string m_authToken;
    string m_userAgent;
    int    m_timeout;
    bool   m_isConnected;
    datetime m_lastHeartbeat;
    int    m_connectionRetries;

public:
    //+------------------------------------------------------------------+
    //| Constructor                                                      |
    //+------------------------------------------------------------------+
    CHttpClient(string serverUrl = "", string authToken = "")
    {
        m_serverUrl = serverUrl;
        m_authToken = authToken;
        m_userAgent = "SuhoAI-MT5-Client/1.0";
        m_timeout = 5000; // 5 seconds
        m_isConnected = false;
        m_lastHeartbeat = 0;
        m_connectionRetries = 0;
    }

    //+------------------------------------------------------------------+
    //| Set server configuration                                         |
    //+------------------------------------------------------------------+
    void SetServer(string url, string token)
    {
        m_serverUrl = url;
        m_authToken = token;
        m_isConnected = false; // Reset connection status
    }

    //+------------------------------------------------------------------+
    //| Test server connection                                           |
    //+------------------------------------------------------------------+
    bool TestConnection()
    {
        if(StringLen(m_serverUrl) == 0) {
            Print("❌ Server URL not configured");
            return false;
        }

        string endpoint = "/api/v1/health";
        string response = "";
        int statusCode = 0;

        bool result = HttpRequest("GET", endpoint, "", response, statusCode);

        if(result && statusCode == 200) {
            Print("✅ Server connection successful");
            m_isConnected = true;
            m_lastHeartbeat = TimeCurrent();
            m_connectionRetries = 0;
            return true;
        } else {
            Print("❌ Server connection failed. Status: " + IntegerToString(statusCode));
            m_isConnected = false;
            m_connectionRetries++;
            return false;
        }
    }

    //+------------------------------------------------------------------+
    //| Send account profile to server                                  |
    //+------------------------------------------------------------------+
    bool SendAccountProfile(string profileData)
    {
        if(!m_isConnected && !TestConnection()) {
            return false;
        }

        string endpoint = "/api/v1/account/profile";
        string response = "";
        int statusCode = 0;

        bool result = HttpRequest("POST", endpoint, profileData, response, statusCode);

        if(result && (statusCode == 200 || statusCode == 201)) {
            Print("✅ Account profile sent successfully");
            return true;
        } else {
            Print("❌ Failed to send account profile. Status: " + IntegerToString(statusCode));
            if(statusCode == 401) {
                Print("🔑 Authentication failed - check JWT token");
            }
            return false;
        }
    }

    //+------------------------------------------------------------------+
    //| Send price data to server                                       |
    //+------------------------------------------------------------------+
    bool SendPriceData(string priceData)
    {
        if(!m_isConnected && !TestConnection()) {
            return false;
        }

        string endpoint = "/api/v1/prices/stream";
        string response = "";
        int statusCode = 0;

        bool result = HttpRequest("POST", endpoint, priceData, response, statusCode);

        if(result && statusCode == 200) {
            // Success - update heartbeat
            m_lastHeartbeat = TimeCurrent();
            return true;
        } else {
            if(statusCode != 200) {
                Print("⚠️ Price streaming error. Status: " + IntegerToString(statusCode));
            }
            return false;
        }
    }

    //+------------------------------------------------------------------+
    //| Check for server commands                                       |
    //+------------------------------------------------------------------+
    string GetServerCommands()
    {
        if(!m_isConnected && !TestConnection()) {
            return "";
        }

        string endpoint = "/api/v1/commands/pending";
        string response = "";
        int statusCode = 0;

        bool result = HttpRequest("GET", endpoint, "", response, statusCode);

        if(result && statusCode == 200) {
            m_lastHeartbeat = TimeCurrent();
            return response;
        } else if(statusCode == 204) {
            // No commands pending - this is normal
            return "";
        } else {
            Print("⚠️ Failed to get server commands. Status: " + IntegerToString(statusCode));
            return "";
        }
    }

    //+------------------------------------------------------------------+
    //| Send trade confirmation to server                               |
    //+------------------------------------------------------------------+
    bool SendTradeConfirmation(string confirmationData)
    {
        if(!m_isConnected && !TestConnection()) {
            return false;
        }

        string endpoint = "/api/v1/trades/confirmation";
        string response = "";
        int statusCode = 0;

        bool result = HttpRequest("POST", endpoint, confirmationData, response, statusCode);

        if(result && statusCode == 200) {
            Print("✅ Trade confirmation sent");
            return true;
        } else {
            Print("❌ Failed to send trade confirmation. Status: " + IntegerToString(statusCode));
            return false;
        }
    }

    //+------------------------------------------------------------------+
    //| Check connection health                                         |
    //+------------------------------------------------------------------+
    bool IsHealthy()
    {
        if(!m_isConnected) return false;

        // Check if heartbeat is too old (more than 2 minutes)
        if(TimeCurrent() - m_lastHeartbeat > 120) {
            Print("⚠️ Connection heartbeat timeout");
            m_isConnected = false;
            return false;
        }

        return true;
    }

    //+------------------------------------------------------------------+
    //| Get connection status                                           |
    //+------------------------------------------------------------------+
    bool IsConnected() { return m_isConnected; }
    int GetRetryCount() { return m_connectionRetries; }
    datetime GetLastHeartbeat() { return m_lastHeartbeat; }

private:
    //+------------------------------------------------------------------+
    //| Core HTTP request implementation                                |
    //+------------------------------------------------------------------+
    bool HttpRequest(string method, string endpoint, string data, string &response, int &statusCode)
    {
        string url = m_serverUrl + endpoint;

        // Convert WebSocket URL to HTTP if needed
        if(StringFind(url, "wss://") == 0) {
            StringReplace(url, "wss://", "https://");
        } else if(StringFind(url, "ws://") == 0) {
            StringReplace(url, "ws://", "http://");
        }

        // Prepare headers
        string headers = "Content-Type: application/x-www-form-urlencoded\r\n";
        headers += "User-Agent: " + m_userAgent + "\r\n";

        if(StringLen(m_authToken) > 0) {
            headers += "Authorization: Bearer " + m_authToken + "\r\n";
        }

        // Convert data to char array for WebRequest
        char dataArray[];
        char responseArray[];

        if(StringLen(data) > 0) {
            StringToCharArray(data, dataArray, 0, StringLen(data));
        }

        // Make HTTP request
        int result = WebRequest(
            method,
            url,
            headers,
            m_timeout,
            dataArray,
            responseArray,
            headers // Will contain response headers
        );

        if(result == -1) {
            int error = GetLastError();
            Print("❌ HTTP request failed. Error: " + IntegerToString(error));

            if(error == 4014) {  // ERR_FUNCTION_NOT_ALLOWED
                Print("💡 Enable WebRequest for: " + url + " in MT5 settings");
            }

            statusCode = 0;
            return false;
        } else {
            statusCode = result;
            response = CharArrayToString(responseArray);

            // Debug logging for development
            if(result != 200 && result != 201 && result != 204) {
                Print("🔍 HTTP " + method + " " + endpoint + " → " + IntegerToString(result));
            }

            return true;
        }
    }
};