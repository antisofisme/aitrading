//+------------------------------------------------------------------+
//|                                        PerformanceDisplay.mqh   |
//|                     Performance analytics visualization component |
//+------------------------------------------------------------------+
#ifndef PERFORMANCEDISPLAY_MQH
#define PERFORMANCEDISPLAY_MQH

#include "UIComponents.mqh"
#include <Controls/ListView.mqh>
#include <Controls/Chart.mqh>

//+------------------------------------------------------------------+
//| Performance Data Structure                                       |
//+------------------------------------------------------------------+
struct SPerformanceMetric
{
    datetime             timestamp;
    double               latency;
    int                  dataSize;
    int                  throughput;
    string               protocol;
    bool                 connectionStatus;
};

//+------------------------------------------------------------------+
//| Performance History Manager                                      |
//+------------------------------------------------------------------+
class CPerformanceHistory
{
private:
    SPerformanceMetric   m_history[];
    int                  m_maxHistory;
    int                  m_currentIndex;
    bool                 m_historyFull;

public:
                        CPerformanceHistory(int maxHistory = 1000);
                       ~CPerformanceHistory(void);

    void                AddMetric(datetime timestamp, double latency, int dataSize, string protocol, bool connected);
    SPerformanceMetric  GetLatestMetric(void);
    void                GetMetricsInRange(datetime fromTime, datetime toTime, SPerformanceMetric &metrics[]);
    double              GetAverageLatency(int periods = 60);
    int                 GetAverageDataSize(int periods = 60);
    double              GetConnectionUptime(int periods = 3600); // Last hour
    void                Clear(void);
    int                 GetHistoryCount(void);
};

//+------------------------------------------------------------------+
//| Performance Display Component                                    |
//+------------------------------------------------------------------+
class CPerformanceDisplay : public CUIComponent
{
private:
    // UI Components
    CLabel*             m_labelTitle;
    CLabel*             m_labelLatency;
    CLabel*             m_labelThroughput;
    CLabel*             m_labelProtocol;
    CLabel*             m_labelDataSize;
    CLabel*             m_labelUptime;
    CLabel*             m_labelAvgLatency;
    CLabel*             m_labelPacketLoss;
    CLabel*             m_labelEfficiency;

    // Performance tracking
    CPerformanceHistory* m_history;
    double               m_currentLatency;
    int                  m_currentDataSize;
    string               m_currentProtocol;
    bool                 m_isConnected;
    datetime             m_connectionStartTime;
    int                  m_totalPacketsSent;
    int                  m_totalPacketsLost;

    // Display settings
    bool                 m_showAdvancedMetrics;
    bool                 m_showRealTimeGraph;

public:
                        CPerformanceDisplay(void);
                       ~CPerformanceDisplay(void);

    bool                Create(int x, int y, int width, int height, string name) override;
    void                Update(void) override;
    void                Destroy(void) override;

    // Data update methods
    void                SetLatency(double ms);
    void                SetThroughput(double bytesPerSec);
    void                SetProtocolStats(string protocol, int dataSize);
    void                SetConnectionStatus(bool connected);
    void                RecordPacketSent(void);
    void                RecordPacketLoss(void);

    // Display control
    void                ShowAdvancedMetrics(bool show) { m_showAdvancedMetrics = show; }
    void                ShowRealTimeGraph(bool show) { m_showRealTimeGraph = show; }

    // Statistics
    double              GetAverageLatency(void);
    double              GetPacketLossRate(void);
    double              GetProtocolEfficiency(void);
    string              GetUptimeString(void);

private:
    void                UpdateLabels(void);
    void                CreateLabels(void);
    color               GetLatencyColor(double latency);
    string              FormatLatencyString(double latency);
    string              FormatThroughputString(double throughput);
    string              FormatEfficiencyString(double efficiency);
};

//+------------------------------------------------------------------+
//| Performance History Implementation                               |
//+------------------------------------------------------------------+
CPerformanceHistory::CPerformanceHistory(int maxHistory) : m_maxHistory(maxHistory), m_currentIndex(0), m_historyFull(false)
{
    ArrayResize(m_history, m_maxHistory);
    ArrayInitialize(m_history, {0});
}

CPerformanceHistory::~CPerformanceHistory(void)
{
    ArrayFree(m_history);
}

void CPerformanceHistory::AddMetric(datetime timestamp, double latency, int dataSize, string protocol, bool connected)
{
    m_history[m_currentIndex].timestamp = timestamp;
    m_history[m_currentIndex].latency = latency;
    m_history[m_currentIndex].dataSize = dataSize;
    m_history[m_currentIndex].protocol = protocol;
    m_history[m_currentIndex].connectionStatus = connected;

    m_currentIndex++;
    if(m_currentIndex >= m_maxHistory)
    {
        m_currentIndex = 0;
        m_historyFull = true;
    }
}

SPerformanceMetric CPerformanceHistory::GetLatestMetric(void)
{
    SPerformanceMetric empty = {0};
    if(m_currentIndex == 0 && !m_historyFull)
        return empty;

    int lastIndex = (m_currentIndex == 0) ? m_maxHistory - 1 : m_currentIndex - 1;
    return m_history[lastIndex];
}

double CPerformanceHistory::GetAverageLatency(int periods)
{
    int count = GetHistoryCount();
    if(count == 0) return 0.0;

    int samplesToCheck = MathMin(periods, count);
    double sum = 0.0;

    for(int i = 0; i < samplesToCheck; i++)
    {
        int index = (m_currentIndex - 1 - i + m_maxHistory) % m_maxHistory;
        sum += m_history[index].latency;
    }

    return sum / samplesToCheck;
}

int CPerformanceHistory::GetAverageDataSize(int periods)
{
    int count = GetHistoryCount();
    if(count == 0) return 0;

    int samplesToCheck = MathMin(periods, count);
    double sum = 0.0;

    for(int i = 0; i < samplesToCheck; i++)
    {
        int index = (m_currentIndex - 1 - i + m_maxHistory) % m_maxHistory;
        sum += m_history[index].dataSize;
    }

    return (int)(sum / samplesToCheck);
}

int CPerformanceHistory::GetHistoryCount(void)
{
    return m_historyFull ? m_maxHistory : m_currentIndex;
}

//+------------------------------------------------------------------+
//| Performance Display Implementation                               |
//+------------------------------------------------------------------+
CPerformanceDisplay::CPerformanceDisplay(void) : m_labelTitle(NULL), m_labelLatency(NULL), m_labelThroughput(NULL),
                                                  m_labelProtocol(NULL), m_labelDataSize(NULL), m_labelUptime(NULL),
                                                  m_labelAvgLatency(NULL), m_labelPacketLoss(NULL), m_labelEfficiency(NULL),
                                                  m_history(NULL), m_currentLatency(0), m_currentDataSize(0),
                                                  m_currentProtocol(""), m_isConnected(false), m_connectionStartTime(0),
                                                  m_totalPacketsSent(0), m_totalPacketsLost(0), m_showAdvancedMetrics(true),
                                                  m_showRealTimeGraph(false)
{
    m_history = new CPerformanceHistory(3600); // 1 hour of history at 1-second intervals
}

CPerformanceDisplay::~CPerformanceDisplay(void)
{
    Destroy();
}

bool CPerformanceDisplay::Create(int x, int y, int width, int height, string name)
{
    if(!CUIComponent::Create(x, y, width, height, name))
        return false;

    CreateLabels();
    return true;
}

void CPerformanceDisplay::CreateLabels(void)
{
    int yPos = UI_MARGIN;
    int labelHeight = 18;
    int labelSpacing = 20;

    // Title
    m_labelTitle = new CLabel();
    if(m_labelTitle != NULL)
    {
        m_labelTitle.Create(0, m_name + "_title", 0, UI_MARGIN, yPos, m_width - UI_MARGIN, yPos + labelHeight);
        m_labelTitle.Text("Performance Metrics");
        m_labelTitle.Color(UI_COLOR_INFO);
        m_labelTitle.FontSize(10);
        m_panel.Add(m_labelTitle);
        yPos += labelSpacing + 5;
    }

    // Current Latency
    m_labelLatency = new CLabel();
    if(m_labelLatency != NULL)
    {
        m_labelLatency.Create(0, m_name + "_latency", 0, UI_MARGIN, yPos, m_width - UI_MARGIN, yPos + labelHeight);
        m_labelLatency.Text("Latency: 0.0 ms");
        m_labelLatency.Color(UI_COLOR_TEXT);
        m_panel.Add(m_labelLatency);
        yPos += labelSpacing;
    }

    // Protocol & Data Size
    m_labelProtocol = new CLabel();
    if(m_labelProtocol != NULL)
    {
        m_labelProtocol.Create(0, m_name + "_protocol", 0, UI_MARGIN, yPos, m_width - UI_MARGIN, yPos + labelHeight);
        m_labelProtocol.Text("Protocol: None");
        m_labelProtocol.Color(UI_COLOR_TEXT);
        m_panel.Add(m_labelProtocol);
        yPos += labelSpacing;
    }

    // Data Size
    m_labelDataSize = new CLabel();
    if(m_labelDataSize != NULL)
    {
        m_labelDataSize.Create(0, m_name + "_datasize", 0, UI_MARGIN, yPos, m_width - UI_MARGIN, yPos + labelHeight);
        m_labelDataSize.Text("Data Size: 0 bytes");
        m_labelDataSize.Color(UI_COLOR_TEXT);
        m_panel.Add(m_labelDataSize);
        yPos += labelSpacing;
    }

    // Advanced metrics (if enabled)
    if(m_showAdvancedMetrics)
    {
        // Average Latency
        m_labelAvgLatency = new CLabel();
        if(m_labelAvgLatency != NULL)
        {
            m_labelAvgLatency.Create(0, m_name + "_avglatency", 0, UI_MARGIN, yPos, m_width - UI_MARGIN, yPos + labelHeight);
            m_labelAvgLatency.Text("Avg Latency (1m): 0.0 ms");
            m_labelAvgLatency.Color(UI_COLOR_TEXT);
            m_panel.Add(m_labelAvgLatency);
            yPos += labelSpacing;
        }

        // Connection Uptime
        m_labelUptime = new CLabel();
        if(m_labelUptime != NULL)
        {
            m_labelUptime.Create(0, m_name + "_uptime", 0, UI_MARGIN, yPos, m_width - UI_MARGIN, yPos + labelHeight);
            m_labelUptime.Text("Uptime: 00:00:00");
            m_labelUptime.Color(UI_COLOR_TEXT);
            m_panel.Add(m_labelUptime);
            yPos += labelSpacing;
        }

        // Packet Loss
        m_labelPacketLoss = new CLabel();
        if(m_labelPacketLoss != NULL)
        {
            m_labelPacketLoss.Create(0, m_name + "_packetloss", 0, UI_MARGIN, yPos, m_width - UI_MARGIN, yPos + labelHeight);
            m_labelPacketLoss.Text("Packet Loss: 0.0%");
            m_labelPacketLoss.Color(UI_COLOR_PROFIT);
            m_panel.Add(m_labelPacketLoss);
            yPos += labelSpacing;
        }

        // Protocol Efficiency
        m_labelEfficiency = new CLabel();
        if(m_labelEfficiency != NULL)
        {
            m_labelEfficiency.Create(0, m_name + "_efficiency", 0, UI_MARGIN, yPos, m_width - UI_MARGIN, yPos + labelHeight);
            m_labelEfficiency.Text("Efficiency: 0%");
            m_labelEfficiency.Color(UI_COLOR_TEXT);
            m_panel.Add(m_labelEfficiency);
        }
    }
}

void CPerformanceDisplay::Update(void)
{
    if(m_history != NULL)
    {
        m_history.AddMetric(TimeCurrent(), m_currentLatency, m_currentDataSize, m_currentProtocol, m_isConnected);
    }

    UpdateLabels();
}

void CPerformanceDisplay::UpdateLabels(void)
{
    // Update current latency
    if(m_labelLatency != NULL)
    {
        string latencyText = "Latency: " + FormatLatencyString(m_currentLatency);
        m_labelLatency.Text(latencyText);
        m_labelLatency.Color(GetLatencyColor(m_currentLatency));
    }

    // Update protocol and data size
    if(m_labelProtocol != NULL)
    {
        string protocolText = "Protocol: " + m_currentProtocol;
        if(m_currentProtocol == "Binary")
            protocolText += " (Optimized)";
        m_labelProtocol.Text(protocolText);
    }

    if(m_labelDataSize != NULL)
    {
        m_labelDataSize.Text("Data Size: " + FormatBytes(m_currentDataSize));
    }

    // Update advanced metrics
    if(m_showAdvancedMetrics && m_history != NULL)
    {
        if(m_labelAvgLatency != NULL)
        {
            double avgLatency = m_history.GetAverageLatency(60);
            m_labelAvgLatency.Text("Avg Latency (1m): " + FormatLatencyString(avgLatency));
        }

        if(m_labelUptime != NULL)
        {
            m_labelUptime.Text("Uptime: " + GetUptimeString());
        }

        if(m_labelPacketLoss != NULL)
        {
            double lossRate = GetPacketLossRate();
            string lossText = "Packet Loss: " + DoubleToString(lossRate, 2) + "%";
            m_labelPacketLoss.Text(lossText);
            m_labelPacketLoss.Color(lossRate < 1.0 ? UI_COLOR_PROFIT : (lossRate < 5.0 ? UI_COLOR_WARNING : UI_COLOR_LOSS));
        }

        if(m_labelEfficiency != NULL)
        {
            double efficiency = GetProtocolEfficiency();
            m_labelEfficiency.Text("Efficiency: " + FormatEfficiencyString(efficiency));
        }
    }
}

void CPerformanceDisplay::SetLatency(double ms)
{
    m_currentLatency = ms;
}

void CPerformanceDisplay::SetProtocolStats(string protocol, int dataSize)
{
    m_currentProtocol = protocol;
    m_currentDataSize = dataSize;
}

void CPerformanceDisplay::SetConnectionStatus(bool connected)
{
    if(connected && !m_isConnected)
    {
        m_connectionStartTime = TimeCurrent();
    }
    m_isConnected = connected;
}

void CPerformanceDisplay::RecordPacketSent(void)
{
    m_totalPacketsSent++;
}

void CPerformanceDisplay::RecordPacketLoss(void)
{
    m_totalPacketsLost++;
}

color CPerformanceDisplay::GetLatencyColor(double latency)
{
    if(latency <= 50.0) return UI_COLOR_PROFIT;      // Good: Green
    if(latency <= 100.0) return UI_COLOR_WARNING;    // Okay: Orange
    return UI_COLOR_LOSS;                            // Poor: Red
}

string CPerformanceDisplay::FormatLatencyString(double latency)
{
    if(latency < 1.0)
        return DoubleToString(latency * 1000, 0) + " μs";
    return DoubleToString(latency, 1) + " ms";
}

double CPerformanceDisplay::GetPacketLossRate(void)
{
    if(m_totalPacketsSent == 0)
        return 0.0;
    return ((double)m_totalPacketsLost / m_totalPacketsSent) * 100.0;
}

double CPerformanceDisplay::GetProtocolEfficiency(void)
{
    if(m_currentProtocol == "Binary")
    {
        // Calculate efficiency compared to JSON (typical reduction ~92%)
        int jsonSize = m_currentDataSize * 13; // Estimated JSON overhead
        return ((double)(jsonSize - m_currentDataSize) / jsonSize) * 100.0;
    }
    return 0.0; // JSON baseline
}

string CPerformanceDisplay::GetUptimeString(void)
{
    if(!m_isConnected || m_connectionStartTime == 0)
        return "00:00:00";

    int uptimeSeconds = (int)(TimeCurrent() - m_connectionStartTime);
    int hours = uptimeSeconds / 3600;
    int minutes = (uptimeSeconds % 3600) / 60;
    int seconds = uptimeSeconds % 60;

    return StringFormat("%02d:%02d:%02d", hours, minutes, seconds);
}

string CPerformanceDisplay::FormatEfficiencyString(double efficiency)
{
    return DoubleToString(efficiency, 1) + "%";
}

void CPerformanceDisplay::Destroy(void)
{
    if(m_history != NULL)
    {
        delete m_history;
        m_history = NULL;
    }

    // Clean up labels
    if(m_labelTitle != NULL) { delete m_labelTitle; m_labelTitle = NULL; }
    if(m_labelLatency != NULL) { delete m_labelLatency; m_labelLatency = NULL; }
    if(m_labelThroughput != NULL) { delete m_labelThroughput; m_labelThroughput = NULL; }
    if(m_labelProtocol != NULL) { delete m_labelProtocol; m_labelProtocol = NULL; }
    if(m_labelDataSize != NULL) { delete m_labelDataSize; m_labelDataSize = NULL; }
    if(m_labelUptime != NULL) { delete m_labelUptime; m_labelUptime = NULL; }
    if(m_labelAvgLatency != NULL) { delete m_labelAvgLatency; m_labelAvgLatency = NULL; }
    if(m_labelPacketLoss != NULL) { delete m_labelPacketLoss; m_labelPacketLoss = NULL; }
    if(m_labelEfficiency != NULL) { delete m_labelEfficiency; m_labelEfficiency = NULL; }

    CUIComponent::Destroy();
}

#endif // PERFORMANCEDISPLAY_MQH