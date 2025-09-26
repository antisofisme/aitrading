//+------------------------------------------------------------------+
//|                                        SimpleDashboard.mqh     |
//|                     Simple dashboard using Comment display      |
//+------------------------------------------------------------------+
#ifndef SIMPLEDASHBOARD_MQH
#define SIMPLEDASHBOARD_MQH

#include "UIComponents_Simple.mqh"
#include "UIEventSystem.mqh"

//+------------------------------------------------------------------+
//| Simple Dashboard Class                                           |
//+------------------------------------------------------------------+
class CSimpleDashboard
{
private:
    // UI Components
    CSimpleStatusDisplay*      m_statusDisplay;
    CSimpleAccountInfo*        m_accountInfo;
    CSimplePerformanceMetrics* m_performanceMetrics;

    // Dashboard state
    bool                 m_isInitialized;
    bool                 m_isVisible;
    datetime             m_lastUpdate;

public:
                        CSimpleDashboard(void);
                       ~CSimpleDashboard(void);

    // Main interface
    bool                Initialize(void);
    void                Shutdown(void);

    // Update methods
    void                UpdateAll(void);
    void                UpdateConnectionStatus(bool connected, string serverInfo = "");
    void                UpdateAccountData(void);
    void                UpdatePerformanceMetrics(double latency, int dataSize, string protocol);

    // Display control
    void                Show(bool visible = true);
    void                Hide(void) { Show(false); }
    void                DisplayComplete(void);

    // State getters
    bool                IsInitialized(void) { return m_isInitialized; }
    bool                IsVisible(void) { return m_isVisible; }
    datetime            GetLastUpdate(void) { return m_lastUpdate; }
};

//+------------------------------------------------------------------+
//| Constructor                                                      |
//+------------------------------------------------------------------+
CSimpleDashboard::CSimpleDashboard(void) : m_statusDisplay(NULL), m_accountInfo(NULL),
                                          m_performanceMetrics(NULL), m_isInitialized(false),
                                          m_isVisible(true), m_lastUpdate(0)
{
}

//+------------------------------------------------------------------+
//| Destructor                                                       |
//+------------------------------------------------------------------+
CSimpleDashboard::~CSimpleDashboard(void)
{
    Shutdown();
}

//+------------------------------------------------------------------+
//| Initialize dashboard                                             |
//+------------------------------------------------------------------+
bool CSimpleDashboard::Initialize(void)
{
    if(m_isInitialized)
        return true;

    Print("[DASHBOARD] Initializing Simple Dashboard...");

    // Create status display
    m_statusDisplay = new CSimpleStatusDisplay();
    if(m_statusDisplay == NULL)
    {
        Print("[DASHBOARD] Failed to create status display");
        return false;
    }

    // Create account info
    m_accountInfo = new CSimpleAccountInfo();
    if(m_accountInfo == NULL)
    {
        Print("[DASHBOARD] Failed to create account info");
        delete m_statusDisplay;
        m_statusDisplay = NULL;
        return false;
    }

    // Create performance metrics
    m_performanceMetrics = new CSimplePerformanceMetrics();
    if(m_performanceMetrics == NULL)
    {
        Print("[DASHBOARD] Failed to create performance metrics");
        delete m_statusDisplay;
        delete m_accountInfo;
        m_statusDisplay = NULL;
        m_accountInfo = NULL;
        return false;
    }

    m_isInitialized = true;
    m_lastUpdate = TimeCurrent();

    Print("[DASHBOARD] Simple Dashboard initialized successfully");
    return true;
}

//+------------------------------------------------------------------+
//| Update all components                                            |
//+------------------------------------------------------------------+
void CSimpleDashboard::UpdateAll(void)
{
    if(!m_isInitialized || !m_isVisible)
        return;

    m_lastUpdate = TimeCurrent();

    // Update all components
    if(m_statusDisplay != NULL)
        m_statusDisplay.Update();

    if(m_accountInfo != NULL)
        m_accountInfo.Update();

    if(m_performanceMetrics != NULL)
        m_performanceMetrics.Update();

    // Display everything on chart
    DisplayComplete();
}

//+------------------------------------------------------------------+
//| Update connection status                                         |
//+------------------------------------------------------------------+
void CSimpleDashboard::UpdateConnectionStatus(bool connected, string serverInfo)
{
    if(m_statusDisplay != NULL)
    {
        string status = connected ? "Connected" : "Disconnected";
        if(connected && serverInfo != "")
            status += " (" + serverInfo + ")";

        m_statusDisplay.SetConnectionStatus(status);
        m_statusDisplay.SetLastUpdate(TimeCurrent());
    }

    Print("[DASHBOARD] Connection status updated: ", connected ? "CONNECTED" : "DISCONNECTED");
}

//+------------------------------------------------------------------+
//| Update account data                                              |
//+------------------------------------------------------------------+
void CSimpleDashboard::UpdateAccountData(void)
{
    if(m_accountInfo != NULL)
    {
        m_accountInfo.Update();
    }
}

//+------------------------------------------------------------------+
//| Update performance metrics                                       |
//+------------------------------------------------------------------+
void CSimpleDashboard::UpdatePerformanceMetrics(double latency, int dataSize, string protocol)
{
    if(m_performanceMetrics != NULL)
    {
        m_performanceMetrics.SetLatency(latency);
        m_performanceMetrics.SetDataSize(dataSize);
        m_performanceMetrics.SetProtocol(protocol);
    }
}

//+------------------------------------------------------------------+
//| Show/hide dashboard                                              |
//+------------------------------------------------------------------+
void CSimpleDashboard::Show(bool visible)
{
    m_isVisible = visible;

    if(m_statusDisplay != NULL)
        m_statusDisplay.Show(visible);

    if(m_accountInfo != NULL)
        m_accountInfo.Show(visible);

    if(m_performanceMetrics != NULL)
        m_performanceMetrics.Show(visible);

    if(!visible)
    {
        Comment(""); // Clear comment when hiding
    }
}

//+------------------------------------------------------------------+
//| Display complete dashboard                                       |
//+------------------------------------------------------------------+
void CSimpleDashboard::DisplayComplete(void)
{
    if(!m_isVisible)
        return;

    string fullDisplay = "";

    // Status section
    if(m_statusDisplay != NULL)
    {
        fullDisplay += "=== SUHO AI TRADING STATUS ===\n";
        fullDisplay += "Connection: " + m_statusDisplay.GetConnectionStatus() + "\n";
        fullDisplay += "Trading: " + m_statusDisplay.GetTradingStatus() + "\n";

        if(m_statusDisplay.GetLastUpdate() > 0)
        {
            fullDisplay += "Last Update: " + TimeToString(m_statusDisplay.GetLastUpdate(), TIME_DATE|TIME_MINUTES|TIME_SECONDS) + "\n";
        }
        else
        {
            fullDisplay += "Last Update: Never\n";
        }
    }

    // Account section
    if(m_accountInfo != NULL)
    {
        fullDisplay += "\n=== ACCOUNT INFORMATION ===\n";
        fullDisplay += "Balance: " + DoubleToString(m_accountInfo.GetBalance(), 2) + " " + AccountInfoString(ACCOUNT_CURRENCY) + "\n";
        fullDisplay += "Equity: " + DoubleToString(m_accountInfo.GetEquity(), 2) + " " + AccountInfoString(ACCOUNT_CURRENCY) + "\n";

        color profitColor = (m_accountInfo.GetProfit() >= 0) ? UI_COLOR_PROFIT : UI_COLOR_LOSS;
        string profitText = (m_accountInfo.GetProfit() >= 0) ? "(Profit)" : "(Loss)";
        fullDisplay += "P&L: " + DoubleToString(m_accountInfo.GetProfit(), 2) + " " + AccountInfoString(ACCOUNT_CURRENCY) + " " + profitText + "\n";
    }

    // Performance section
    if(m_performanceMetrics != NULL)
    {
        fullDisplay += "\n=== PERFORMANCE METRICS ===\n";

        double latency = m_performanceMetrics.GetLatency();
        if(latency < 1.0)
        {
            fullDisplay += "Latency: " + DoubleToString(latency * 1000, 0) + " μs";
        }
        else
        {
            fullDisplay += "Latency: " + DoubleToString(latency, 1) + " ms";
        }

        if(latency <= 50.0)
            fullDisplay += " (Excellent)\n";
        else if(latency <= 100.0)
            fullDisplay += " (Good)\n";
        else
            fullDisplay += " (Poor)\n";

        int dataSize = m_performanceMetrics.GetDataSize();
        fullDisplay += "Data Size: " + FormatBytes(dataSize) + "\n";

        string protocol = m_performanceMetrics.GetProtocol();
        fullDisplay += "Protocol: " + protocol;
        if(protocol == "Binary")
            fullDisplay += " (Optimized)\n";
        else
            fullDisplay += "\n";

        if(protocol == "Binary" && dataSize > 0)
        {
            int jsonSize = dataSize * 13; // Estimated JSON overhead
            double efficiency = ((double)(jsonSize - dataSize) / jsonSize) * 100.0;
            fullDisplay += "Efficiency: " + DoubleToString(efficiency, 1) + "%\n";
        }
    }

    // Instructions
    fullDisplay += "\n=== CONTROLS ===\n";
    fullDisplay += "Use EA inputs to modify settings\n";
    fullDisplay += "Check journal for detailed logs\n";

    // Display everything
    Comment(fullDisplay);
}

//+------------------------------------------------------------------+
//| Shutdown dashboard                                               |
//+------------------------------------------------------------------+
void CSimpleDashboard::Shutdown(void)
{
    if(!m_isInitialized)
        return;

    Print("[DASHBOARD] Shutting down Simple Dashboard...");

    // Clear display
    Comment("");

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

    if(m_performanceMetrics != NULL)
    {
        delete m_performanceMetrics;
        m_performanceMetrics = NULL;
    }

    m_isInitialized = false;
    Print("[DASHBOARD] Simple Dashboard shutdown complete");
}

#endif // SIMPLEDASHBOARD_MQH