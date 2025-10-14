//+------------------------------------------------------------------+
//|                                           UIEventSystem.mqh     |
//|                     Event system for UI-EA communication        |
//+------------------------------------------------------------------+
#ifndef UIEVENTSYSTEM_MQH
#define UIEVENTSYSTEM_MQH

//+------------------------------------------------------------------+
//| Global Variables for UI-EA Communication                        |
//+------------------------------------------------------------------+
#define UI_EVENT_PREFIX         "SuhoAI_"
#define UI_VAR_CONNECT_REQUEST  UI_EVENT_PREFIX + "ConnectRequest"
#define UI_VAR_DISCONNECT_REQUEST UI_EVENT_PREFIX + "DisconnectRequest"
#define UI_VAR_SETTINGS_REQUEST UI_EVENT_PREFIX + "SettingsRequest"
#define UI_VAR_BINARY_PROTOCOL  UI_EVENT_PREFIX + "BinaryProtocol"
#define UI_VAR_CURRENT_CHART    UI_EVENT_PREFIX + "CurrentChartOnly"
#define UI_VAR_CONNECTION_STATUS UI_EVENT_PREFIX + "ConnectionStatus"
#define UI_VAR_TRADING_STATUS   UI_EVENT_PREFIX + "TradingStatus"
#define UI_VAR_LAST_UPDATE      UI_EVENT_PREFIX + "LastUpdate"
#define UI_VAR_PERFORMANCE_LATENCY UI_EVENT_PREFIX + "Latency"
#define UI_VAR_PERFORMANCE_DATASIZE UI_EVENT_PREFIX + "DataSize"
#define UI_VAR_PERFORMANCE_PROTOCOL UI_EVENT_PREFIX + "Protocol"

//+------------------------------------------------------------------+
//| UI Event Manager Class                                           |
//+------------------------------------------------------------------+
class CUIEventManager
{
private:
    bool                m_initialized;
    datetime            m_lastCheck;
    enum ENUM_EVENT_CONSTANTS {
        CHECK_INTERVAL = 100 // milliseconds
    };

public:
                        CUIEventManager(void);
                       ~CUIEventManager(void);

    bool                Initialize(void);
    void                Shutdown(void);
    bool                CheckForUIEvents(void);

    // Event setters (from EA to UI)
    void                SetConnectionStatus(bool connected, string info = "");
    void                SetTradingStatus(string status);
    void                SetPerformanceMetrics(double latency, int dataSize, string protocol);
    void                SetLastUpdate(datetime timestamp);

    // Event getters (from UI to EA)
    bool                GetConnectRequest(void);
    bool                GetDisconnectRequest(void);
    bool                GetSettingsRequest(void);
    bool                GetBinaryProtocolSetting(void);
    bool                GetCurrentChartSetting(void);

    // Clear request flags
    void                ClearConnectRequest(void);
    void                ClearDisconnectRequest(void);
    void                ClearSettingsRequest(void);

    // Utility methods
    bool                IsInitialized(void) { return m_initialized; }
};

//+------------------------------------------------------------------+
//| Constructor                                                      |
//+------------------------------------------------------------------+
CUIEventManager::CUIEventManager(void) : m_initialized(false), m_lastCheck(0)
{
}

//+------------------------------------------------------------------+
//| Destructor                                                       |
//+------------------------------------------------------------------+
CUIEventManager::~CUIEventManager(void)
{
    Shutdown();
}

//+------------------------------------------------------------------+
//| Initialize event manager                                         |
//+------------------------------------------------------------------+
bool CUIEventManager::Initialize(void)
{
    if(m_initialized)
        return true;

    Print("[UI-EVENT] Initializing UI Event System...");

    // Initialize global variables with default values
    GlobalVariableSet(UI_VAR_CONNECT_REQUEST, 0);
    GlobalVariableSet(UI_VAR_DISCONNECT_REQUEST, 0);
    GlobalVariableSet(UI_VAR_SETTINGS_REQUEST, 0);
    GlobalVariableSet(UI_VAR_BINARY_PROTOCOL, 1); // Default to binary protocol
    GlobalVariableSet(UI_VAR_CURRENT_CHART, 0);   // Default to all pairs
    GlobalVariableSet(UI_VAR_CONNECTION_STATUS, 0);
    GlobalVariableSet(UI_VAR_TRADING_STATUS, 0);
    GlobalVariableSet(UI_VAR_LAST_UPDATE, TimeCurrent());
    GlobalVariableSet(UI_VAR_PERFORMANCE_LATENCY, 0);
    GlobalVariableSet(UI_VAR_PERFORMANCE_DATASIZE, 0);

    m_initialized = true;
    m_lastCheck = TimeCurrent();

    Print("[UI-EVENT] UI Event System initialized successfully");
    return true;
}

//+------------------------------------------------------------------+
//| Shutdown event manager                                           |
//+------------------------------------------------------------------+
void CUIEventManager::Shutdown(void)
{
    if(!m_initialized)
        return;

    Print("[UI-EVENT] Shutting down UI Event System...");

    // Clean up global variables
    GlobalVariableDel(UI_VAR_CONNECT_REQUEST);
    GlobalVariableDel(UI_VAR_DISCONNECT_REQUEST);
    GlobalVariableDel(UI_VAR_SETTINGS_REQUEST);
    GlobalVariableDel(UI_VAR_BINARY_PROTOCOL);
    GlobalVariableDel(UI_VAR_CURRENT_CHART);
    GlobalVariableDel(UI_VAR_CONNECTION_STATUS);
    GlobalVariableDel(UI_VAR_TRADING_STATUS);
    GlobalVariableDel(UI_VAR_LAST_UPDATE);
    GlobalVariableDel(UI_VAR_PERFORMANCE_LATENCY);
    GlobalVariableDel(UI_VAR_PERFORMANCE_DATASIZE);

    m_initialized = false;
    Print("[UI-EVENT] UI Event System shutdown complete");
}

//+------------------------------------------------------------------+
//| Check for UI events                                              |
//+------------------------------------------------------------------+
bool CUIEventManager::CheckForUIEvents(void)
{
    if(!m_initialized)
        return false;

    datetime currentTime = TimeCurrent();

    // Throttle checks to avoid excessive CPU usage
    if((currentTime - m_lastCheck) * 1000 < CHECK_INTERVAL)
        return false;

    m_lastCheck = currentTime;

    bool hasEvents = false;

    // Check for connect request
    if(GetConnectRequest())
    {
        Print("[UI-EVENT] Connect request detected");
        hasEvents = true;
    }

    // Check for disconnect request
    if(GetDisconnectRequest())
    {
        Print("[UI-EVENT] Disconnect request detected");
        hasEvents = true;
    }

    // Check for settings request
    if(GetSettingsRequest())
    {
        Print("[UI-EVENT] Settings request detected");
        hasEvents = true;
    }

    return hasEvents;
}

//+------------------------------------------------------------------+
//| Set connection status                                            |
//+------------------------------------------------------------------+
void CUIEventManager::SetConnectionStatus(bool connected, string info)
{
    if(!m_initialized)
        return;

    double status = connected ? 1.0 : 0.0;
    GlobalVariableSet(UI_VAR_CONNECTION_STATUS, status);

    // Store additional info in a string global variable name
    if(info != "")
    {
        string infoVar = UI_EVENT_PREFIX + "ConnectionInfo";
        // Since MQL5 doesn't support string global variables directly,
        // we'll encode the info in the variable name or use a comment approach
        Comment("Connection Info: " + info);
    }

    Print("[UI-EVENT] Connection status set: ", connected ? "CONNECTED" : "DISCONNECTED");
}

//+------------------------------------------------------------------+
//| Set trading status                                               |
//+------------------------------------------------------------------+
void CUIEventManager::SetTradingStatus(string status)
{
    if(!m_initialized)
        return;

    // Convert status string to numeric value for global variable
    double statusValue = 0;
    if(status == "Active") statusValue = 1;
    else if(status == "Paused") statusValue = 2;
    else if(status == "Error") statusValue = 3;

    GlobalVariableSet(UI_VAR_TRADING_STATUS, statusValue);
    Print("[UI-EVENT] Trading status set: ", status);
}

//+------------------------------------------------------------------+
//| Set performance metrics                                          |
//+------------------------------------------------------------------+
void CUIEventManager::SetPerformanceMetrics(double latency, int dataSize, string protocol)
{
    if(!m_initialized)
        return;

    GlobalVariableSet(UI_VAR_PERFORMANCE_LATENCY, latency);
    GlobalVariableSet(UI_VAR_PERFORMANCE_DATASIZE, dataSize);

    // Convert protocol string to numeric
    double protocolValue = 0;
    if(protocol == "Binary") protocolValue = 1;
    else if(protocol == "JSON") protocolValue = 2;

    GlobalVariableSet(UI_VAR_PERFORMANCE_PROTOCOL, protocolValue);

    Print("[UI-EVENT] Performance metrics updated - Latency: ", latency, "ms, Size: ", dataSize, " bytes, Protocol: ", protocol);
}

//+------------------------------------------------------------------+
//| Set last update timestamp                                        |
//+------------------------------------------------------------------+
void CUIEventManager::SetLastUpdate(datetime timestamp)
{
    if(!m_initialized)
        return;

    GlobalVariableSet(UI_VAR_LAST_UPDATE, timestamp);
}

//+------------------------------------------------------------------+
//| Get connect request                                              |
//+------------------------------------------------------------------+
bool CUIEventManager::GetConnectRequest(void)
{
    if(!m_initialized)
        return false;

    return GlobalVariableGet(UI_VAR_CONNECT_REQUEST) > 0;
}

//+------------------------------------------------------------------+
//| Get disconnect request                                           |
//+------------------------------------------------------------------+
bool CUIEventManager::GetDisconnectRequest(void)
{
    if(!m_initialized)
        return false;

    return GlobalVariableGet(UI_VAR_DISCONNECT_REQUEST) > 0;
}

//+------------------------------------------------------------------+
//| Get settings request                                             |
//+------------------------------------------------------------------+
bool CUIEventManager::GetSettingsRequest(void)
{
    if(!m_initialized)
        return false;

    return GlobalVariableGet(UI_VAR_SETTINGS_REQUEST) > 0;
}

//+------------------------------------------------------------------+
//| Get binary protocol setting                                     |
//+------------------------------------------------------------------+
bool CUIEventManager::GetBinaryProtocolSetting(void)
{
    if(!m_initialized)
        return true; // Default to binary

    return GlobalVariableGet(UI_VAR_BINARY_PROTOCOL) > 0;
}

//+------------------------------------------------------------------+
//| Get current chart setting                                       |
//+------------------------------------------------------------------+
bool CUIEventManager::GetCurrentChartSetting(void)
{
    if(!m_initialized)
        return false; // Default to all pairs

    return GlobalVariableGet(UI_VAR_CURRENT_CHART) > 0;
}

//+------------------------------------------------------------------+
//| Clear connect request                                            |
//+------------------------------------------------------------------+
void CUIEventManager::ClearConnectRequest(void)
{
    if(m_initialized)
        GlobalVariableSet(UI_VAR_CONNECT_REQUEST, 0);
}

//+------------------------------------------------------------------+
//| Clear disconnect request                                         |
//+------------------------------------------------------------------+
void CUIEventManager::ClearDisconnectRequest(void)
{
    if(m_initialized)
        GlobalVariableSet(UI_VAR_DISCONNECT_REQUEST, 0);
}

//+------------------------------------------------------------------+
//| Clear settings request                                           |
//+------------------------------------------------------------------+
void CUIEventManager::ClearSettingsRequest(void)
{
    if(m_initialized)
        GlobalVariableSet(UI_VAR_SETTINGS_REQUEST, 0);
}

//+------------------------------------------------------------------+
//| Helper functions for EA integration                             |
//+------------------------------------------------------------------+

// Global instance for easy access
CUIEventManager* g_UIEventManager = NULL;

//+------------------------------------------------------------------+
//| Initialize UI event system (call from EA OnInit)               |
//+------------------------------------------------------------------+
bool InitializeUIEventSystem(void)
{
    if(g_UIEventManager != NULL)
        return true;

    g_UIEventManager = new CUIEventManager();
    if(g_UIEventManager == NULL)
    {
        Print("[UI-EVENT] Failed to create UI Event Manager");
        return false;
    }

    return g_UIEventManager.Initialize();
}

//+------------------------------------------------------------------+
//| Shutdown UI event system (call from EA OnDeinit)              |
//+------------------------------------------------------------------+
void ShutdownUIEventSystem(void)
{
    if(g_UIEventManager != NULL)
    {
        g_UIEventManager.Shutdown();
        delete g_UIEventManager;
        g_UIEventManager = NULL;
    }
}

//+------------------------------------------------------------------+
//| Process UI events (call from EA OnTick or OnTimer)            |
//+------------------------------------------------------------------+
bool ProcessUIEvents(void)
{
    if(g_UIEventManager == NULL)
        return false;

    return g_UIEventManager.CheckForUIEvents();
}

//+------------------------------------------------------------------+
//| Update UI with EA status (convenience functions)              |
//+------------------------------------------------------------------+
void UpdateUIConnectionStatus(bool connected, string info = "")
{
    if(g_UIEventManager != NULL)
        g_UIEventManager.SetConnectionStatus(connected, info);
}

void UpdateUITradingStatus(string status)
{
    if(g_UIEventManager != NULL)
        g_UIEventManager.SetTradingStatus(status);
}

void UpdateUIPerformanceMetrics(double latency, int dataSize, string protocol)
{
    if(g_UIEventManager != NULL)
        g_UIEventManager.SetPerformanceMetrics(latency, dataSize, protocol);
}

//+------------------------------------------------------------------+
//| Get UI settings (convenience functions)                        |
//+------------------------------------------------------------------+
bool GetUIBinaryProtocolSetting(void)
{
    return (g_UIEventManager != NULL) ? g_UIEventManager.GetBinaryProtocolSetting() : true;
}

bool GetUICurrentChartSetting(void)
{
    return (g_UIEventManager != NULL) ? g_UIEventManager.GetCurrentChartSetting() : false;
}

#endif // UIEVENTSYSTEM_MQH