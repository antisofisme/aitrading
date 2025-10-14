//+------------------------------------------------------------------+
//|                                   SimpleUIIntegration.mqh      |
//|                     Simple UI integration for EA               |
//+------------------------------------------------------------------+
#ifndef SIMPLEUIINTEGRATION_MQH
#define SIMPLEUIINTEGRATION_MQH

#include "SimpleDashboard.mqh"

//+------------------------------------------------------------------+
//| Simple UI Integration Manager Class                             |
//+------------------------------------------------------------------+
class CSimpleUIManager
{
private:
    CSimpleDashboard*    m_dashboard;
    bool                 m_initialized;
    bool                 m_dashboardVisible;

public:
                        CSimpleUIManager(void);
                       ~CSimpleUIManager(void);

    // Main interface
    bool                Initialize(void);
    void                Shutdown(void);
    void                ProcessUIEvents(void);

    // Dashboard management
    void                ShowDashboard(void);
    void                HideDashboard(void);
    void                UpdateDashboard(bool connected, string serverInfo, double latency, int dataSize, string protocol);

    // Status updates
    void                UpdateConnectionStatus(bool connected, string info = "");
    void                UpdateTradingStatus(string status);
    void                UpdatePerformanceMetrics(double latency, int dataSize, string protocol);

    // Event handlers for EA integration
    bool                CheckConnectRequest(void);
    bool                CheckDisconnectRequest(void);
    bool                GetBinaryProtocolSetting(void);
    bool                GetCurrentChartSetting(void);

    // State getters
    bool                IsInitialized(void) { return m_initialized; }
    bool                IsDashboardVisible(void) { return m_dashboardVisible; }
};

//+------------------------------------------------------------------+
//| Constructor                                                      |
//+------------------------------------------------------------------+
CSimpleUIManager::CSimpleUIManager(void) : m_dashboard(NULL), m_initialized(false), m_dashboardVisible(false)
{
}

//+------------------------------------------------------------------+
//| Destructor                                                       |
//+------------------------------------------------------------------+
CSimpleUIManager::~CSimpleUIManager(void)
{
    Shutdown();
}

//+------------------------------------------------------------------+
//| Initialize UI system                                             |
//+------------------------------------------------------------------+
bool CSimpleUIManager::Initialize(void)
{
    if(m_initialized)
        return true;

    Print("[UI-SIMPLE] Initializing Simple UI Manager...");

    // Initialize event system first
    if(!InitializeUIEventSystem())
    {
        Print("[UI-SIMPLE] Failed to initialize UI event system");
        return false;
    }

    // Create dashboard
    m_dashboard = new CSimpleDashboard();
    if(m_dashboard == NULL)
    {
        Print("[UI-SIMPLE] Failed to create dashboard");
        return false;
    }

    if(!m_dashboard.Initialize())
    {
        Print("[UI-SIMPLE] Failed to initialize dashboard");
        delete m_dashboard;
        m_dashboard = NULL;
        return false;
    }

    m_initialized = true;
    m_dashboardVisible = true; // Dashboard is shown by default

    Print("[UI-SIMPLE] Simple UI Manager initialized successfully");
    return true;
}

//+------------------------------------------------------------------+
//| Shutdown UI system                                               |
//+------------------------------------------------------------------+
void CSimpleUIManager::Shutdown(void)
{
    if(!m_initialized)
        return;

    Print("[UI-SIMPLE] Shutting down Simple UI Manager...");

    // Hide UI components
    HideDashboard();

    // Destroy components
    if(m_dashboard != NULL)
    {
        m_dashboard.Shutdown();
        delete m_dashboard;
        m_dashboard = NULL;
    }

    // Shutdown event system
    ShutdownUIEventSystem();

    m_initialized = false;
    m_dashboardVisible = false;

    Print("[UI-SIMPLE] Simple UI Manager shutdown complete");
}

//+------------------------------------------------------------------+
//| Process UI events                                                |
//+------------------------------------------------------------------+
void CSimpleUIManager::ProcessUIEvents(void)
{
    if(!m_initialized)
        return;

    // Process UI events
    ProcessUIEvents();

    // Update dashboard if visible
    if(m_dashboardVisible && m_dashboard != NULL)
    {
        m_dashboard.UpdateAll();
    }
}

//+------------------------------------------------------------------+
//| Show dashboard                                                   |
//+------------------------------------------------------------------+
void CSimpleUIManager::ShowDashboard(void)
{
    if(m_dashboard != NULL && !m_dashboardVisible)
    {
        m_dashboard.Show(true);
        m_dashboardVisible = true;
        Print("[UI-SIMPLE] Dashboard shown");
    }
}

//+------------------------------------------------------------------+
//| Hide dashboard                                                   |
//+------------------------------------------------------------------+
void CSimpleUIManager::HideDashboard(void)
{
    if(m_dashboard != NULL && m_dashboardVisible)
    {
        m_dashboard.Hide();
        m_dashboardVisible = false;
        Print("[UI-SIMPLE] Dashboard hidden");
    }
}

//+------------------------------------------------------------------+
//| Update dashboard with current data                               |
//+------------------------------------------------------------------+
void CSimpleUIManager::UpdateDashboard(bool connected, string serverInfo, double latency, int dataSize, string protocol)
{
    if(m_dashboard != NULL)
    {
        m_dashboard.UpdateConnectionStatus(connected, serverInfo);
        m_dashboard.UpdatePerformanceMetrics(latency, dataSize, protocol);
        m_dashboard.UpdateAccountData();
    }

    // Update event system
    UpdateConnectionStatus(connected, serverInfo);
    UpdatePerformanceMetrics(latency, dataSize, protocol);
}

//+------------------------------------------------------------------+
//| Update connection status                                         |
//+------------------------------------------------------------------+
void CSimpleUIManager::UpdateConnectionStatus(bool connected, string info)
{
    UpdateUIConnectionStatus(connected, info);

    if(m_dashboard != NULL)
    {
        m_dashboard.UpdateConnectionStatus(connected, info);
    }
}

//+------------------------------------------------------------------+
//| Update trading status                                            |
//+------------------------------------------------------------------+
void CSimpleUIManager::UpdateTradingStatus(string status)
{
    UpdateUITradingStatus(status);

    if(m_dashboard != NULL && m_dashboard.IsInitialized())
    {
        // Simple dashboard doesn't have separate trading status update
        // Status is shown in connection status
    }
}

//+------------------------------------------------------------------+
//| Update performance metrics                                       |
//+------------------------------------------------------------------+
void CSimpleUIManager::UpdatePerformanceMetrics(double latency, int dataSize, string protocol)
{
    UpdateUIPerformanceMetrics(latency, dataSize, protocol);

    if(m_dashboard != NULL)
    {
        m_dashboard.UpdatePerformanceMetrics(latency, dataSize, protocol);
    }
}

//+------------------------------------------------------------------+
//| Event checkers for EA integration                               |
//+------------------------------------------------------------------+
bool CSimpleUIManager::CheckConnectRequest(void)
{
    if(g_UIEventManager != NULL && g_UIEventManager.GetConnectRequest())
    {
        g_UIEventManager.ClearConnectRequest();
        return true;
    }
    return false;
}

bool CSimpleUIManager::CheckDisconnectRequest(void)
{
    if(g_UIEventManager != NULL && g_UIEventManager.GetDisconnectRequest())
    {
        g_UIEventManager.ClearDisconnectRequest();
        return true;
    }
    return false;
}

bool CSimpleUIManager::GetBinaryProtocolSetting(void)
{
    return GetUIBinaryProtocolSetting();
}

bool CSimpleUIManager::GetCurrentChartSetting(void)
{
    return GetUICurrentChartSetting();
}

//+------------------------------------------------------------------+
//| Global Simple UI Manager Instance                               |
//+------------------------------------------------------------------+
CSimpleUIManager* g_SimpleUIManager = NULL;

//+------------------------------------------------------------------+
//| EA Integration Functions                                         |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Initialize Simple UI for EA (call from OnInit)                 |
//+------------------------------------------------------------------+
bool InitializeSimpleUI(void)
{
    if(g_SimpleUIManager != NULL)
        return true;

    g_SimpleUIManager = new CSimpleUIManager();
    if(g_SimpleUIManager == NULL)
    {
        Print("[UI-SIMPLE] Failed to create Simple UI Manager");
        return false;
    }

    if(!g_SimpleUIManager.Initialize())
    {
        delete g_SimpleUIManager;
        g_SimpleUIManager = NULL;
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Shutdown Simple UI for EA (call from OnDeinit)                |
//+------------------------------------------------------------------+
void ShutdownSimpleUI(void)
{
    if(g_SimpleUIManager != NULL)
    {
        g_SimpleUIManager.Shutdown();
        delete g_SimpleUIManager;
        g_SimpleUIManager = NULL;
    }
}

//+------------------------------------------------------------------+
//| Process Simple UI events for EA (call from OnTick or OnTimer) |
//+------------------------------------------------------------------+
void ProcessSimpleUIEvents(void)
{
    if(g_SimpleUIManager != NULL)
    {
        g_SimpleUIManager.ProcessUIEvents();
    }
}

//+------------------------------------------------------------------+
//| Update Simple UI with EA data (convenience functions)         |
//+------------------------------------------------------------------+
void UpdateSimpleUIConnectionStatus(bool connected, string info = "")
{
    if(g_SimpleUIManager != NULL)
        g_SimpleUIManager.UpdateConnectionStatus(connected, info);
}

void UpdateSimpleUITradingStatus(string status)
{
    if(g_SimpleUIManager != NULL)
        g_SimpleUIManager.UpdateTradingStatus(status);
}

void UpdateSimpleUIPerformanceMetrics(double latency, int dataSize, string protocol)
{
    if(g_SimpleUIManager != NULL)
        g_SimpleUIManager.UpdatePerformanceMetrics(latency, dataSize, protocol);
}

void UpdateSimpleUIDashboard(bool connected, string serverInfo, double latency, int dataSize, string protocol)
{
    if(g_SimpleUIManager != NULL)
        g_SimpleUIManager.UpdateDashboard(connected, serverInfo, latency, dataSize, protocol);
}

//+------------------------------------------------------------------+
//| Check for Simple UI requests (for EA event handling)          |
//+------------------------------------------------------------------+
bool CheckSimpleUIConnectRequest(void)
{
    return (g_SimpleUIManager != NULL) ? g_SimpleUIManager.CheckConnectRequest() : false;
}

bool CheckSimpleUIDisconnectRequest(void)
{
    return (g_SimpleUIManager != NULL) ? g_SimpleUIManager.CheckDisconnectRequest() : false;
}

bool GetSimpleUIBinaryProtocolPreference(void)
{
    return (g_SimpleUIManager != NULL) ? g_SimpleUIManager.GetBinaryProtocolSetting() : true;
}

bool GetSimpleUICurrentChartPreference(void)
{
    return (g_SimpleUIManager != NULL) ? g_SimpleUIManager.GetCurrentChartSetting() : false;
}

#endif // SIMPLEUIINTEGRATION_MQH