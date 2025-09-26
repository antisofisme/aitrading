//+------------------------------------------------------------------+
//|                                           SettingsPanel.mqh     |
//|                     Configuration interface for Suho AI Trading |
//+------------------------------------------------------------------+
#ifndef SETTINGSPANEL_MQH
#define SETTINGSPANEL_MQH

#include "UIComponents.mqh"
#include <Controls/Dialog.mqh>
#include <Controls/Button.mqh>
#include <Controls/CheckBox.mqh>
#include <Controls/Edit.mqh>
#include <Controls/ComboBox.mqh>
#include <Controls/SpinEdit.mqh>

//+------------------------------------------------------------------+
//| Settings Categories                                              |
//+------------------------------------------------------------------+
enum ENUM_SETTINGS_CATEGORY
{
    SETTINGS_CONNECTION,
    SETTINGS_PROTOCOL,
    SETTINGS_TRADING,
    SETTINGS_DISPLAY,
    SETTINGS_ADVANCED
};

//+------------------------------------------------------------------+
//| Settings Structure                                               |
//+------------------------------------------------------------------+
struct SSettingsData
{
    // Connection Settings
    string               serverUrl;
    int                  serverPort;
    int                  connectionTimeout;
    int                  reconnectInterval;
    bool                 autoReconnect;

    // Protocol Settings
    bool                 useBinaryProtocol;
    bool                 useCompression;
    int                  heartbeatInterval;
    bool                 enableEncryption;

    // Trading Settings
    bool                 streamCurrentChartOnly;
    double               maxRiskPerTrade;
    bool                 enableAutoTrading;
    int                  maxConcurrentTrades;
    bool                 enableStopLoss;
    bool                 enableTakeProfit;

    // Display Settings
    bool                 showAdvancedMetrics;
    bool                 showPerformanceGraph;
    int                  refreshInterval;
    bool                 enableSoundAlerts;
    bool                 enablePopupAlerts;

    // Advanced Settings
    int                  maxHistoryRecords;
    bool                 enableDebugLogging;
    string               logLevel;
    bool                 enableProfiler;
};

//+------------------------------------------------------------------+
//| Settings Panel Class                                             |
//+------------------------------------------------------------------+
class CSettingsPanel : public CAppDialog
{
private:
    // UI Components - Connection Tab
    CEdit*               m_editServerUrl;
    CSpinEdit*           m_spinServerPort;
    CSpinEdit*           m_spinConnectionTimeout;
    CSpinEdit*           m_spinReconnectInterval;
    CCheckBox*           m_chkAutoReconnect;

    // UI Components - Protocol Tab
    CCheckBox*           m_chkBinaryProtocol;
    CCheckBox*           m_chkCompression;
    CSpinEdit*           m_spinHeartbeatInterval;
    CCheckBox*           m_chkEncryption;

    // UI Components - Trading Tab
    CCheckBox*           m_chkCurrentChartOnly;
    CEdit*               m_editMaxRisk;
    CCheckBox*           m_chkAutoTrading;
    CSpinEdit*           m_spinMaxTrades;
    CCheckBox*           m_chkStopLoss;
    CCheckBox*           m_chkTakeProfit;

    // UI Components - Display Tab
    CCheckBox*           m_chkAdvancedMetrics;
    CCheckBox*           m_chkPerformanceGraph;
    CSpinEdit*           m_spinRefreshInterval;
    CCheckBox*           m_chkSoundAlerts;
    CCheckBox*           m_chkPopupAlerts;

    // UI Components - Advanced Tab
    CSpinEdit*           m_spinMaxHistory;
    CCheckBox*           m_chkDebugLogging;
    CComboBox*           m_comboLogLevel;
    CCheckBox*           m_chkProfiler;

    // Control buttons
    CButton*             m_btnOK;
    CButton*             m_btnCancel;
    CButton*             m_btnApply;
    CButton*             m_btnReset;

    // Tab buttons
    CButton*             m_btnTabConnection;
    CButton*             m_btnTabProtocol;
    CButton*             m_btnTabTrading;
    CButton*             m_btnTabDisplay;
    CButton*             m_btnTabAdvanced;

    // Settings data
    SSettingsData        m_settings;
    SSettingsData        m_originalSettings;
    ENUM_SETTINGS_CATEGORY m_activeTab;
    bool                 m_settingsChanged;

    // Layout constants
    enum ENUM_PANEL_CONSTANTS {
        PANEL_WIDTH = 500,
        PANEL_HEIGHT = 400,
        TAB_HEIGHT = 30,
        BUTTON_HEIGHT = 25,
        EDIT_HEIGHT = 23,
        LABEL_WIDTH = 150,
        CONTROL_WIDTH = 200
    };

public:
                        CSettingsPanel(void);
                       ~CSettingsPanel(void);

    // Main interface
    bool                Initialize(void);
    void                ShowSettings(void);
    void                HideSettings(void);
    bool                Create(const long chart, const string name, const int subwin, const int x1, const int y1, const int x2, const int y2);
    void                Destroy(int reason) override;

    // Settings management
    void                LoadSettings(void);
    void                SaveSettings(void);
    void                ResetToDefaults(void);
    bool                ValidateSettings(void);
    void                ApplySettings(void);

    // Event handling
    bool                OnEvent(const int id, const long &lparam, const double &dparam, const string &sparam) override;

    // Getters
    SSettingsData       GetSettings(void) { return m_settings; }
    bool                HasUnsavedChanges(void) { return m_settingsChanged; }

protected:
    // UI Creation
    void                CreateTabs(void);
    void                CreateConnectionTab(void);
    void                CreateProtocolTab(void);
    void                CreateTradingTab(void);
    void                CreateDisplayTab(void);
    void                CreateAdvancedTab(void);
    void                CreateButtons(void);

    // Tab management
    void                SwitchToTab(ENUM_SETTINGS_CATEGORY tab);
    void                HideAllTabs(void);
    void                ShowTab(ENUM_SETTINGS_CATEGORY tab);

    // Event handlers
    void                OnTabClicked(ENUM_SETTINGS_CATEGORY tab);
    void                OnOKClicked(void);
    void                OnCancelClicked(void);
    void                OnApplyClicked(void);
    void                OnResetClicked(void);
    void                OnSettingChanged(void);

    // Validation
    bool                ValidateConnectionSettings(void);
    bool                ValidateProtocolSettings(void);
    bool                ValidateTradingSettings(void);
    bool                ValidateDisplaySettings(void);
    bool                ValidateAdvancedSettings(void);

    // Utility
    void                UpdateControlStates(void);
    CLabel*             CreateLabel(string name, int x, int y, string text);
    void                MarkChanged(void);
};

//+------------------------------------------------------------------+
//| Constructor                                                      |
//+------------------------------------------------------------------+
CSettingsPanel::CSettingsPanel(void) : m_editServerUrl(NULL), m_spinServerPort(NULL), m_spinConnectionTimeout(NULL),
                                        m_spinReconnectInterval(NULL), m_chkAutoReconnect(NULL), m_chkBinaryProtocol(NULL),
                                        m_chkCompression(NULL), m_spinHeartbeatInterval(NULL), m_chkEncryption(NULL),
                                        m_chkCurrentChartOnly(NULL), m_editMaxRisk(NULL), m_chkAutoTrading(NULL),
                                        m_spinMaxTrades(NULL), m_chkStopLoss(NULL), m_chkTakeProfit(NULL),
                                        m_chkAdvancedMetrics(NULL), m_chkPerformanceGraph(NULL), m_spinRefreshInterval(NULL),
                                        m_chkSoundAlerts(NULL), m_chkPopupAlerts(NULL), m_spinMaxHistory(NULL),
                                        m_chkDebugLogging(NULL), m_comboLogLevel(NULL), m_chkProfiler(NULL),
                                        m_btnOK(NULL), m_btnCancel(NULL), m_btnApply(NULL), m_btnReset(NULL),
                                        m_btnTabConnection(NULL), m_btnTabProtocol(NULL), m_btnTabTrading(NULL),
                                        m_btnTabDisplay(NULL), m_btnTabAdvanced(NULL), m_activeTab(SETTINGS_CONNECTION),
                                        m_settingsChanged(false)
{
    // Initialize settings with defaults
    m_settings.serverUrl = "wss://api.suho.trading";
    m_settings.serverPort = 443;
    m_settings.connectionTimeout = 30;
    m_settings.reconnectInterval = 5;
    m_settings.autoReconnect = true;
    m_settings.useBinaryProtocol = true;
    m_settings.useCompression = false;
    m_settings.heartbeatInterval = 30;
    m_settings.enableEncryption = true;
    m_settings.streamCurrentChartOnly = false;
    m_settings.maxRiskPerTrade = 2.0;
    m_settings.enableAutoTrading = true;
    m_settings.maxConcurrentTrades = 5;
    m_settings.enableStopLoss = true;
    m_settings.enableTakeProfit = true;
    m_settings.showAdvancedMetrics = true;
    m_settings.showPerformanceGraph = false;
    m_settings.refreshInterval = 1000;
    m_settings.enableSoundAlerts = true;
    m_settings.enablePopupAlerts = false;
    m_settings.maxHistoryRecords = 3600;
    m_settings.enableDebugLogging = false;
    m_settings.logLevel = "INFO";
    m_settings.enableProfiler = false;

    m_originalSettings = m_settings;
}

//+------------------------------------------------------------------+
//| Destructor                                                       |
//+------------------------------------------------------------------+
CSettingsPanel::~CSettingsPanel(void)
{
    // Cleanup will be handled by Destroy()
}

//+------------------------------------------------------------------+
//| Initialize settings panel                                        |
//+------------------------------------------------------------------+
bool CSettingsPanel::Initialize(void)
{
    Print("[SETTINGS] Initializing Settings Panel...");

    if(!Create(0, "SuhoAI_Settings", 0, 100, 100, 100 + PANEL_WIDTH, 100 + PANEL_HEIGHT))
    {
        Print("[SETTINGS] Failed to create settings dialog");
        return false;
    }

    Caption("Suho AI Trading - Settings");
    // ColorBackground(UI_COLOR_BACKGROUND);
    // ColorBorder(UI_COLOR_BORDER);

    // Load current settings
    LoadSettings();

    // Create UI components
    CreateTabs();
    CreateButtons();

    // Show connection tab by default
    SwitchToTab(SETTINGS_CONNECTION);

    Print("[SETTINGS] Settings Panel initialized successfully");
    return true;
}

//+------------------------------------------------------------------+
//| Create tab buttons                                               |
//+------------------------------------------------------------------+
void CSettingsPanel::CreateTabs(void)
{
    int tabWidth = PANEL_WIDTH / 5;
    int y = 10;

    // Connection Tab
    m_btnTabConnection = new CButton();
    if(m_btnTabConnection != NULL)
    {
        m_btnTabConnection.Create(0, "TabConnection", 0, 0, y, tabWidth, y + TAB_HEIGHT);
        m_btnTabConnection.Text("Connection");
        Add(m_btnTabConnection);
    }

    // Protocol Tab
    m_btnTabProtocol = new CButton();
    if(m_btnTabProtocol != NULL)
    {
        m_btnTabProtocol.Create(0, "TabProtocol", 0, tabWidth, y, tabWidth * 2, y + TAB_HEIGHT);
        m_btnTabProtocol.Text("Protocol");
        Add(m_btnTabProtocol);
    }

    // Trading Tab
    m_btnTabTrading = new CButton();
    if(m_btnTabTrading != NULL)
    {
        m_btnTabTrading.Create(0, "TabTrading", 0, tabWidth * 2, y, tabWidth * 3, y + TAB_HEIGHT);
        m_btnTabTrading.Text("Trading");
        Add(m_btnTabTrading);
    }

    // Display Tab
    m_btnTabDisplay = new CButton();
    if(m_btnTabDisplay != NULL)
    {
        m_btnTabDisplay.Create(0, "TabDisplay", 0, tabWidth * 3, y, tabWidth * 4, y + TAB_HEIGHT);
        m_btnTabDisplay.Text("Display");
        Add(m_btnTabDisplay);
    }

    // Advanced Tab
    m_btnTabAdvanced = new CButton();
    if(m_btnTabAdvanced != NULL)
    {
        m_btnTabAdvanced.Create(0, "TabAdvanced", 0, tabWidth * 4, y, PANEL_WIDTH, y + TAB_HEIGHT);
        m_btnTabAdvanced.Text("Advanced");
        Add(m_btnTabAdvanced);
    }

    // Create tab content
    CreateConnectionTab();
    CreateProtocolTab();
    CreateTradingTab();
    CreateDisplayTab();
    CreateAdvancedTab();
}

//+------------------------------------------------------------------+
//| Create connection tab                                            |
//+------------------------------------------------------------------+
void CSettingsPanel::CreateConnectionTab(void)
{
    int yPos = TAB_HEIGHT + 20;
    int rowHeight = 30;

    // Server URL
    CreateLabel("LabelServerUrl", 10, yPos, "Server URL:");
    m_editServerUrl = new CEdit();
    if(m_editServerUrl != NULL)
    {
        m_editServerUrl.Create(0, "EditServerUrl", 0, LABEL_WIDTH, yPos, LABEL_WIDTH + CONTROL_WIDTH, yPos + EDIT_HEIGHT);
        m_editServerUrl.Text(m_settings.serverUrl);
        Add(m_editServerUrl);
    }
    yPos += rowHeight;

    // Server Port
    CreateLabel("LabelServerPort", 10, yPos, "Server Port:");
    m_spinServerPort = new CSpinEdit();
    if(m_spinServerPort != NULL)
    {
        m_spinServerPort.Create(0, "SpinServerPort", 0, LABEL_WIDTH, yPos, LABEL_WIDTH + 100, yPos + EDIT_HEIGHT);
        m_spinServerPort.MinValue(1);
        m_spinServerPort.MaxValue(65535);
        m_spinServerPort.Value(m_settings.serverPort);
        Add(m_spinServerPort);
    }
    yPos += rowHeight;

    // Connection Timeout
    CreateLabel("LabelConnectionTimeout", 10, yPos, "Connection Timeout (s):");
    m_spinConnectionTimeout = new CSpinEdit();
    if(m_spinConnectionTimeout != NULL)
    {
        m_spinConnectionTimeout.Create(0, "SpinConnectionTimeout", 0, LABEL_WIDTH, yPos, LABEL_WIDTH + 100, yPos + EDIT_HEIGHT);
        m_spinConnectionTimeout.MinValue(5);
        m_spinConnectionTimeout.MaxValue(300);
        m_spinConnectionTimeout.Value(m_settings.connectionTimeout);
        Add(m_spinConnectionTimeout);
    }
    yPos += rowHeight;

    // Auto Reconnect
    m_chkAutoReconnect = new CCheckBox();
    if(m_chkAutoReconnect != NULL)
    {
        m_chkAutoReconnect.Create(0, "ChkAutoReconnect", 0, 10, yPos, 300, yPos + BUTTON_HEIGHT);
        m_chkAutoReconnect.Text("Enable Auto Reconnect");
        m_chkAutoReconnect.Checked(m_settings.autoReconnect);
        Add(m_chkAutoReconnect);
    }
}

//+------------------------------------------------------------------+
//| Load settings                                                    |
//+------------------------------------------------------------------+
void CSettingsPanel::LoadSettings(void)
{
    // In a real implementation, this would load from a file or registry
    // For now, we'll use global variables as a simple persistence method

    // Load connection settings
    if(GlobalVariableCheck("SuhoAI_Settings_ServerUrl"))
        m_settings.serverUrl = ""; // GlobalVariables don't support strings directly

    if(GlobalVariableCheck("SuhoAI_Settings_ServerPort"))
        m_settings.serverPort = (int)GlobalVariableGet("SuhoAI_Settings_ServerPort");

    if(GlobalVariableCheck("SuhoAI_Settings_BinaryProtocol"))
        m_settings.useBinaryProtocol = GlobalVariableGet("SuhoAI_Settings_BinaryProtocol") > 0;

    if(GlobalVariableCheck("SuhoAI_Settings_CurrentChartOnly"))
        m_settings.streamCurrentChartOnly = GlobalVariableGet("SuhoAI_Settings_CurrentChartOnly") > 0;

    // Copy to original for comparison
    m_originalSettings = m_settings;
    m_settingsChanged = false;

    Print("[SETTINGS] Settings loaded from global variables");
}

//+------------------------------------------------------------------+
//| Save settings                                                    |
//+------------------------------------------------------------------+
void CSettingsPanel::SaveSettings(void)
{
    // Save to global variables (in a real implementation, this would save to a file)
    GlobalVariableSet("SuhoAI_Settings_ServerPort", m_settings.serverPort);
    GlobalVariableSet("SuhoAI_Settings_BinaryProtocol", m_settings.useBinaryProtocol ? 1 : 0);
    GlobalVariableSet("SuhoAI_Settings_CurrentChartOnly", m_settings.streamCurrentChartOnly ? 1 : 0);
    GlobalVariableSet("SuhoAI_Settings_ConnectionTimeout", m_settings.connectionTimeout);
    GlobalVariableSet("SuhoAI_Settings_AutoReconnect", m_settings.autoReconnect ? 1 : 0);
    GlobalVariableSet("SuhoAI_Settings_MaxRisk", m_settings.maxRiskPerTrade);
    GlobalVariableSet("SuhoAI_Settings_MaxTrades", m_settings.maxConcurrentTrades);
    GlobalVariableSet("SuhoAI_Settings_RefreshInterval", m_settings.refreshInterval);

    m_originalSettings = m_settings;
    m_settingsChanged = false;

    Print("[SETTINGS] Settings saved to global variables");
}

//+------------------------------------------------------------------+
//| Event handling                                                   |
//+------------------------------------------------------------------+
bool CSettingsPanel::OnEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
{
    if(id == CHARTEVENT_OBJECT_CLICK)
    {
        if(StringFind(sparam, "TabConnection") >= 0)
        {
            OnTabClicked(SETTINGS_CONNECTION);
            return true;
        }
        else if(StringFind(sparam, "TabProtocol") >= 0)
        {
            OnTabClicked(SETTINGS_PROTOCOL);
            return true;
        }
        else if(StringFind(sparam, "TabTrading") >= 0)
        {
            OnTabClicked(SETTINGS_TRADING);
            return true;
        }
        else if(StringFind(sparam, "TabDisplay") >= 0)
        {
            OnTabClicked(SETTINGS_DISPLAY);
            return true;
        }
        else if(StringFind(sparam, "TabAdvanced") >= 0)
        {
            OnTabClicked(SETTINGS_ADVANCED);
            return true;
        }
        else if(StringFind(sparam, "BtnOK") >= 0)
        {
            OnOKClicked();
            return true;
        }
        else if(StringFind(sparam, "BtnCancel") >= 0)
        {
            OnCancelClicked();
            return true;
        }
        else if(StringFind(sparam, "BtnApply") >= 0)
        {
            OnApplyClicked();
            return true;
        }
        else if(StringFind(sparam, "BtnReset") >= 0)
        {
            OnResetClicked();
            return true;
        }
    }
    else if(id == CHARTEVENT_OBJECT_CHANGE)
    {
        OnSettingChanged();
        return true;
    }

    return CAppDialog::OnEvent(id, lparam, dparam, sparam);
}

//+------------------------------------------------------------------+
//| Switch to tab                                                    |
//+------------------------------------------------------------------+
void CSettingsPanel::SwitchToTab(ENUM_SETTINGS_CATEGORY tab)
{
    HideAllTabs();
    ShowTab(tab);
    m_activeTab = tab;

    // Update tab button states (visual feedback)
    if(m_btnTabConnection != NULL) m_btnTabConnection.Pressed(tab == SETTINGS_CONNECTION);
    if(m_btnTabProtocol != NULL) m_btnTabProtocol.Pressed(tab == SETTINGS_PROTOCOL);
    if(m_btnTabTrading != NULL) m_btnTabTrading.Pressed(tab == SETTINGS_TRADING);
    if(m_btnTabDisplay != NULL) m_btnTabDisplay.Pressed(tab == SETTINGS_DISPLAY);
    if(m_btnTabAdvanced != NULL) m_btnTabAdvanced.Pressed(tab == SETTINGS_ADVANCED);
}

//+------------------------------------------------------------------+
//| Create control buttons                                           |
//+------------------------------------------------------------------+
void CSettingsPanel::CreateButtons(void)
{
    int buttonWidth = 80;
    int buttonSpacing = 10;
    int yPos = PANEL_HEIGHT - 40;
    int xPos = PANEL_WIDTH - (4 * buttonWidth + 3 * buttonSpacing);

    // OK Button
    m_btnOK = new CButton();
    if(m_btnOK != NULL)
    {
        m_btnOK.Create(0, "BtnOK", 0, xPos, yPos, xPos + buttonWidth, yPos + BUTTON_HEIGHT);
        m_btnOK.Text("OK");
        Add(m_btnOK);
        xPos += buttonWidth + buttonSpacing;
    }

    // Cancel Button
    m_btnCancel = new CButton();
    if(m_btnCancel != NULL)
    {
        m_btnCancel.Create(0, "BtnCancel", 0, xPos, yPos, xPos + buttonWidth, yPos + BUTTON_HEIGHT);
        m_btnCancel.Text("Cancel");
        Add(m_btnCancel);
        xPos += buttonWidth + buttonSpacing;
    }

    // Apply Button
    m_btnApply = new CButton();
    if(m_btnApply != NULL)
    {
        m_btnApply.Create(0, "BtnApply", 0, xPos, yPos, xPos + buttonWidth, yPos + BUTTON_HEIGHT);
        m_btnApply.Text("Apply");
        Add(m_btnApply);
        xPos += buttonWidth + buttonSpacing;
    }

    // Reset Button
    m_btnReset = new CButton();
    if(m_btnReset != NULL)
    {
        m_btnReset.Create(0, "BtnReset", 0, xPos, yPos, xPos + buttonWidth, yPos + BUTTON_HEIGHT);
        m_btnReset.Text("Reset");
        Add(m_btnReset);
    }
}

//+------------------------------------------------------------------+
//| Create label helper                                              |
//+------------------------------------------------------------------+
CLabel* CSettingsPanel::CreateLabel(string name, int x, int y, string text)
{
    CLabel* label = new CLabel();
    if(label != NULL)
    {
        if(label.Create(0, name, 0, x, y, x + LABEL_WIDTH, y + 20))
        {
            label.Text(text);
            label.Color(UI_COLOR_TEXT);
            Add(label);
        }
        else
        {
            delete label;
            label = NULL;
        }
    }
    return label;
}

//+------------------------------------------------------------------+
//| Event handlers                                                   |
//+------------------------------------------------------------------+
void CSettingsPanel::OnOKClicked(void)
{
    if(ValidateSettings())
    {
        ApplySettings();
        SaveSettings();
        Hide();
    }
}

void CSettingsPanel::OnCancelClicked(void)
{
    if(m_settingsChanged)
    {
        // Restore original settings
        m_settings = m_originalSettings;
        m_settingsChanged = false;
    }
    Hide();
}

void CSettingsPanel::OnApplyClicked(void)
{
    if(ValidateSettings())
    {
        ApplySettings();
        SaveSettings();
    }
}

void CSettingsPanel::OnResetClicked(void)
{
    ResetToDefaults();
    MarkChanged();
}

void CSettingsPanel::MarkChanged(void)
{
    m_settingsChanged = true;
    if(m_btnApply != NULL)
        m_btnApply.ColorBackground(UI_COLOR_WARNING);
}

bool CSettingsPanel::ValidateSettings(void)
{
    // Basic validation - in a real implementation, this would be more comprehensive
    if(m_settings.serverPort < 1 || m_settings.serverPort > 65535)
    {
        MessageBox("Invalid server port. Must be between 1 and 65535.", "Settings Validation", MB_OK | MB_ICONERROR);
        return false;
    }

    if(m_settings.maxRiskPerTrade < 0.1 || m_settings.maxRiskPerTrade > 100.0)
    {
        MessageBox("Invalid max risk per trade. Must be between 0.1% and 100%.", "Settings Validation", MB_OK | MB_ICONERROR);
        return false;
    }

    return true;
}

void CSettingsPanel::ApplySettings(void)
{
    // Signal to main EA that settings have changed
    GlobalVariableSet("SuhoAI_SettingsChanged", GetTickCount());
    Print("[SETTINGS] Settings applied and signaled to main EA");
}

void CSettingsPanel::ShowSettings(void)
{
    Show();
}

void CSettingsPanel::HideSettings(void)
{
    Hide();
}

#endif // SETTINGSPANEL_MQH