//+------------------------------------------------------------------+
//|                                    UIComponents_Simple.mqh     |
//|                     Simplified UI components for MQL5 compatibility |
//+------------------------------------------------------------------+
#ifndef UICOMPONENTS_SIMPLE_MQH
#define UICOMPONENTS_SIMPLE_MQH

//+------------------------------------------------------------------+
//| Color scheme constants                                           |
//+------------------------------------------------------------------+
#define UI_COLOR_BACKGROUND   C'45,45,48'
#define UI_COLOR_PANEL        C'60,63,65'
#define UI_COLOR_BORDER       C'85,85,85'
#define UI_COLOR_TEXT         clrWhite
#define UI_COLOR_PROFIT       clrLimeGreen
#define UI_COLOR_LOSS         clrRed
#define UI_COLOR_WARNING      clrOrange
#define UI_COLOR_INFO         clrDodgerBlue

//+------------------------------------------------------------------+
//| UI Layout constants                                              |
//+------------------------------------------------------------------+
#define UI_MARGIN            5
#define UI_BUTTON_HEIGHT     25
#define UI_LABEL_HEIGHT      20
#define UI_EDIT_HEIGHT       25
#define UI_PANEL_HEIGHT      150

//+------------------------------------------------------------------+
//| Simple Status Display Component                                  |
//+------------------------------------------------------------------+
class CSimpleStatusDisplay
{
private:
    string               m_connectionStatus;
    string               m_tradingStatus;
    datetime             m_lastUpdate;
    bool                 m_visible;

public:
                        CSimpleStatusDisplay(void);
                       ~CSimpleStatusDisplay(void);

    void                SetConnectionStatus(string status);
    void                SetTradingStatus(string status);
    void                SetLastUpdate(datetime timestamp);
    void                Show(bool visible = true);
    void                Hide(void) { Show(false); }
    void                Update(void);
    void                DisplayOnChart(void);

    string              GetConnectionStatus(void) { return m_connectionStatus; }
    string              GetTradingStatus(void) { return m_tradingStatus; }
    datetime            GetLastUpdate(void) { return m_lastUpdate; }
    bool                IsVisible(void) { return m_visible; }
};

//+------------------------------------------------------------------+
//| Simple Account Info Component                                    |
//+------------------------------------------------------------------+
class CSimpleAccountInfo
{
private:
    double               m_balance;
    double               m_equity;
    double               m_margin;
    double               m_freeMargin;
    double               m_profit;
    bool                 m_visible;

public:
                        CSimpleAccountInfo(void);
                       ~CSimpleAccountInfo(void);

    void                Update(void);
    void                Show(bool visible = true);
    void                Hide(void) { Show(false); }
    void                DisplayOnChart(void);

    double              GetBalance(void) { return m_balance; }
    double              GetEquity(void) { return m_equity; }
    double              GetProfit(void) { return m_profit; }
    bool                IsVisible(void) { return m_visible; }
};

//+------------------------------------------------------------------+
//| Simple Performance Metrics Component                            |
//+------------------------------------------------------------------+
class CSimplePerformanceMetrics
{
private:
    double               m_latency;
    int                  m_dataSize;
    string               m_protocol;
    bool                 m_visible;

public:
                        CSimplePerformanceMetrics(void);
                       ~CSimplePerformanceMetrics(void);

    void                SetLatency(double ms);
    void                SetDataSize(int bytes);
    void                SetProtocol(string protocol);
    void                Show(bool visible = true);
    void                Hide(void) { Show(false); }
    void                Update(void);
    void                DisplayOnChart(void);

    double              GetLatency(void) { return m_latency; }
    int                 GetDataSize(void) { return m_dataSize; }
    string              GetProtocol(void) { return m_protocol; }
    bool                IsVisible(void) { return m_visible; }
};

//+------------------------------------------------------------------+
//| Implementation of CSimpleStatusDisplay                          |
//+------------------------------------------------------------------+
CSimpleStatusDisplay::CSimpleStatusDisplay(void) : m_connectionStatus("Disconnected"),
                                                   m_tradingStatus("Inactive"),
                                                   m_lastUpdate(0),
                                                   m_visible(true)
{
}

CSimpleStatusDisplay::~CSimpleStatusDisplay(void)
{
}

void CSimpleStatusDisplay::SetConnectionStatus(string status)
{
    m_connectionStatus = status;
}

void CSimpleStatusDisplay::SetTradingStatus(string status)
{
    m_tradingStatus = status;
}

void CSimpleStatusDisplay::SetLastUpdate(datetime timestamp)
{
    m_lastUpdate = timestamp;
}

void CSimpleStatusDisplay::Show(bool visible)
{
    m_visible = visible;
}

void CSimpleStatusDisplay::Update(void)
{
    // Update internal data - display will be handled by DisplayOnChart
}

void CSimpleStatusDisplay::DisplayOnChart(void)
{
    if(!m_visible) return;

    // Use Comment for simple display
    string display = "=== SUHO AI TRADING STATUS ===\n";
    display += "Connection: " + m_connectionStatus + "\n";
    display += "Trading: " + m_tradingStatus + "\n";

    if(m_lastUpdate > 0)
    {
        display += "Last Update: " + TimeToString(m_lastUpdate, TIME_DATE|TIME_MINUTES|TIME_SECONDS) + "\n";
    }
    else
    {
        display += "Last Update: Never\n";
    }

    Comment(display);
}

//+------------------------------------------------------------------+
//| Implementation of CSimpleAccountInfo                            |
//+------------------------------------------------------------------+
CSimpleAccountInfo::CSimpleAccountInfo(void) : m_balance(0), m_equity(0), m_margin(0),
                                               m_freeMargin(0), m_profit(0), m_visible(true)
{
}

CSimpleAccountInfo::~CSimpleAccountInfo(void)
{
}

void CSimpleAccountInfo::Update(void)
{
    m_balance = AccountInfoDouble(ACCOUNT_BALANCE);
    m_equity = AccountInfoDouble(ACCOUNT_EQUITY);
    m_margin = AccountInfoDouble(ACCOUNT_MARGIN);
    m_freeMargin = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
    m_profit = AccountInfoDouble(ACCOUNT_PROFIT);
}

void CSimpleAccountInfo::Show(bool visible)
{
    m_visible = visible;
}

void CSimpleAccountInfo::DisplayOnChart(void)
{
    if(!m_visible) return;

    string display = "\n=== ACCOUNT INFORMATION ===\n";
    display += "Balance: " + DoubleToString(m_balance, 2) + " " + AccountInfoString(ACCOUNT_CURRENCY) + "\n";
    display += "Equity: " + DoubleToString(m_equity, 2) + " " + AccountInfoString(ACCOUNT_CURRENCY) + "\n";
    display += "Margin: " + DoubleToString(m_margin, 2) + " " + AccountInfoString(ACCOUNT_CURRENCY) + "\n";
    display += "Free Margin: " + DoubleToString(m_freeMargin, 2) + " " + AccountInfoString(ACCOUNT_CURRENCY) + "\n";

    color profitColor = (m_profit >= 0) ? UI_COLOR_PROFIT : UI_COLOR_LOSS;
    display += "Profit: " + DoubleToString(m_profit, 2) + " " + AccountInfoString(ACCOUNT_CURRENCY) + "\n";

    // Append to existing comment
    string currentComment = "";
    Comment(currentComment + display);
}

//+------------------------------------------------------------------+
//| Implementation of CSimplePerformanceMetrics                     |
//+------------------------------------------------------------------+
CSimplePerformanceMetrics::CSimplePerformanceMetrics(void) : m_latency(0), m_dataSize(0),
                                                            m_protocol(""), m_visible(true)
{
}

CSimplePerformanceMetrics::~CSimplePerformanceMetrics(void)
{
}

void CSimplePerformanceMetrics::SetLatency(double ms)
{
    m_latency = ms;
}

void CSimplePerformanceMetrics::SetDataSize(int bytes)
{
    m_dataSize = bytes;
}

void CSimplePerformanceMetrics::SetProtocol(string protocol)
{
    m_protocol = protocol;
}

void CSimplePerformanceMetrics::Show(bool visible)
{
    m_visible = visible;
}

void CSimplePerformanceMetrics::Update(void)
{
    // Update internal metrics
}

void CSimplePerformanceMetrics::DisplayOnChart(void)
{
    if(!m_visible) return;

    string display = "\n=== PERFORMANCE METRICS ===\n";

    if(m_latency < 1.0)
    {
        display += "Latency: " + DoubleToString(m_latency * 1000, 0) + " μs";
    }
    else
    {
        display += "Latency: " + DoubleToString(m_latency, 1) + " ms";
    }

    if(m_latency <= 50.0)
        display += " (Excellent)\n";
    else if(m_latency <= 100.0)
        display += " (Good)\n";
    else
        display += " (Poor)\n";

    display += "Data Size: ";
    if(m_dataSize < 1024)
        display += IntegerToString(m_dataSize) + " B\n";
    else
        display += DoubleToString(m_dataSize / 1024.0, 1) + " KB\n";

    display += "Protocol: " + m_protocol;
    if(m_protocol == "Binary")
        display += " (Optimized)\n";
    else
        display += "\n";

    if(m_protocol == "Binary" && m_dataSize > 0)
    {
        int jsonSize = m_dataSize * 13; // Estimated JSON overhead
        double efficiency = ((double)(jsonSize - m_dataSize) / jsonSize) * 100.0;
        display += "Efficiency: " + DoubleToString(efficiency, 1) + "%\n";
    }

    // Append to existing comment
    string currentComment = "";
    Comment(currentComment + display);
}

//+------------------------------------------------------------------+
//| Helper functions for UI formatting                              |
//+------------------------------------------------------------------+
string FormatPrice(double price, int digits = 5)
{
    return DoubleToString(price, digits);
}

string FormatCurrency(double amount, string currency = "USD")
{
    return currency + " " + DoubleToString(amount, 2);
}

color GetProfitColor(double value)
{
    if(value > 0) return UI_COLOR_PROFIT;
    if(value < 0) return UI_COLOR_LOSS;
    return clrGray;
}

string FormatBytes(int bytes)
{
    if(bytes < 1024) return IntegerToString(bytes) + " B";
    if(bytes < 1024 * 1024) return DoubleToString(bytes / 1024.0, 1) + " KB";
    return DoubleToString(bytes / (1024.0 * 1024.0), 1) + " MB";
}

string FormatLatency(double ms)
{
    if(ms < 1.0) return DoubleToString(ms * 1000, 0) + " μs";
    return DoubleToString(ms, 1) + " ms";
}

#endif // UICOMPONENTS_SIMPLE_MQH