const EventEmitter = require('events');
const moment = require('moment-timezone');
const { TRADING_SESSIONS } = require('../config/forexPairs');
const logger = require('../utils/logger');

class SessionManager extends EventEmitter {
  constructor(options = {}) {
    super();
    this.currentSession = null;
    this.sessionData = new Map();
    this.checkInterval = options.checkInterval || 60000; // Check every minute
    this.preSessionAlert = options.preSessionAlert || 300000; // 5 minutes before
    this.postSessionAlert = options.postSessionAlert || 300000; // 5 minutes after
    
    this.initializeSessions();
    this.startSessionMonitoring();
  }

  /**
   * Initialize trading sessions with Indonesian timezone considerations
   */
  initializeSessions() {
    // Convert session times to Indonesian timezone (UTC+7)
    const indonesianTimezone = 'Asia/Jakarta';
    
    Object.keys(TRADING_SESSIONS).forEach(sessionKey => {
      const session = TRADING_SESSIONS[sessionKey];
      
      this.sessionData.set(sessionKey, {
        ...session,
        indonesianTime: this.convertToIndonesianTime(session),
        active: false,
        volume: 0,
        volatility: 0,
        spread: { avg: 0, min: 0, max: 0 },
        lastUpdate: null
      });
    });

    logger.info('Trading sessions initialized for Indonesian market', {
      timezone: indonesianTimezone,
      sessions: Object.keys(TRADING_SESSIONS)
    });
  }

  /**
   * Convert session times to Indonesian timezone
   */
  convertToIndonesianTime(session) {
    const now = moment();
    const sessionStart = moment.tz(session.start, 'HH:mm', session.timezone);
    const sessionEnd = moment.tz(session.end, 'HH:mm', session.timezone);
    
    // Convert to Indonesian time
    const startIndonesian = sessionStart.clone().tz('Asia/Jakarta');
    const endIndonesian = sessionEnd.clone().tz('Asia/Jakarta');
    
    return {
      start: startIndonesian.format('HH:mm'),
      end: endIndonesian.format('HH:mm'),
      startUTC: sessionStart.utc().format('HH:mm'),
      endUTC: sessionEnd.utc().format('HH:mm')
    };
  }

  /**
   * Get current active trading session
   */
  getCurrentSession() {
    const now = moment.utc();
    const currentHour = now.hour();
    const currentMinute = now.minute();
    const currentTime = currentHour * 60 + currentMinute;

    for (const [sessionKey, sessionData] of this.sessionData.entries()) {
      const session = TRADING_SESSIONS[sessionKey];
      const startTime = this.parseTime(session.start);
      const endTime = this.parseTime(session.end);
      
      // Handle sessions that cross midnight
      if (startTime > endTime) {
        if (currentTime >= startTime || currentTime <= endTime) {
          return {
            name: sessionKey,
            ...sessionData,
            active: true,
            timeRemaining: this.calculateTimeRemaining(currentTime, endTime)
          };
        }
      } else {
        if (currentTime >= startTime && currentTime <= endTime) {
          return {
            name: sessionKey,
            ...sessionData,
            active: true,
            timeRemaining: this.calculateTimeRemaining(currentTime, endTime)
          };
        }
      }
    }

    return null;
  }

  /**
   * Parse time string to minutes
   */
  parseTime(timeString) {
    const [hour, minute] = timeString.split(':').map(Number);
    return hour * 60 + minute;
  }

  /**
   * Calculate time remaining in session
   */
  calculateTimeRemaining(currentTime, endTime) {
    let remaining = endTime - currentTime;
    if (remaining < 0) {
      remaining += 24 * 60; // Add 24 hours for next day
    }
    
    const hours = Math.floor(remaining / 60);
    const minutes = remaining % 60;
    
    return {
      total: remaining,
      hours,
      minutes,
      formatted: `${hours}h ${minutes}m`
    };
  }

  /**
   * Get next trading session
   */
  getNextSession() {
    const now = moment.utc();
    const currentTime = now.hour() * 60 + now.minute();
    let nextSession = null;
    let minTimeDiff = 24 * 60; // 24 hours in minutes

    for (const [sessionKey, sessionData] of this.sessionData.entries()) {
      const session = TRADING_SESSIONS[sessionKey];
      const startTime = this.parseTime(session.start);
      
      let timeDiff = startTime - currentTime;
      if (timeDiff <= 0) {
        timeDiff += 24 * 60; // Next day
      }
      
      if (timeDiff < minTimeDiff) {
        minTimeDiff = timeDiff;
        nextSession = {
          name: sessionKey,
          ...sessionData,
          startsIn: this.formatTimeDifference(timeDiff)
        };
      }
    }

    return nextSession;
  }

  /**
   * Format time difference
   */
  formatTimeDifference(minutes) {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return {
      total: minutes,
      hours,
      minutes: mins,
      formatted: `${hours}h ${mins}m`
    };
  }

  /**
   * Get session-specific trading recommendations
   */
  getSessionRecommendations(sessionName = null) {
    const session = sessionName ? this.sessionData.get(sessionName) : this.getCurrentSession();
    
    if (!session) {
      return {
        recommendation: 'No active session',
        pairs: [],
        strategy: 'hold',
        riskLevel: 'high'
      };
    }

    const sessionConfig = TRADING_SESSIONS[session.name || sessionName];
    
    return {
      recommendation: this.getSessionStrategy(sessionConfig),
      pairs: sessionConfig.majorPairs,
      strategy: this.getOptimalStrategy(sessionConfig),
      riskLevel: this.getRiskLevel(sessionConfig),
      characteristics: sessionConfig.characteristics,
      indonesianTime: session.indonesianTime
    };
  }

  /**
   * Get session-specific strategy
   */
  getSessionStrategy(session) {
    switch (session.characteristics.volatility) {
      case 'high':
        return 'Aggressive trading recommended - High volatility and volume';
      case 'medium':
        return 'Moderate trading - Medium volatility, good opportunities';
      case 'low':
        return 'Conservative trading - Low volatility, tight ranges';
      default:
        return 'Standard trading approach';
    }
  }

  /**
   * Get optimal trading strategy for session
   */
  getOptimalStrategy(session) {
    const volatility = session.characteristics.volatility;
    const volume = session.characteristics.volume;
    
    if (volatility === 'high' && volume === 'high') {
      return 'breakout';
    } else if (volatility === 'low' && volume === 'low') {
      return 'range';
    } else if (volatility === 'medium') {
      return 'trend_following';
    }
    
    return 'adaptive';
  }

  /**
   * Get risk level for session
   */
  getRiskLevel(session) {
    const volatility = session.characteristics.volatility;
    const spreads = session.characteristics.spreads;
    
    if (volatility === 'high' && spreads === 'tight') {
      return 'medium';
    } else if (volatility === 'low' && spreads === 'wide') {
      return 'low';
    } else if (volatility === 'high' && spreads === 'wide') {
      return 'high';
    }
    
    return 'medium';
  }

  /**
   * Check for session overlaps
   */
  getSessionOverlaps() {
    const now = moment.utc();
    const activeSessions = [];
    
    for (const [sessionKey, sessionData] of this.sessionData.entries()) {
      const session = TRADING_SESSIONS[sessionKey];
      const startTime = this.parseTime(session.start);
      const endTime = this.parseTime(session.end);
      const currentTime = now.hour() * 60 + now.minute();
      
      let isActive = false;
      if (startTime > endTime) {
        isActive = currentTime >= startTime || currentTime <= endTime;
      } else {
        isActive = currentTime >= startTime && currentTime <= endTime;
      }
      
      if (isActive) {
        activeSessions.push({
          name: sessionKey,
          ...sessionData,
          timeRemaining: this.calculateTimeRemaining(currentTime, endTime)
        });
      }
    }
    
    return {
      count: activeSessions.length,
      sessions: activeSessions,
      isOverlap: activeSessions.length > 1,
      recommendations: activeSessions.length > 1 ? this.getOverlapRecommendations(activeSessions) : null
    };
  }

  /**
   * Get recommendations for session overlaps
   */
  getOverlapRecommendations(activeSessions) {
    const sessionNames = activeSessions.map(s => s.name);
    
    // London-NY overlap (most liquid)
    if (sessionNames.includes('EUROPE') && sessionNames.includes('US')) {
      return {
        strategy: 'aggressive',
        pairs: ['EURUSD', 'GBPUSD', 'USDCHF'],
        volatility: 'very_high',
        liquidity: 'maximum',
        spreads: 'tightest',
        recommendation: 'Prime trading time - Maximum liquidity and volatility'
      };
    }
    
    // Asia-Europe overlap
    if (sessionNames.includes('ASIA') && sessionNames.includes('EUROPE')) {
      return {
        strategy: 'moderate',
        pairs: ['EURJPY', 'GBPJPY', 'EURGBP'],
        volatility: 'medium',
        liquidity: 'high',
        spreads: 'medium',
        recommendation: 'Good trading opportunities with moderate risk'
      };
    }
    
    return {
      strategy: 'adaptive',
      pairs: [],
      volatility: 'variable',
      liquidity: 'medium',
      spreads: 'variable',
      recommendation: 'Mixed session characteristics - Use adaptive strategy'
    };
  }

  /**
   * Start session monitoring
   */
  startSessionMonitoring() {
    this.monitoringInterval = setInterval(() => {
      this.checkSessionChanges();
    }, this.checkInterval);
    
    logger.info('Session monitoring started', {
      checkInterval: this.checkInterval,
      preSessionAlert: this.preSessionAlert,
      postSessionAlert: this.postSessionAlert
    });
  }

  /**
   * Check for session changes and emit events
   */
  checkSessionChanges() {
    const newSession = this.getCurrentSession();
    const overlaps = this.getSessionOverlaps();
    
    // Check for session start/end
    if (newSession && (!this.currentSession || this.currentSession.name !== newSession.name)) {
      this.currentSession = newSession;
      this.emit('sessionStart', {
        session: newSession,
        overlaps: overlaps,
        recommendations: this.getSessionRecommendations(newSession.name),
        timestamp: Date.now()
      });
      
      logger.info('Trading session started', {
        session: newSession.name,
        overlaps: overlaps.count
      });
    }
    
    if (!newSession && this.currentSession) {
      this.emit('sessionEnd', {
        session: this.currentSession,
        nextSession: this.getNextSession(),
        timestamp: Date.now()
      });
      
      logger.info('Trading session ended', {
        session: this.currentSession.name
      });
      
      this.currentSession = null;
    }
    
    // Check for upcoming sessions
    this.checkUpcomingSessions();
    
    // Emit regular update
    this.emit('sessionUpdate', {
      currentSession: this.currentSession,
      nextSession: this.getNextSession(),
      overlaps: overlaps,
      timestamp: Date.now()
    });
  }

  /**
   * Check for upcoming sessions and send alerts
   */
  checkUpcomingSessions() {
    const nextSession = this.getNextSession();
    
    if (nextSession && nextSession.startsIn.total <= this.preSessionAlert / 60000) {
      this.emit('sessionAlert', {
        type: 'upcoming',
        session: nextSession,
        startsIn: nextSession.startsIn,
        recommendations: this.getSessionRecommendations(nextSession.name),
        timestamp: Date.now()
      });
    }
  }

  /**
   * Update session data with real-time metrics
   */
  updateSessionMetrics(sessionName, metrics) {
    const sessionData = this.sessionData.get(sessionName);
    if (sessionData) {
      sessionData.volume = metrics.volume || sessionData.volume;
      sessionData.volatility = metrics.volatility || sessionData.volatility;
      sessionData.spread = metrics.spread || sessionData.spread;
      sessionData.lastUpdate = Date.now();
      
      this.emit('sessionMetricsUpdate', {
        session: sessionName,
        metrics: sessionData,
        timestamp: Date.now()
      });
    }
  }

  /**
   * Get all session data
   */
  getAllSessions() {
    const sessions = {};
    
    for (const [sessionKey, sessionData] of this.sessionData.entries()) {
      sessions[sessionKey] = {
        ...sessionData,
        config: TRADING_SESSIONS[sessionKey]
      };
    }
    
    return sessions;
  }

  /**
   * Get session statistics
   */
  getSessionStatistics() {
    const current = this.getCurrentSession();
    const next = this.getNextSession();
    const overlaps = this.getSessionOverlaps();
    
    return {
      currentSession: current,
      nextSession: next,
      overlaps: overlaps,
      totalSessions: this.sessionData.size,
      activeSessions: overlaps.count,
      timezone: 'Asia/Jakarta',
      lastCheck: Date.now()
    };
  }

  /**
   * Stop session monitoring
   */
  stop() {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
    logger.info('Session monitoring stopped');
  }
}

module.exports = SessionManager;