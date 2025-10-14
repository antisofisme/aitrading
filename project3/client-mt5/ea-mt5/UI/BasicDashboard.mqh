//+------------------------------------------------------------------+
//|                                           BasicDashboard.mqh    |
//|                     Main dashboard interface for Suho AI Trading |
//+------------------------------------------------------------------+
#ifndef BASICDASHBOARD_MQH
#define BASICDASHBOARD_MQH

#include "UIComponents.mqh"
#include <Controls/Dialog.mqh>

//+------------------------------------------------------------------+
//| Dashboard Events                                                 |
//+------------------------------------------------------------------+
enum ENUM_DASHBOARD_EVENT
{
    EVENT_CONNECT_CLICKED,
    EVENT_DISCONNECT_CLICKED,
    EVENT_SETTINGS_CLICKED,
    EVENT_PROTOCOL_CHANGED,
    EVENT_CHART_MODE_CHANGED
};

//+------------------------------------------------------------------+
//| Dashboard Event Structure                                        |
//+------------------------------------------------------------------+
struct SDashboardEvent
{
    ENUM_DASHBOARD_EVENT  type;
    string                data;
    datetime              timestamp;
};

//+------------------------------------------------------------------+
//| Main Dashboard Class                                             |
//+------------------------------------------------------------------+
class CBasicDashboard : public CAppDialog
{
private:
    // UI Components
    CStatusDisplay*      m_statusDisplay;
    CAccountInfoDisplay* m_accountInfo;
    CTradingPairs*       m_tradingPairs;
    CControlPanel*       m_controlPanel;
    CPerformanceMetrics* m_performanceMetrics;

    // Dashboard state
    bool                 m_isInitialized;
    bool                 m_isConnected;
    bool                 m_useBinaryProtocol;
    bool                 m_streamCurrentChartOnly;
    datetime             m_lastUpdate;

    // Event handling
    SDashboardEvent      m_eventQueue[];
    int                  m_eventCount;

    // Layout constants
    enum ENUM_LAYOUT_CONSTANTS {
        DASHBOARD_WIDTH = 400,
        DASHBOARD_HEIGHT = 600,
        COMPONENT_SPACING = 10
    };

public:
                        CBasicDashboard(void);
                       ~CBasicDashboard(void);

    // Main interface
    bool                Initialize(void);
    void                Shutdown(void);
    bool                Create(const long chart, const string name, const int subwin, const int x1, const int y1, const int x2, const int y2);
    void                Destroy(const int reason = 0) override;

    // Update methods
    void                UpdateAll(void);
    void                UpdateConnectionStatus(bool connected, string serverInfo = "");
    void                UpdateAccountData(void);
    void                UpdateTradingPairs(string &pairs[]);
    void                UpdatePerformanceMetrics(double latency, int dataSize, string protocol);

    // Event handling
    bool                OnEvent(const int id, const long &lparam, const double &dparam, const string &sparam) override;
    void                ProcessEvents(void);
    bool                AddEvent(ENUM_DASHBOARD_EVENT type, string data = "");

    // Settings
    void                SetBinaryProtocol(bool enabled) { m_useBinaryProtocol = enabled; }
    void                SetChartMode(bool currentChartOnly) { m_streamCurrentChartOnly = currentChartOnly; }
    bool                GetBinaryProtocol(void) { return m_useBinaryProtocol; }
    bool                GetChartMode(void) { return m_streamCurrentChartOnly; }

    // State getters
    bool                IsInitialized(void) { return m_isInitialized; }
    bool                IsConnected(void) { return m_isConnected; }
    datetime            GetLastUpdate(void) { return m_lastUpdate; }

protected:
    // Layout methods
    void                CreateLayout(void);
    void                PositionComponents(void);

    // Event processors
    void                OnConnectClicked(void);
    void                OnDisconnectClicked(void);
    void                OnSettingsClicked(void);
    void                OnProtocolChanged(void);
    void                OnChartModeChanged(void);
};

//+------------------------------------------------------------------+
//| Constructor                                                      |
//+------------------------------------------------------------------+
CBasicDashboard::CBasicDashboard(void) : m_statusDisplay(NULL), m_accountInfo(NULL), m_tradingPairs(NULL),
                                         m_controlPanel(NULL), m_performanceMetrics(NULL), m_isInitialized(false),
                                         m_isConnected(false), m_useBinaryProtocol(true), m_streamCurrentChartOnly(false),
                                         m_lastUpdate(0), m_eventCount(0)
{
}

//+------------------------------------------------------------------+
//| Destructor                                                       |
//+------------------------------------------------------------------+
CBasicDashboard::~CBasicDashboard(void)
{
    Shutdown();
}

//+------------------------------------------------------------------+
//| Initialize dashboard                                             |
//+------------------------------------------------------------------+
bool CBasicDashboard::Initialize(void)
{
    if(m_isInitialized)
        return true;

    Print("[DASHBOARD] Initializing Suho AI Trading Dashboard...");

    // Create main dialog
    if(!Create(0, "SuhoAI_Dashboard", 0, 50, 50, 50 + DASHBOARD_WIDTH, 50 + DASHBOARD_HEIGHT))
    {
        Print("[DASHBOARD] Failed to create main dialog");
        return false;
    }

    // Set dialog properties
    Caption("Suho AI Trading Dashboard");
    // ColorBackground(UI_COLOR_BACKGROUND);
    // ColorBorder(UI_COLOR_BORDER);

    // Create layout
    CreateLayout();

    m_isInitialized = true;
    m_lastUpdate = TimeCurrent();

    Print("[DASHBOARD] Dashboard initialized successfully");
    return true;
}

//+------------------------------------------------------------------+
//| Create dashboard layout                                          |
//+------------------------------------------------------------------+
void CBasicDashboard::CreateLayout(void)
{
    int currentY = COMPONENT_SPACING;

    // Status Display (top)
    m_statusDisplay = new CStatusDisplay();
    if(m_statusDisplay != NULL)
    {
        m_statusDisplay.Create(COMPONENT_SPACING, currentY, DASHBOARD_WIDTH - (2 * COMPONENT_SPACING), 80, "StatusDisplay");
        currentY += 80 + COMPONENT_SPACING;
    }

    // Control Panel
    m_controlPanel = new CControlPanel();
    if(m_controlPanel != NULL)
    {
        m_controlPanel.Create(COMPONENT_SPACING, currentY, DASHBOARD_WIDTH - (2 * COMPONENT_SPACING), 100, "ControlPanel");
        currentY += 100 + COMPONENT_SPACING;
    }

    // Account Info
    m_accountInfo = new CAccountInfoDisplay();
    if(m_accountInfo != NULL)
    {
        m_accountInfo.Create(COMPONENT_SPACING, currentY, DASHBOARD_WIDTH - (2 * COMPONENT_SPACING), 120, "AccountInfo");
        currentY += 120 + COMPONENT_SPACING;
    }

    // Trading Pairs
    m_tradingPairs = new CTradingPairs();
    if(m_tradingPairs != NULL)
    {
        m_tradingPairs.Create(COMPONENT_SPACING, currentY, DASHBOARD_WIDTH - (2 * COMPONENT_SPACING), 150, "TradingPairs");
        currentY += 150 + COMPONENT_SPACING;
    }

    // Performance Metrics
    m_performanceMetrics = new CPerformanceMetrics();
    if(m_performanceMetrics != NULL)
    {
        m_performanceMetrics.Create(COMPONENT_SPACING, currentY, DASHBOARD_WIDTH - (2 * COMPONENT_SPACING), 100, "PerformanceMetrics");
    }

    Print("[DASHBOARD] Layout created with ", (m_statusDisplay != NULL) + (m_controlPanel != NULL) + (m_accountInfo != NULL) + (m_tradingPairs != NULL) + (m_performanceMetrics != NULL), " components");
}

//+------------------------------------------------------------------+
//| Update all components                                            |
//+------------------------------------------------------------------+
void CBasicDashboard::UpdateAll(void)
{
    if(!m_isInitialized)
        return;

    m_lastUpdate = TimeCurrent();

    // Update all components
    if(m_statusDisplay != NULL)
        m_statusDisplay.Update();

    if(m_accountInfo != NULL)
        m_accountInfo.Update();

    if(m_tradingPairs != NULL)
        m_tradingPairs.Update();

    if(m_controlPanel != NULL)
        m_controlPanel.Update();

    if(m_performanceMetrics != NULL)
        m_performanceMetrics.Update();

    // Process any pending events
    ProcessEvents();

    // Refresh display
    // ChartRedraw();
}

//+------------------------------------------------------------------+
//| Update connection status                                         |
//+------------------------------------------------------------------+
void CBasicDashboard::UpdateConnectionStatus(bool connected, string serverInfo)
{
    m_isConnected = connected;

    if(m_statusDisplay != NULL)
    {
        string status = connected ? "Connected" : "Disconnected";
        color statusColor = connected ? UI_COLOR_PROFIT : UI_COLOR_LOSS;

        if(connected && serverInfo != "")
            status += " (" + serverInfo + ")";

        m_statusDisplay.SetConnectionStatus(status, statusColor);
        m_statusDisplay.SetLastUpdate(TimeCurrent());
    }

    Print("[DASHBOARD] Connection status updated: ", connected ? "CONNECTED" : "DISCONNECTED");
}

//+------------------------------------------------------------------+
//| Update account data                                              |
//+------------------------------------------------------------------+
void CBasicDashboard::UpdateAccountData(void)
{
    if(m_accountInfo != NULL)
    {
        m_accountInfo.Update();
    }
}

//+------------------------------------------------------------------+
//| Update trading pairs                                             |
//+------------------------------------------------------------------+
void CBasicDashboard::UpdateTradingPairs(string &pairs[])
{
    if(m_tradingPairs != NULL)
    {
        m_tradingPairs.SetTradingPairs(pairs);
        m_tradingPairs.Update();
    }
}

//+------------------------------------------------------------------+
//| Update performance metrics                                       |
//+------------------------------------------------------------------+
void CBasicDashboard::UpdatePerformanceMetrics(double latency, int dataSize, string protocol)
{
    if(m_performanceMetrics != NULL)
    {
        m_performanceMetrics.SetLatency(latency);
        m_performanceMetrics.SetProtocolStats(protocol, dataSize);
        m_performanceMetrics.Update();
    }
}

//+------------------------------------------------------------------+
//| Event handling                                                   |
//+------------------------------------------------------------------+
bool CBasicDashboard::OnEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
    // Handle UI events
    switch(id)
    {
        case CHARTEVENT_OBJECT_CLICK:
        {
            if(StringFind(sparam, "Connect") >= 0)
            {
                AddEvent(EVENT_CONNECT_CLICKED);
                return true;
            }
            else if(StringFind(sparam, "Disconnect") >= 0)
            {
                AddEvent(EVENT_DISCONNECT_CLICKED);
                return true;
            }
            else if(StringFind(sparam, "Settings") >= 0)
            {
                AddEvent(EVENT_SETTINGS_CLICKED);
                return true;
            }
            break;
        }

        case CHARTEVENT_OBJECT_CHANGE:
        {
            if(StringFind(sparam, "BinaryProtocol") >= 0)
            {
                AddEvent(EVENT_PROTOCOL_CHANGED);
                return true;
            }
            else if(StringFind(sparam, "CurrentChart") >= 0)
            {
                AddEvent(EVENT_CHART_MODE_CHANGED);
                return true;
            }
            break;
        }
    }

    return CAppDialog::OnEvent(id, lparam, dparam, sparam);
}

//+------------------------------------------------------------------+
//| Process events                                                   |
//+------------------------------------------------------------------+
void CBasicDashboard::ProcessEvents(void)
{
    for(int i = 0; i < m_eventCount; i++)
    {
        switch(m_eventQueue[i].type)
        {
            case EVENT_CONNECT_CLICKED:
                OnConnectClicked();
                break;

            case EVENT_DISCONNECT_CLICKED:
                OnDisconnectClicked();
                break;

            case EVENT_SETTINGS_CLICKED:
                OnSettingsClicked();
                break;

            case EVENT_PROTOCOL_CHANGED:
                OnProtocolChanged();
                break;

            case EVENT_CHART_MODE_CHANGED:
                OnChartModeChanged();
                break;
        }
    }

    // Clear event queue
    ArrayResize(m_eventQueue, 0);
    m_eventCount = 0;
}

//+------------------------------------------------------------------+
//| Add event to queue                                               |
//+------------------------------------------------------------------+
bool CBasicDashboard::AddEvent(ENUM_DASHBOARD_EVENT type, string data)
{
    ArrayResize(m_eventQueue, m_eventCount + 1);
    m_eventQueue[m_eventCount].type = type;
    m_eventQueue[m_eventCount].data = data;
    m_eventQueue[m_eventCount].timestamp = TimeCurrent();
    m_eventCount++;

    return true;
}

//+------------------------------------------------------------------+
//| Event processors                                                 |
//+------------------------------------------------------------------+
void CBasicDashboard::OnConnectClicked(void)
{
    Print("[DASHBOARD] Connect button clicked");
    // Signal to main EA to connect
    GlobalVariableSet("SuhoAI_ConnectRequest", 1);
}

void CBasicDashboard::OnDisconnectClicked(void)
{
    Print("[DASHBOARD] Disconnect button clicked");
    // Signal to main EA to disconnect
    GlobalVariableSet("SuhoAI_DisconnectRequest", 1);
}

void CBasicDashboard::OnSettingsClicked(void)
{
    Print("[DASHBOARD] Settings button clicked");
    // Open settings panel
    GlobalVariableSet("SuhoAI_SettingsRequest", 1);
}

void CBasicDashboard::OnProtocolChanged(void)
{
    m_useBinaryProtocol = !m_useBinaryProtocol;
    GlobalVariableSet("SuhoAI_BinaryProtocol", m_useBinaryProtocol ? 1 : 0);
    Print("[DASHBOARD] Protocol changed to: ", m_useBinaryProtocol ? "Binary" : "JSON");
}

void CBasicDashboard::OnChartModeChanged(void)
{
    m_streamCurrentChartOnly = !m_streamCurrentChartOnly;
    GlobalVariableSet("SuhoAI_CurrentChartOnly", m_streamCurrentChartOnly ? 1 : 0);
    Print("[DASHBOARD] Chart mode changed to: ", m_streamCurrentChartOnly ? "Current Chart Only" : "All Pairs");
}

//+------------------------------------------------------------------+
//| Shutdown dashboard                                               |
//+------------------------------------------------------------------+
void CBasicDashboard::Shutdown(void)
{
    if(!m_isInitialized)
        return;

    Print("[DASHBOARD] Shutting down dashboard...");

    // Destroy components
    if(m_statusDisplay != NULL)
    {
        delete m_statusDisplay;
        m_statusDisplay = NULL;
    }

    if(m_accountInfo != NULL)
    {
        delete m_accountInfo;
        m_accountInfo = NULL;
    }

    if(m_tradingPairs != NULL)
    {
        delete m_tradingPairs;
        m_tradingPairs = NULL;
    }

    if(m_controlPanel != NULL)
    {
        delete m_controlPanel;
        m_controlPanel = NULL;
    }

    if(m_performanceMetrics != NULL)
    {
        delete m_performanceMetrics;
        m_performanceMetrics = NULL;
    }

    m_isInitialized = false;
    Print("[DASHBOARD] Dashboard shutdown complete");
}

#endif // BASICDASHBOARD_MQH