const axios = require('axios');

class ErrorNotifier {
  constructor(config = {}) {
    this.config = {
      enabled: config.enabled !== false,
      channels: config.channels || {},
      ...config
    };

    this.notificationQueue = [];
    this.isProcessing = false;
  }

  /**
   * Send notification for an error
   * @param {Object} errorData - Error data with categorization
   * @param {Object} options - Notification options
   * @returns {Promise<Object>} - Notification result
   */
  async notify(errorData, options = {}) {
    if (!this.config.enabled) {
      return { success: false, reason: 'Notifications disabled' };
    }

    const notification = this._buildNotification(errorData, options);

    // Add to queue for batch processing
    this.notificationQueue.push(notification);

    // Process queue if not already processing
    if (!this.isProcessing) {
      this._processQueue();
    }

    return { success: true, queued: true, id: notification.id };
  }

  /**
   * Send immediate notification (bypass queue)
   * @param {Object} errorData - Error data
   * @param {Object} options - Notification options
   * @returns {Promise<Object>} - Notification result
   */
  async notifyImmediate(errorData, options = {}) {
    if (!this.config.enabled) {
      return { success: false, reason: 'Notifications disabled' };
    }

    const notification = this._buildNotification(errorData, options);
    return await this._sendNotification(notification);
  }

  /**
   * Send pattern alert
   * @param {Object} patternData - Pattern detection data
   * @returns {Promise<Object>} - Notification result
   */
  async notifyPattern(patternData) {
    if (!this.config.enabled) {
      return { success: false, reason: 'Notifications disabled' };
    }

    const notification = {
      id: this._generateId(),
      type: 'pattern_alert',
      priority: this._getPatternPriority(patternData),
      timestamp: new Date().toISOString(),
      title: 'Error Pattern Detected',
      message: this._buildPatternMessage(patternData),
      data: patternData,
      channels: this._selectChannels('pattern')
    };

    return await this._sendNotification(notification);
  }

  /**
   * Send system alert
   * @param {string} alertType - Type of alert
   * @param {Object} alertData - Alert data
   * @returns {Promise<Object>} - Notification result
   */
  async notifySystemAlert(alertType, alertData) {
    if (!this.config.enabled) {
      return { success: false, reason: 'Notifications disabled' };
    }

    const notification = {
      id: this._generateId(),
      type: 'system_alert',
      alertType,
      priority: alertData.priority || 'medium',
      timestamp: new Date().toISOString(),
      title: `System Alert: ${alertType}`,
      message: alertData.message,
      data: alertData,
      channels: this._selectChannels('system', alertData.priority)
    };

    return await this._sendNotification(notification);
  }

  /**
   * Build notification object from error data
   * @private
   */
  _buildNotification(errorData, options) {
    const severity = errorData.categorization?.severity || 'MEDIUM';
    const category = errorData.categorization?.category || 'UNKNOWN';

    return {
      id: this._generateId(),
      type: 'error',
      priority: this._mapSeverityToPriority(severity),
      timestamp: new Date().toISOString(),
      title: `${severity} ${category} Error`,
      message: this._buildErrorMessage(errorData),
      error: {
        id: errorData.id,
        category: errorData.categorization?.category,
        subcategory: errorData.categorization?.subcategory,
        severity: errorData.categorization?.severity,
        message: errorData.originalError?.message,
        patterns: errorData.patterns?.map(p => p.id) || []
      },
      channels: options.channels || this._selectChannels('error', severity),
      metadata: {
        source: 'ErrorDNA',
        version: '1.0',
        ...options.metadata
      }
    };
  }

  /**
   * Build error message for notification
   * @private
   */
  _buildErrorMessage(errorData) {
    const { categorization, originalError, patterns } = errorData;

    let message = `Error detected in ${categorization?.category || 'unknown'} system`;

    if (categorization?.subcategory) {
      message += ` (${categorization.subcategory})`;
    }

    if (originalError?.message) {
      message += `\n\nError: ${originalError.message}`;
    }

    if (patterns && patterns.length > 0) {
      message += `\n\nPattern detected: ${patterns[0].description}`;
    }

    if (categorization?.confidence) {
      message += `\n\nClassification confidence: ${Math.round(categorization.confidence * 100)}%`;
    }

    return message;
  }

  /**
   * Build pattern alert message
   * @private
   */
  _buildPatternMessage(patternData) {
    const { newPatterns, existingPatterns, anomalies } = patternData;

    let message = 'Error pattern analysis results:\n';

    if (newPatterns.length > 0) {
      message += `\n• New patterns detected: ${newPatterns.length}`;
      newPatterns.forEach(pattern => {
        message += `\n  - ${pattern.description} (${pattern.occurrences} occurrences)`;
      });
    }

    if (existingPatterns.length > 0) {
      message += `\n• Updated patterns: ${existingPatterns.length}`;
      existingPatterns.forEach(pattern => {
        message += `\n  - ${pattern.description} (${pattern.occurrences} total occurrences)`;
      });
    }

    if (anomalies.length > 0) {
      message += `\n• Anomalies detected: ${anomalies.length}`;
      anomalies.forEach(anomaly => {
        message += `\n  - ${anomaly.description}`;
      });
    }

    return message;
  }

  /**
   * Process notification queue
   * @private
   */
  async _processQueue() {
    if (this.isProcessing || this.notificationQueue.length === 0) {
      return;
    }

    this.isProcessing = true;

    try {
      while (this.notificationQueue.length > 0) {
        const notification = this.notificationQueue.shift();
        await this._sendNotification(notification);

        // Small delay to prevent flooding
        await this._delay(100);
      }
    } catch (error) {
      console.error('Error processing notification queue:', error);
    } finally {
      this.isProcessing = false;
    }
  }

  /**
   * Send notification through configured channels
   * @private
   */
  async _sendNotification(notification) {
    const results = [];

    for (const channel of notification.channels) {
      try {
        const result = await this._sendToChannel(channel, notification);
        results.push({ channel, success: true, result });
      } catch (error) {
        console.error(`Failed to send notification to ${channel}:`, error);
        results.push({ channel, success: false, error: error.message });
      }
    }

    return {
      id: notification.id,
      success: results.some(r => r.success),
      results,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Send notification to specific channel
   * @private
   */
  async _sendToChannel(channel, notification) {
    switch (channel) {
      case 'webhook':
        return await this._sendWebhook(notification);
      case 'email':
        return await this._sendEmail(notification);
      case 'slack':
        return await this._sendSlack(notification);
      default:
        throw new Error(`Unknown notification channel: ${channel}`);
    }
  }

  /**
   * Send webhook notification
   * @private
   */
  async _sendWebhook(notification) {
    const webhookConfig = this.config.channels.webhook;

    if (!webhookConfig?.enabled || !webhookConfig?.url) {
      throw new Error('Webhook not configured');
    }

    const payload = {
      timestamp: notification.timestamp,
      type: notification.type,
      priority: notification.priority,
      title: notification.title,
      message: notification.message,
      data: notification.error || notification.data,
      source: 'ErrorDNA'
    };

    const response = await axios.post(webhookConfig.url, payload, {
      timeout: webhookConfig.timeout || 5000,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'ErrorDNA/1.0'
      }
    });

    return {
      status: response.status,
      data: response.data
    };
  }

  /**
   * Send email notification
   * @private
   */
  async _sendEmail(notification) {
    const emailConfig = this.config.channels.email;

    if (!emailConfig?.enabled) {
      throw new Error('Email not configured or disabled');
    }

    // Email implementation would go here
    // For now, just log the notification
    console.log('Email notification:', {
      to: emailConfig.recipients,
      subject: notification.title,
      body: notification.message
    });

    return { sent: true, method: 'email' };
  }

  /**
   * Send Slack notification
   * @private
   */
  async _sendSlack(notification) {
    const slackConfig = this.config.channels.slack;

    if (!slackConfig?.enabled || !slackConfig?.webhookUrl) {
      throw new Error('Slack not configured');
    }

    const payload = {
      text: notification.title,
      attachments: [{
        color: this._getSlackColor(notification.priority),
        title: notification.title,
        text: notification.message,
        timestamp: Math.floor(new Date(notification.timestamp).getTime() / 1000),
        fields: [
          {
            title: 'Priority',
            value: notification.priority,
            short: true
          },
          {
            title: 'Type',
            value: notification.type,
            short: true
          }
        ]
      }]
    };

    const response = await axios.post(slackConfig.webhookUrl, payload, {
      timeout: 5000,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    return {
      status: response.status,
      data: response.data
    };
  }

  /**
   * Select appropriate channels based on notification type and priority
   * @private
   */
  _selectChannels(type, priority = 'medium') {
    const channels = [];

    // Always use webhook if enabled
    if (this.config.channels.webhook?.enabled) {
      channels.push('webhook');
    }

    // Use email for high priority or specific types
    if (this.config.channels.email?.enabled &&
        (priority === 'critical' || priority === 'high' || type === 'system')) {
      channels.push('email');
    }

    // Use Slack for patterns and system alerts
    if (this.config.channels.slack?.enabled &&
        (type === 'pattern' || type === 'system' || priority === 'critical')) {
      channels.push('slack');
    }

    return channels.length > 0 ? channels : ['webhook']; // Fallback to webhook
  }

  /**
   * Map error severity to notification priority
   * @private
   */
  _mapSeverityToPriority(severity) {
    const mapping = {
      'CRITICAL': 'critical',
      'HIGH': 'high',
      'MEDIUM': 'medium',
      'LOW': 'low'
    };

    return mapping[severity] || 'medium';
  }

  /**
   * Get pattern notification priority
   * @private
   */
  _getPatternPriority(patternData) {
    if (patternData.anomalies?.length > 0) return 'high';
    if (patternData.newPatterns?.length > 0) return 'medium';
    return 'low';
  }

  /**
   * Get Slack color for priority
   * @private
   */
  _getSlackColor(priority) {
    const colors = {
      'critical': 'danger',
      'high': 'warning',
      'medium': 'good',
      'low': '#36a64f'
    };

    return colors[priority] || 'good';
  }

  /**
   * Generate unique notification ID
   * @private
   */
  _generateId() {
    return `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Simple delay utility
   * @private
   */
  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get notification queue status
   */
  getQueueStatus() {
    return {
      queueLength: this.notificationQueue.length,
      isProcessing: this.isProcessing,
      enabled: this.config.enabled
    };
  }

  /**
   * Clear notification queue
   */
  clearQueue() {
    this.notificationQueue = [];
    return { cleared: true };
  }
}

module.exports = ErrorNotifier;