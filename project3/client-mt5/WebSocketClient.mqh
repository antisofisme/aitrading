//+------------------------------------------------------------------+
//|                                             WebSocketClient.mqh |
//|                     Enhanced WebSocket client for dual connections |
//+------------------------------------------------------------------+

#include <Trade\Trade.mqh>

//+------------------------------------------------------------------+
//| Enhanced WebSocket Client for Trading Commands                  |
//+------------------------------------------------------------------+
class CWebSocketClient
{
private:
    string m_serverUrl;
    string m_authToken;
    string m_userAgent;
    string m_userId;
    int    m_timeout;
    bool   m_isConnected;
    datetime m_lastHeartbeat;
    int    m_connectionRetries;
    bool   m_isReconnecting;

    // Dual connection support
    bool   m_isPriceStreamConnected;
    string m_priceStreamUrl;
    datetime m_lastPriceStream;

    // Command processing
    string m_pendingCommands[];
    int    m_commandCount;

public:
    //+------------------------------------------------------------------+
    //| Constructor                                                      |
    //+------------------------------------------------------------------+
    CWebSocketClient(string serverUrl = "", string authToken = "", string userId = "")
    {
        m_serverUrl = serverUrl;
        m_authToken = authToken;
        m_userId = userId;
        m_userAgent = "SuhoAI-MT5-Client/2.0";
        m_timeout = 10000; // 10 seconds
        m_isConnected = false;
        m_lastHeartbeat = 0;
        m_connectionRetries = 0;
        m_isReconnecting = false;

        // Price streaming
        m_isPriceStreamConnected = false;
        m_priceStreamUrl = "";
        m_lastPriceStream = 0;

        // Commands
        ArrayResize(m_pendingCommands, 100);
        m_commandCount = 0;
    }

    //+------------------------------------------------------------------+
    //| Set dual server configuration                                    |
    //+------------------------------------------------------------------+
    void SetServer(string url, string token, string userId = "")
    {
        m_serverUrl = url;
        m_authToken = token;
        m_userId = userId;
        m_isConnected = false;
        m_isPriceStreamConnected = false;

        // Setup price streaming URL
        if(StringFind(url, "wss://") == 0) {
            m_priceStreamUrl = StringSubstr(url, 0, StringFind(url, "/ws/")) + "/ws/price-stream";
        } else if(StringFind(url, "ws://") == 0) {
            m_priceStreamUrl = StringSubstr(url, 0, StringFind(url, "/ws/")) + "/ws/price-stream";
        } else {
            m_priceStreamUrl = url + "/ws/price-stream";
        }
    }

    //+------------------------------------------------------------------+
    //| Establish dual WebSocket connections                            |
    //+------------------------------------------------------------------+
    bool ConnectToServer()
    {
        if(StringLen(m_serverUrl) == 0) {
            Print("❌ Server URL not configured");
            return false;
        }

        Print("🔗 Connecting to dual WebSocket endpoints...");

        // 1. Connect main trading WebSocket
        if(!ConnectTradingWebSocket()) {
            Print("❌ Failed to connect trading WebSocket");
            return false;
        }

        // 2. Connect price streaming WebSocket
        if(!ConnectPriceStreamWebSocket()) {
            Print("❌ Failed to connect price stream WebSocket");
            m_isConnected = false;
            return false;
        }

        Print("✅ Dual WebSocket connections established");
        Print("📊 Trading commands: " + m_serverUrl);
        Print("💱 Price streaming: " + m_priceStreamUrl);

        m_lastHeartbeat = TimeCurrent();
        m_connectionRetries = 0;
        return true;
    }

    //+------------------------------------------------------------------+
    //| Connect trading commands WebSocket                              |
    //+------------------------------------------------------------------+
    bool ConnectTradingWebSocket()
    {
        string endpoint = "/api/v1/health";
        string response = "";
        int statusCode = 0;

        bool result = HttpRequest("GET", endpoint, "", response, statusCode);

        if(result && statusCode == 200) {
            m_isConnected = true;
            Print("✅ Trading WebSocket connected");
            return true;
        } else {
            Print("❌ Trading WebSocket failed. Status: " + IntegerToString(statusCode));
            m_connectionRetries++;
            return false;
        }
    }

    //+------------------------------------------------------------------+
    //| Connect price streaming WebSocket                               |
    //+------------------------------------------------------------------+
    bool ConnectPriceStreamWebSocket()
    {
        // Test price stream endpoint
        string endpoint = "/api/v1/prices/health";
        string response = "";
        int statusCode = 0;

        bool result = HttpRequest("GET", endpoint, "", response, statusCode);

        if(result && (statusCode == 200 || statusCode == 404)) { // 404 is OK for price stream
            m_isPriceStreamConnected = true;
            Print("✅ Price stream WebSocket connected");
            return true;
        } else {
            Print("❌ Price stream WebSocket failed. Status: " + IntegerToString(statusCode));
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
    //| Stream price data via dedicated WebSocket                       |
    //+------------------------------------------------------------------+
    bool StreamPriceData(string priceData)
    {
        if(!m_isPriceStreamConnected) {
            if(!ConnectPriceStreamWebSocket()) {
                return false;
            }
        }

        string endpoint = "/api/v1/prices/stream";
        string response = "";
        int statusCode = 0;

        bool result = HttpRequest("POST", endpoint, priceData, response, statusCode);

        if(result && statusCode == 200) {
            m_lastPriceStream = TimeCurrent();
            return true;
        } else {
            if(statusCode != 200) {
                Print("⚠️ Price streaming error. Status: " + IntegerToString(statusCode));
                // Try reconnection on failure
                if(statusCode == 0 || statusCode >= 500) {
                    m_isPriceStreamConnected = false;
                }
            }
            return false;
        }
    }

    //+------------------------------------------------------------------+
    //| Get pending trading commands from server                        |
    //+------------------------------------------------------------------+
    string GetServerCommands()
    {
        if(!m_isConnected && !ConnectTradingWebSocket()) {
            return "";
        }

        string endpoint = "/api/v1/commands/pending";
        if(StringLen(m_userId) > 0) {
            endpoint += "?user_id=" + m_userId;
        }

        string response = "";
        int statusCode = 0;

        bool result = HttpRequest("GET", endpoint, "", response, statusCode);

        if(result && statusCode == 200) {
            m_lastHeartbeat = TimeCurrent();
            // Parse and queue commands
            QueueCommands(response);
            return response;
        } else if(statusCode == 204) {
            // No commands pending - this is normal
            m_lastHeartbeat = TimeCurrent();
            return "";
        } else {
            Print("⚠️ Failed to get trading commands. Status: " + IntegerToString(statusCode));
            // Try reconnection on persistent failures
            if(statusCode == 0 || statusCode == 401) {
                m_isConnected = false;
            }
            return "";
        }
    }

    //+------------------------------------------------------------------+
    //| Queue trading commands for processing                           |
    //+------------------------------------------------------------------+
    void QueueCommands(string commandsJson)
    {
        if(StringLen(commandsJson) == 0) return;

        // Simple command queuing - add to array
        if(m_commandCount < ArraySize(m_pendingCommands) - 1) {
            m_pendingCommands[m_commandCount] = commandsJson;
            m_commandCount++;
        } else {
            Print("⚠️ Command queue full, dropping oldest command");
            // Shift array left and add new command
            for(int i = 0; i < ArraySize(m_pendingCommands) - 1; i++) {
                m_pendingCommands[i] = m_pendingCommands[i + 1];
            }
            m_pendingCommands[ArraySize(m_pendingCommands) - 1] = commandsJson;
        }
    }

    //+------------------------------------------------------------------+
    //| Get next queued command                                         |
    //+------------------------------------------------------------------+
    string GetNextCommand()
    {
        if(m_commandCount <= 0) return "";

        string command = m_pendingCommands[0];

        // Shift array left
        for(int i = 0; i < m_commandCount - 1; i++) {
            m_pendingCommands[i] = m_pendingCommands[i + 1];
        }
        m_commandCount--;

        return command;
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
    //| Check dual connection health                                    |
    //+------------------------------------------------------------------+
    bool IsHealthy()
    {
        bool tradingHealthy = m_isConnected && (TimeCurrent() - m_lastHeartbeat <= 120);
        bool priceStreamHealthy = m_isPriceStreamConnected && (TimeCurrent() - m_lastPriceStream <= 60);

        if(!tradingHealthy) {
            Print("⚠️ Trading connection unhealthy");
            m_isConnected = false;
        }

        if(!priceStreamHealthy) {
            Print("⚠️ Price stream connection unhealthy");
            m_isPriceStreamConnected = false;
        }

        // Auto-reconnect if needed
        if(!tradingHealthy || !priceStreamHealthy) {
            if(!m_isReconnecting) {
                Print("🔄 Initiating auto-reconnection...");
                m_isReconnecting = true;
                // Attempt reconnection
                bool reconnected = ConnectToServer();
                m_isReconnecting = false;
                return reconnected;
            }
        }

        return tradingHealthy && priceStreamHealthy;
    }

    //+------------------------------------------------------------------+
    //| Force reconnection                                              |
    //+------------------------------------------------------------------+
    bool Reconnect()
    {
        Print("🔄 Forcing reconnection to server...");
        m_isConnected = false;
        m_isPriceStreamConnected = false;
        m_connectionRetries++;

        if(m_connectionRetries > 5) {
            Print("❌ Max reconnection attempts reached");
            return false;
        }

        Sleep(2000); // Wait 2 seconds before retry
        return ConnectToServer();
    }

    //+------------------------------------------------------------------+
    //| Get dual connection status                                      |
    //+------------------------------------------------------------------+
    bool IsConnected() { return m_isConnected; }
    bool IsPriceStreamConnected() { return m_isPriceStreamConnected; }
    bool IsFullyConnected() { return m_isConnected && m_isPriceStreamConnected; }
    int GetRetryCount() { return m_connectionRetries; }
    datetime GetLastHeartbeat() { return m_lastHeartbeat; }
    datetime GetLastPriceStream() { return m_lastPriceStream; }
    int GetPendingCommandCount() { return m_commandCount; }

    //+------------------------------------------------------------------+
    //| Get connection statistics                                        |
    //+------------------------------------------------------------------+
    string GetConnectionStats()
    {
        string stats = "Connection Status:\n";
        stats += "Trading: " + (m_isConnected ? "Connected" : "Disconnected") + "\n";
        stats += "Price Stream: " + (m_isPriceStreamConnected ? "Connected" : "Disconnected") + "\n";
        stats += "Last Heartbeat: " + TimeToString(m_lastHeartbeat) + "\n";
        stats += "Last Price Stream: " + TimeToString(m_lastPriceStream) + "\n";
        stats += "Retry Count: " + IntegerToString(m_connectionRetries) + "\n";
        stats += "Pending Commands: " + IntegerToString(m_commandCount);
        return stats;
    }

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