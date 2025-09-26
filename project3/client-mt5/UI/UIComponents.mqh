//+------------------------------------------------------------------+
//|                                           UIComponents.mqh      |
//|                     Reusable UI elements for modular interface   |
//+------------------------------------------------------------------+
#ifndef UICOMPONENTS_MQH
#define UICOMPONENTS_MQH

#include <Controls/Dialog.mqh>
#include <Controls/Label.mqh>
#include <Controls/Edit.mqh>
#include <Controls/Button.mqh>
#include <Controls/CheckBox.mqh>
#include <Controls/ComboBox.mqh>
#include <Controls/Panel.mqh>

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
//| Base UI Component Class                                          |
//+------------------------------------------------------------------+
class CUIComponent
{
protected:
    CPanel*              m_panel;
    int                  m_x;
    int                  m_y;
    int                  m_width;
    int                  m_height;
    bool                 m_visible;
    string               m_name;

public:
                        CUIComponent(void);
                       ~CUIComponent(void);

    virtual bool        Create(int x, int y, int width, int height, string name);
    virtual void        Show(bool visible = true);
    virtual void        Hide(void) { Show(false); }
    virtual void        Update(void) {}
    virtual void        Destroy(void);

    // Getters
    int                 GetX(void) { return m_x; }
    int                 GetY(void) { return m_y; }
    int                 GetWidth(void) { return m_width; }
    int                 GetHeight(void) { return m_height; }
    bool                IsVisible(void) { return m_visible; }
    string              GetName(void) { return m_name; }
};

//+------------------------------------------------------------------+
//| Status Display Component                                         |
//+------------------------------------------------------------------+
class CStatusDisplay : public CUIComponent
{
private:
    CLabel*             m_labelConnection;
    CLabel*             m_labelStatus;
    CLabel*             m_labelLastUpdate;

public:
                        CStatusDisplay(void);
                       ~CStatusDisplay(void);

    bool                Create(int x, int y, int width, int height, string name) override;
    void                Update(void) override;
    void                SetConnectionStatus(string status, color clr = clrWhite);
    void                SetTradingStatus(string status, color clr = clrWhite);
    void                SetLastUpdate(datetime timestamp);
    void                Destroy(void) override;
};

//+------------------------------------------------------------------+
//| Account Info Component                                           |
//+------------------------------------------------------------------+
class CAccountInfoDisplay : public CUIComponent
{
private:
    CLabel*             m_labelBalance;
    CLabel*             m_labelEquity;
    CLabel*             m_labelMargin;
    CLabel*             m_labelFreeMargin;
    CLabel*             m_labelProfit;

public:
                        CAccountInfoDisplay(void);
                       ~CAccountInfoDisplay(void);

    bool                Create(int x, int y, int width, int height, string name) override;
    void                Update(void) override;
    void                Destroy(void) override;
};

//+------------------------------------------------------------------+
//| Trading Pairs Display Component                                  |
//+------------------------------------------------------------------+
class CTradingPairs : public CUIComponent
{
private:
    CLabel*             m_labels[];
    int                 m_pairCount;
    string              m_pairs[];

public:
                        CTradingPairs(void);
                       ~CTradingPairs(void);

    bool                Create(int x, int y, int width, int height, string name) override;
    void                Update(void) override;
    void                SetTradingPairs(string &pairs[]);
    void                UpdatePriceData(string symbol, double bid, double ask, double spread);
    void                Destroy(void) override;
};

//+------------------------------------------------------------------+
//| Control Panel Component                                          |
//+------------------------------------------------------------------+
class CControlPanel : public CUIComponent
{
private:
    CButton*            m_btnConnect;
    CButton*            m_btnDisconnect;
    CCheckBox*          m_chkBinaryProtocol;
    CCheckBox*          m_chkCurrentChart;
    CButton*            m_btnSettings;

public:
                        CControlPanel(void);
                       ~CControlPanel(void);

    bool                Create(int x, int y, int width, int height, string name) override;
    void                Update(void) override;

    // Event handlers
    bool                OnConnectClick(void);
    bool                OnDisconnectClick(void);
    bool                OnSettingsClick(void);
    bool                OnProtocolChange(void);
    bool                OnChartModeChange(void);

    void                Destroy(void) override;
};

//+------------------------------------------------------------------+
//| Performance Metrics Component                                    |
//+------------------------------------------------------------------+
class CPerformanceMetrics : public CUIComponent
{
private:
    CLabel*             m_labelLatency;
    CLabel*             m_labelThroughput;
    CLabel*             m_labelProtocol;
    CLabel*             m_labelDataSize;

public:
                        CPerformanceMetrics(void);
                       ~CPerformanceMetrics(void);

    bool                Create(int x, int y, int width, int height, string name) override;
    void                Update(void) override;
    void                SetLatency(double ms);
    void                SetThroughput(double bytesPerSec);
    void                SetProtocolStats(string protocol, int dataSize);
    void                Destroy(void) override;
};

//+------------------------------------------------------------------+
//| Implementation of CUIComponent                                   |
//+------------------------------------------------------------------+
CUIComponent::CUIComponent(void) : m_panel(NULL), m_x(0), m_y(0), m_width(0), m_height(0), m_visible(false)
{
}

CUIComponent::~CUIComponent(void)
{
    Destroy();
}

bool CUIComponent::Create(int x, int y, int width, int height, string name)
{
    m_x = x;
    m_y = y;
    m_width = width;
    m_height = height;
    m_name = name;
    m_visible = true;

    if(m_panel == NULL)
    {
        m_panel = new CPanel();
        if(m_panel != NULL)
        {
            if(!m_panel.Create(0, m_name + "_panel", 0, x, y, x + width, y + height))
            {
                delete m_panel;
                m_panel = NULL;
                return false;
            }
            m_panel.ColorBackground(UI_COLOR_PANEL);
            m_panel.ColorBorder(UI_COLOR_BORDER);
        }
    }

    return m_panel != NULL;
}

void CUIComponent::Show(bool visible)
{
    m_visible = visible;
    if(m_panel != NULL)
    {
        m_panel.Show();
    }
}

void CUIComponent::Destroy(void)
{
    if(m_panel != NULL)
    {
        delete m_panel;
        m_panel = NULL;
    }
}

//+------------------------------------------------------------------+
//| Implementation of CStatusDisplay                                 |
//+------------------------------------------------------------------+
CStatusDisplay::CStatusDisplay(void) : m_labelConnection(NULL), m_labelStatus(NULL), m_labelLastUpdate(NULL)
{
}

CStatusDisplay::~CStatusDisplay(void)
{
    Destroy();
}

bool CStatusDisplay::Create(int x, int y, int width, int height, string name)
{
    if(!CUIComponent::Create(x, y, width, height, name))
        return false;

    // Create connection status label
    m_labelConnection = new CLabel();
    if(m_labelConnection != NULL)
    {
        if(!m_labelConnection.Create(0, name + "_conn", 0, UI_MARGIN, UI_MARGIN, width - UI_MARGIN, UI_MARGIN + UI_LABEL_HEIGHT))
        {
            delete m_labelConnection;
            m_labelConnection = NULL;
            return false;
        }
        m_labelConnection.Text("Connection: Disconnected");
        m_labelConnection.Color(clrRed);
        if(m_panel != NULL) m_panel.Add(m_labelConnection);
    }

    // Create trading status label
    m_labelStatus = new CLabel();
    if(m_labelStatus != NULL)
    {
        if(!m_labelStatus.Create(0, name + "_status", 0, UI_MARGIN, UI_MARGIN + 25, width - UI_MARGIN, UI_MARGIN + 45))
        {
            delete m_labelStatus;
            m_labelStatus = NULL;
            return false;
        }
        m_labelStatus.Text("Trading: Inactive");
        m_labelStatus.Color(clrGray);
        if(m_panel != NULL) m_panel.Add(m_labelStatus);
    }

    // Create last update label
    m_labelLastUpdate = new CLabel();
    if(m_labelLastUpdate != NULL)
    {
        if(!m_labelLastUpdate.Create(0, name + "_update", 0, UI_MARGIN, UI_MARGIN + 50, width - UI_MARGIN, UI_MARGIN + 70))
        {
            delete m_labelLastUpdate;
            m_labelLastUpdate = NULL;
            return false;
        }
        m_labelLastUpdate.Text("Last Update: Never");
        m_labelLastUpdate.Color(clrGray);
        if(m_panel != NULL) m_panel.Add(m_labelLastUpdate);
    }

    return true;
}

void CStatusDisplay::Update(void)
{
    // Update will be called by parent dashboard
}

void CStatusDisplay::SetConnectionStatus(string status, color clr)
{
    if(m_labelConnection != NULL)
    {
        m_labelConnection.Text("Connection: " + status);
        m_labelConnection.Color(clr);
    }
}

void CStatusDisplay::SetTradingStatus(string status, color clr)
{
    if(m_labelStatus != NULL)
    {
        m_labelStatus.Text("Trading: " + status);
        m_labelStatus.Color(clr);
    }
}

void CStatusDisplay::SetLastUpdate(datetime timestamp)
{
    if(m_labelLastUpdate != NULL)
    {
        string timeStr = TimeToString(timestamp, TIME_DATE | TIME_MINUTES | TIME_SECONDS);
        m_labelLastUpdate.Text("Last Update: " + timeStr);
        m_labelLastUpdate.Color(clrWhite);
    }
}

void CStatusDisplay::Destroy(void)
{
    if(m_labelConnection != NULL)
    {
        delete m_labelConnection;
        m_labelConnection = NULL;
    }
    if(m_labelStatus != NULL)
    {
        delete m_labelStatus;
        m_labelStatus = NULL;
    }
    if(m_labelLastUpdate != NULL)
    {
        delete m_labelLastUpdate;
        m_labelLastUpdate = NULL;
    }
    CUIComponent::Destroy();
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

#endif // UICOMPONENTS_MQH