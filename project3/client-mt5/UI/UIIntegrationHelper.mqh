//+------------------------------------------------------------------+
//|                                     UIIntegrationHelper.mqh     |
//|                     Helper functions for integrating UI with EA  |
//+------------------------------------------------------------------+
#ifndef UIINTEGRATIONHELPER_MQH
#define UIINTEGRATIONHELPER_MQH

#include "BasicDashboard.mqh"
#include "SettingsPanel.mqh"
#include "UIEventSystem.mqh"

//+------------------------------------------------------------------+
//| UI Integration Manager Class                                     |
//+------------------------------------------------------------------+
class CUIIntegrationManager
{
private:
    CBasicDashboard*     m_dashboard;
    CSettingsPanel*      m_settingsPanel;
    bool                 m_initialized;
    bool                 m_dashboardVisible;
    bool                 m_settingsVisible;

public:
                        CUIIntegrationManager(void);
                       ~CUIIntegrationManager(void);

    // Main interface
    bool                Initialize(void);
    void                Shutdown(void);
    void                ProcessUIEvents(void);

    // Dashboard management
    void                ShowDashboard(void);
    void                HideDashboard(void);
    void                UpdateDashboard(bool connected, string serverInfo, double latency, int dataSize, string protocol);

    // Settings management
    void                ShowSettings(void);
    void                HideSettings(void);
    SSettingsData       GetCurrentSettings(void);

    // Status updates
    void                UpdateConnectionStatus(bool connected, string info = "");
    void                UpdateTradingStatus(string status);
    void                UpdatePerformanceMetrics(double latency, int dataSize, string protocol);

    // Event handlers for EA integration
    bool                CheckConnectRequest(void);
    bool                CheckDisconnectRequest(void);
    bool                CheckSettingsRequest(void);
    bool                GetBinaryProtocolSetting(void);
    bool                GetCurrentChartSetting(void);

    // State getters
    bool                IsInitialized(void) { return m_initialized; }
    bool                IsDashboardVisible(void) { return m_dashboardVisible; }
    bool                IsSettingsVisible(void) { return m_settingsVisible; }
};

//+------------------------------------------------------------------+
//| Constructor                                                      |
//+------------------------------------------------------------------+
CUIIntegrationManager::CUIIntegrationManager(void) : m_dashboard(NULL), m_settingsPanel(NULL), m_initialized(false),
                                                      m_dashboardVisible(false), m_settingsVisible(false)
{
}

//+------------------------------------------------------------------+
//| Destructor                                                       |
//+------------------------------------------------------------------+
CUIIntegrationManager::~CUIIntegrationManager(void)
{
    Shutdown();
}

//+------------------------------------------------------------------+
//| Initialize UI system                                             |
//+------------------------------------------------------------------+
bool CUIIntegrationManager::Initialize(void)
{
    if(m_initialized)
        return true;

    Print("[UI-INTEGRATION] Initializing UI Integration Manager...");

    // Initialize event system first
    if(!InitializeUIEventSystem())
    {
        Print("[UI-INTEGRATION] Failed to initialize UI event system");
        return false;
    }

    // Create dashboard
    m_dashboard = new CBasicDashboard();
    if(m_dashboard == NULL)
    {
        Print("[UI-INTEGRATION] Failed to create dashboard");
        return false;
    }

    if(!m_dashboard.Initialize())
    {
        Print("[UI-INTEGRATION] Failed to initialize dashboard");
        delete m_dashboard;
        m_dashboard = NULL;
        return false;
    }

    // Create settings panel
    m_settingsPanel = new CSettingsPanel();
    if(m_settingsPanel == NULL)
    {
        Print("[UI-INTEGRATION] Failed to create settings panel");
        return false;
    }

    if(!m_settingsPanel.Initialize())
    {
        Print("[UI-INTEGRATION] Failed to initialize settings panel");
        delete m_settingsPanel;
        m_settingsPanel = NULL;
        return false;
    }

    m_initialized = true;
    m_dashboardVisible = true; // Dashboard is shown by default

    Print("[UI-INTEGRATION] UI Integration Manager initialized successfully");
    return true;
}

//+------------------------------------------------------------------+
//| Shutdown UI system                                               |
//+------------------------------------------------------------------+
void CUIIntegrationManager::Shutdown(void)
{
    if(!m_initialized)
        return;

    Print("[UI-INTEGRATION] Shutting down UI Integration Manager...");

    // Hide UI components
    HideDashboard();
    HideSettings();

    // Destroy components
    if(m_dashboard != NULL)
    {
        m_dashboard.Shutdown();
        delete m_dashboard;
        m_dashboard = NULL;
    }

    if(m_settingsPanel != NULL)
    {
        delete m_settingsPanel;
        m_settingsPanel = NULL;
    }

    // Shutdown event system
    ShutdownUIEventSystem();

    m_initialized = false;
    m_dashboardVisible = false;
    m_settingsVisible = false;

    Print("[UI-INTEGRATION] UI Integration Manager shutdown complete");
}

//+------------------------------------------------------------------+
//| Process UI events                                                |
//+------------------------------------------------------------------+
void CUIIntegrationManager::ProcessUIEvents(void)
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

    // Check for settings requests
    if(CheckSettingsRequest())
    {
        ShowSettings();
        g_UIEventManager.ClearSettingsRequest();
    }
}

//+------------------------------------------------------------------+
//| Show dashboard                                                   |
//+------------------------------------------------------------------+
void CUIIntegrationManager::ShowDashboard(void)
{
    if(m_dashboard != NULL && !m_dashboardVisible)
    {
        // Dashboard is initialized to be visible, so we just need to track state
        m_dashboardVisible = true;
        Print("[UI-INTEGRATION] Dashboard shown");
    }
}

//+------------------------------------------------------------------+
//| Hide dashboard                                                   |
//+------------------------------------------------------------------+
void CUIIntegrationManager::HideDashboard(void)
{
    if(m_dashboard != NULL && m_dashboardVisible)
    {
        // In a full implementation, this would hide the dashboard
        // For now, we just track the state
        m_dashboardVisible = false;
        Print("[UI-INTEGRATION] Dashboard hidden");
    }
}

//+------------------------------------------------------------------+
//| Update dashboard with current data                               |
//+------------------------------------------------------------------+
void CUIIntegrationManager::UpdateDashboard(bool connected, string serverInfo, double latency, int dataSize, string protocol)
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
//| Show settings panel                                              |
//+------------------------------------------------------------------+
void CUIIntegrationManager::ShowSettings(void)
{
    if(m_settingsPanel != NULL && !m_settingsVisible)
    {
        m_settingsPanel.ShowSettings();
        m_settingsVisible = true;
        Print("[UI-INTEGRATION] Settings panel shown");
    }
}

//+------------------------------------------------------------------+
//| Hide settings panel                                              |
//+------------------------------------------------------------------+
void CUIIntegrationManager::HideSettings(void)
{
    if(m_settingsPanel != NULL && m_settingsVisible)
    {
        m_settingsPanel.HideSettings();
        m_settingsVisible = false;
        Print("[UI-INTEGRATION] Settings panel hidden");
    }
}

//+------------------------------------------------------------------+
//| Get current settings                                             |
//+------------------------------------------------------------------+
SSettingsData CUIIntegrationManager::GetCurrentSettings(void)
{
    SSettingsData emptySettings = {};
    if(m_settingsPanel != NULL)
    {
        return m_settingsPanel.GetSettings();
    }
    return emptySettings;
}

//+------------------------------------------------------------------+
//| Update connection status                                         |
//+------------------------------------------------------------------+
void CUIIntegrationManager::UpdateConnectionStatus(bool connected, string info)
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
void CUIIntegrationManager::UpdateTradingStatus(string status)
{
    UpdateUITradingStatus(status);
}

//+------------------------------------------------------------------+
//| Update performance metrics                                       |
//+------------------------------------------------------------------+
void CUIIntegrationManager::UpdatePerformanceMetrics(double latency, int dataSize, string protocol)
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
bool CUIIntegrationManager::CheckConnectRequest(void)
{
    if(g_UIEventManager != NULL && g_UIEventManager.GetConnectRequest())
    {
        g_UIEventManager.ClearConnectRequest();
        return true;
    }
    return false;
}

bool CUIIntegrationManager::CheckDisconnectRequest(void)
{
    if(g_UIEventManager != NULL && g_UIEventManager.GetDisconnectRequest())
    {
        g_UIEventManager.ClearDisconnectRequest();
        return true;
    }
    return false;
}

bool CUIIntegrationManager::CheckSettingsRequest(void)
{
    return (g_UIEventManager != NULL) ? g_UIEventManager.GetSettingsRequest() : false;
}

bool CUIIntegrationManager::GetBinaryProtocolSetting(void)
{
    return GetUIBinaryProtocolSetting();
}

bool CUIIntegrationManager::GetCurrentChartSetting(void)
{
    return GetUICurrentChartSetting();
}

//+------------------------------------------------------------------+
//| Global UI Manager Instance                                       |
//+------------------------------------------------------------------+
CUIIntegrationManager* g_UIManager = NULL;

//+------------------------------------------------------------------+
//| EA Integration Functions                                         |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| Initialize UI for EA (call from OnInit)                        |
//+------------------------------------------------------------------+
bool InitializeUI(void)
{
    if(g_UIManager != NULL)
        return true;

    g_UIManager = new CUIIntegrationManager();
    if(g_UIManager == NULL)
    {
        Print("[UI-INTEGRATION] Failed to create UI Manager");
        return false;
    }

    if(!g_UIManager.Initialize())
    {
        delete g_UIManager;
        g_UIManager = NULL;
        return false;
    }

    return true;
}

//+------------------------------------------------------------------+
//| Shutdown UI for EA (call from OnDeinit)                        |
//+------------------------------------------------------------------+
void ShutdownUI(void)
{
    if(g_UIManager != NULL)
    {
        g_UIManager.Shutdown();
        delete g_UIManager;
        g_UIManager = NULL;
    }
}

//+------------------------------------------------------------------+
//| Process UI events for EA (call from OnTick or OnTimer)         |
//+------------------------------------------------------------------+
void ProcessEAUIEvents(void)
{
    if(g_UIManager != NULL)
    {
        g_UIManager.ProcessUIEvents();
    }
}

//+------------------------------------------------------------------+
//| Update UI with EA data (convenience functions)                 |
//+------------------------------------------------------------------+
void UpdateEAUIConnectionStatus(bool connected, string info = "")
{
    if(g_UIManager != NULL)
        g_UIManager.UpdateConnectionStatus(connected, info);
}

void UpdateEAUITradingStatus(string status)
{
    if(g_UIManager != NULL)
        g_UIManager.UpdateTradingStatus(status);
}

void UpdateEAUIPerformanceMetrics(double latency, int dataSize, string protocol)
{
    if(g_UIManager != NULL)
        g_UIManager.UpdatePerformanceMetrics(latency, dataSize, protocol);
}

void UpdateEAUIDashboard(bool connected, string serverInfo, double latency, int dataSize, string protocol)
{
    if(g_UIManager != NULL)
        g_UIManager.UpdateDashboard(connected, serverInfo, latency, dataSize, protocol);
}

//+------------------------------------------------------------------+
//| Check for UI requests (for EA event handling)                  |
//+------------------------------------------------------------------+
bool CheckUIConnectRequest(void)
{
    return (g_UIManager != NULL) ? g_UIManager.CheckConnectRequest() : false;
}

bool CheckUIDisconnectRequest(void)
{
    return (g_UIManager != NULL) ? g_UIManager.CheckDisconnectRequest() : false;
}

bool CheckUISettingsRequest(void)
{
    return (g_UIManager != NULL) ? g_UIManager.CheckSettingsRequest() : false;
}

bool GetUIBinaryProtocolPreference(void)
{
    return (g_UIManager != NULL) ? g_UIManager.GetBinaryProtocolSetting() : true;
}

bool GetUICurrentChartPreference(void)
{
    return (g_UIManager != NULL) ? g_UIManager.GetCurrentChartSetting() : false;
}

#endif // UIINTEGRATIONHELPER_MQH