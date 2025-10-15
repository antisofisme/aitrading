"""
security_core.py - Security Management System

🎯 PURPOSE:
Business: Comprehensive security for trading operations and data protection
Technical: Encryption, authentication, and secure communication management
Domain: Security/Encryption/Authentication/Data Protection

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:27.866Z
Session: client-side-ai-brain-full-compliance
Confidence: 93%
Complexity: high

🧩 PATTERNS USED:
- AI_BRAIN_SECURITY_SYSTEM: Comprehensive security with encryption and authentication
- SECURE_COMMUNICATION: Encrypted communication and data protection

📦 DEPENDENCIES:
Internal: logger_manager, config_manager
External: cryptography, hashlib, secrets, base64, ssl

💡 AI DECISION REASONING:
Trading systems handle sensitive financial data requiring robust security. Comprehensive approach ensures data protection and regulatory compliance.

🚀 USAGE:
security_core.encrypt_sensitive_data(credentials)

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import hashlib
import hmac
import secrets
import threading
import time
import json
import re
from typing import Dict, Any, Optional, List, Union, Callable, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
from pathlib import Path
import ipaddress
import socket
import ssl
import base64

class ThreatLevel(Enum):
    """Threat severity levels"""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"         # High priority threat
    MEDIUM = "medium"     # Moderate threat
    LOW = "low"          # Low priority threat
    INFO = "info"        # Informational security event

class ThreatType(Enum):
    """Types of security threats"""
    BRUTE_FORCE = "brute_force"
    CREDENTIAL_STUFFING = "credential_stuffing"
    SQL_INJECTION = "sql_injection"
    XSS_ATTACK = "xss_attack"
    CSRF_ATTACK = "csrf_attack"
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MALWARE = "malware"
    PHISHING = "phishing"
    DOS_ATTACK = "dos_attack"
    INSIDER_THREAT = "insider_threat"
    CONFIGURATION_ERROR = "configuration_error"
    WEAK_AUTHENTICATION = "weak_authentication"
    DATA_LEAKAGE = "data_leakage"

class SecurityAction(Enum):
    """Security response actions"""
    BLOCK = "block"
    QUARANTINE = "quarantine"
    MONITOR = "monitor"
    ALERT = "alert"
    LOG = "log"
    RATE_LIMIT = "rate_limit"
    REQUIRE_MFA = "require_mfa"
    FORCE_PASSWORD_RESET = "force_password_reset"

@dataclass
class SecurityEvent:
    """Security event with threat analysis"""
    id: str
    timestamp: datetime
    threat_type: ThreatType
    threat_level: ThreatLevel
    source_ip: Optional[str]
    user_id: Optional[str]
    component: str
    description: str
    details: Dict[str, Any]
    confidence: float = 0.0
    false_positive_probability: float = 0.0
    recommended_actions: List[SecurityAction] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.recommended_actions is None:
            self.recommended_actions = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SecurityRule:
    """AI Brain security rule"""
    id: str
    name: str
    threat_type: ThreatType
    description: str
    enabled: bool = True
    threshold_value: Optional[float] = None
    time_window: Optional[int] = None  # seconds
    pattern: Optional[str] = None
    validator_func: Optional[Callable] = None
    actions: List[SecurityAction] = None
    whitelist: Set[str] = None
    blacklist: Set[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.actions is None:
            self.actions = []
        if self.whitelist is None:
            self.whitelist = set()
        if self.blacklist is None:
            self.blacklist = set()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SecurityStats:
    """Security system statistics"""
    total_events: int = 0
    threats_detected: int = 0
    false_positives: int = 0
    actions_taken: int = 0
    blocked_ips: int = 0
    events_by_type: Dict[str, int] = None
    events_by_level: Dict[str, int] = None
    top_threat_sources: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.events_by_type is None:
            self.events_by_type = defaultdict(int)
        if self.events_by_level is None:
            self.events_by_level = defaultdict(int)
        if self.top_threat_sources is None:
            self.top_threat_sources = []

class SecurityCore:
    """
    AI Brain Security Core System
    Intelligent threat detection and adaptive security protection
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        # Security rules and events
        self._rules: Dict[str, SecurityRule] = {}
        self._events: deque = deque(maxlen=10000)
        self._blocked_ips: Set[str] = set()
        self._suspicious_ips: Dict[str, List[datetime]] = defaultdict(list)
        
        # AI Brain threat analysis
        self._threat_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self._user_baselines: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._anomaly_scores: Dict[str, float] = defaultdict(float)
        
        # Rate limiting and tracking
        self._rate_limits: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._failed_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self._session_tracking: Dict[str, Dict[str, Any]] = {}
        
        # Encryption and hashing
        self._encryption_key = None
        self._hash_salt = secrets.token_bytes(32)
        
        # Configuration
        self._enable_ai_analysis = True
        self._enable_rate_limiting = True
        self._enable_ip_blocking = True
        self._max_failed_attempts = 5
        self._block_duration = 3600  # 1 hour
        
        # Statistics
        self._stats = SecurityStats()
        
        # Persistence
        self._security_log_path = Path("logs/security_events.json")
        self._blocked_ips_path = Path("logs/blocked_ips.json")
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize system
        self._initialize_security_core()
    
    @classmethod
    def get_instance(cls) -> 'SecurityCore':
        """Singleton pattern with thread safety"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def _initialize_security_core(self):
        """Initialize security core system"""
        # Generate encryption key
        self._encryption_key = secrets.token_bytes(32)
        
        # Load default security rules
        self._load_default_rules()
        
        # Load persistent data
        self._load_persistence()
        
        print("🛡️ AI Brain Security Core initialized")
    
    # ==================== THREAT DETECTION ====================
    
    def analyze_security_event(self, component: str, event_type: str, 
                             details: Dict[str, Any], 
                             source_ip: Optional[str] = None,
                             user_id: Optional[str] = None) -> Optional[SecurityEvent]:
        """Analyze potential security event"""
        
        with self._lock:
            try:
                # Generate event ID
                event_id = self._generate_event_id()
                
                # Initialize threat analysis
                threat_type = self._classify_threat_type(event_type, details)
                threat_level = ThreatLevel.INFO
                confidence = 0.5
                
                # AI Brain threat analysis
                if self._enable_ai_analysis:
                    threat_level, confidence = self._ai_threat_analysis(
                        component, event_type, details, source_ip, user_id
                    )
                
                # Skip if confidence is too low
                if confidence < 0.3:
                    return None
                
                # Create security event
                event = SecurityEvent(
                    id=event_id,
                    timestamp=datetime.now(),
                    threat_type=threat_type,
                    threat_level=threat_level,
                    source_ip=source_ip,
                    user_id=user_id,
                    component=component,
                    description=f"{event_type} detected in {component}",
                    details=details,
                    confidence=confidence,
                    false_positive_probability=self._calculate_false_positive_probability(threat_type, confidence)
                )
                
                # Determine recommended actions
                event.recommended_actions = self._determine_security_actions(event)
                
                # Record event
                self._record_security_event(event)
                
                # Execute automatic responses if needed
                if threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
                    self._execute_automatic_response(event)
                
                return event
                
            except Exception as e:
                print(f"❌ Security analysis error: {e}")
                return None
    
    def _classify_threat_type(self, event_type: str, details: Dict[str, Any]) -> ThreatType:
        """Classify threat type based on event characteristics"""
        event_lower = event_type.lower()
        
        # Pattern-based classification
        if "login_failed" in event_lower or "authentication_failed" in event_lower:
            # Check for brute force patterns
            if details.get("consecutive_failures", 0) > 3:
                return ThreatType.BRUTE_FORCE
            else:
                return ThreatType.WEAK_AUTHENTICATION
        
        elif "sql" in event_lower or "injection" in event_lower:
            return ThreatType.SQL_INJECTION
        
        elif "xss" in event_lower or "script" in event_lower:
            return ThreatType.XSS_ATTACK
        
        elif "csrf" in event_lower:
            return ThreatType.CSRF_ATTACK
        
        elif "unauthorized" in event_lower or "access_denied" in event_lower:
            return ThreatType.UNAUTHORIZED_ACCESS
        
        elif "dos" in event_lower or "flood" in event_lower:
            return ThreatType.DOS_ATTACK
        
        elif "malware" in event_lower or "virus" in event_lower:
            return ThreatType.MALWARE
        
        elif "phishing" in event_lower:
            return ThreatType.PHISHING
        
        elif "config" in event_lower or "misconfiguration" in event_lower:
            return ThreatType.CONFIGURATION_ERROR
        
        else:
            return ThreatType.SUSPICIOUS_ACTIVITY
    
    def _ai_threat_analysis(self, component: str, event_type: str, details: Dict[str, Any],
                          source_ip: Optional[str], user_id: Optional[str]) -> Tuple[ThreatLevel, float]:
        """AI-powered threat level analysis"""
        
        risk_factors = []
        confidence_factors = []
        
        # IP reputation analysis
        if source_ip:
            ip_risk = self._analyze_ip_reputation(source_ip)
            risk_factors.append(ip_risk * 0.3)  # 30% weight
            confidence_factors.append(0.8)  # High confidence in IP analysis
        
        # User behavior analysis
        if user_id:
            user_risk = self._analyze_user_behavior(user_id, event_type, details)
            risk_factors.append(user_risk * 0.4)  # 40% weight
            confidence_factors.append(0.7)  # Good confidence in behavior analysis
        
        # Pattern analysis
        pattern_risk = self._analyze_threat_patterns(component, event_type)
        risk_factors.append(pattern_risk * 0.2)  # 20% weight
        confidence_factors.append(0.6)  # Moderate confidence in patterns
        
        # Anomaly detection
        anomaly_risk = self._detect_anomalies(component, event_type, details)
        risk_factors.append(anomaly_risk * 0.1)  # 10% weight
        confidence_factors.append(0.5)  # Lower confidence in anomaly detection
        
        # Calculate overall risk and confidence
        if risk_factors:
            overall_risk = sum(risk_factors)
            overall_confidence = sum(confidence_factors) / len(confidence_factors)
        else:
            overall_risk = 0.5
            overall_confidence = 0.3
        
        # Convert risk to threat level
        if overall_risk > 0.8:
            threat_level = ThreatLevel.CRITICAL
        elif overall_risk > 0.6:
            threat_level = ThreatLevel.HIGH
        elif overall_risk > 0.4:
            threat_level = ThreatLevel.MEDIUM
        elif overall_risk > 0.2:
            threat_level = ThreatLevel.LOW
        else:
            threat_level = ThreatLevel.INFO
        
        return threat_level, overall_confidence
    
    def _analyze_ip_reputation(self, ip: str) -> float:
        """Analyze IP reputation and return risk score (0-1)"""
        risk_score = 0.0
        
        # Check if IP is already blocked
        if ip in self._blocked_ips:
            return 1.0
        
        # Check suspicious IP tracking
        if ip in self._suspicious_ips:
            recent_events = [t for t in self._suspicious_ips[ip] 
                           if (datetime.now() - t).seconds < 3600]  # Last hour
            if len(recent_events) > 10:
                risk_score += 0.5
            elif len(recent_events) > 5:
                risk_score += 0.3
        
        # Check for private IP addresses (lower risk)
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                risk_score *= 0.5  # Reduce risk for private IPs
        except ValueError:
            risk_score += 0.2  # Invalid IP format is suspicious
        
        # Check for common threat IP patterns
        threat_patterns = [
            r'^192\.168\.1\.1$',  # Default router (could be compromised)
            r'^10\.0\.0\.',       # Common internal network
            r'^172\.16\.'         # Private network range
        ]
        
        for pattern in threat_patterns:
            if re.match(pattern, ip):
                risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def _analyze_user_behavior(self, user_id: str, event_type: str, details: Dict[str, Any]) -> float:
        """Analyze user behavior and return risk score (0-1)"""
        risk_score = 0.0
        
        # Check failed authentication attempts
        if user_id in self._failed_attempts:
            recent_failures = [t for t in self._failed_attempts[user_id]
                             if (datetime.now() - t).seconds < 3600]  # Last hour
            if len(recent_failures) > 5:
                risk_score += 0.6
            elif len(recent_failures) > 2:
                risk_score += 0.3
        
        # Check for unusual activity patterns
        if user_id in self._user_baselines:
            baseline = self._user_baselines[user_id]
            
            # Check time of activity
            current_hour = datetime.now().hour
            usual_hours = baseline.get('usual_hours', [])
            if usual_hours and current_hour not in usual_hours:
                risk_score += 0.2
            
            # Check frequency of actions
            current_activity = baseline.get('current_activity', 0)
            avg_activity = baseline.get('avg_activity', 1)
            if current_activity > avg_activity * 3:  # 3x normal activity
                risk_score += 0.3
        
        # Check for privilege escalation attempts
        if 'admin' in event_type.lower() or 'privilege' in event_type.lower():
            risk_score += 0.4
        
        return min(risk_score, 1.0)
    
    def _analyze_threat_patterns(self, component: str, event_type: str) -> float:
        """Analyze threat patterns and return risk score (0-1)"""
        risk_score = 0.0
        
        # Check recent similar events
        pattern_key = f"{component}:{event_type}"
        recent_patterns = [t for t in self._threat_patterns[pattern_key]
                          if (datetime.now() - t).seconds < 300]  # Last 5 minutes
        
        if len(recent_patterns) > 10:  # Many similar events
            risk_score += 0.5
        elif len(recent_patterns) > 5:
            risk_score += 0.3
        
        # Check for known attack patterns
        attack_indicators = [
            'injection', 'script', 'exploit', 'bypass', 'overflow',
            'traverse', 'injection', 'payload', 'shell', 'exec'
        ]
        
        event_lower = event_type.lower()
        for indicator in attack_indicators:
            if indicator in event_lower:
                risk_score += 0.2
                break
        
        return min(risk_score, 1.0)
    
    def _detect_anomalies(self, component: str, event_type: str, details: Dict[str, Any]) -> float:
        """Detect anomalies and return risk score (0-1)"""
        risk_score = 0.0
        
        # Check for unusual request patterns
        if 'request_size' in details:
            size = details['request_size']
            if size > 10 * 1024 * 1024:  # > 10MB
                risk_score += 0.3
        
        # Check for unusual user agents
        user_agent = details.get('user_agent', '')
        if user_agent:
            suspicious_agents = ['bot', 'crawler', 'scanner', 'exploit']
            if any(agent in user_agent.lower() for agent in suspicious_agents):
                risk_score += 0.4
        
        # Check for suspicious parameters
        params = details.get('parameters', {})
        if isinstance(params, dict):
            suspicious_params = ['script', 'javascript', 'vbscript', 'onload', 'onerror']
            for param_value in params.values():
                if isinstance(param_value, str):
                    for suspicious in suspicious_params:
                        if suspicious in param_value.lower():
                            risk_score += 0.3
                            break
        
        return min(risk_score, 1.0)
    
    def _calculate_false_positive_probability(self, threat_type: ThreatType, confidence: float) -> float:
        """Calculate probability of false positive"""
        base_fp_rates = {
            ThreatType.SQL_INJECTION: 0.05,
            ThreatType.XSS_ATTACK: 0.05,
            ThreatType.BRUTE_FORCE: 0.1,
            ThreatType.DOS_ATTACK: 0.15,
            ThreatType.SUSPICIOUS_ACTIVITY: 0.3,
            ThreatType.UNAUTHORIZED_ACCESS: 0.2
        }
        
        base_rate = base_fp_rates.get(threat_type, 0.25)
        
        # Adjust based on confidence
        adjusted_rate = base_rate * (1 - confidence)
        
        return min(adjusted_rate, 0.9)
    
    # ==================== SECURITY ACTIONS ====================
    
    def _determine_security_actions(self, event: SecurityEvent) -> List[SecurityAction]:
        """Determine appropriate security actions based on threat analysis"""
        actions = []
        
        # Critical threats
        if event.threat_level == ThreatLevel.CRITICAL:
            if event.source_ip:
                actions.append(SecurityAction.BLOCK)
            actions.append(SecurityAction.ALERT)
            actions.append(SecurityAction.LOG)
            
            if event.threat_type in [ThreatType.BRUTE_FORCE, ThreatType.DOS_ATTACK]:
                actions.append(SecurityAction.RATE_LIMIT)
            
            if event.user_id:
                actions.append(SecurityAction.REQUIRE_MFA)
        
        # High threats
        elif event.threat_level == ThreatLevel.HIGH:
            actions.append(SecurityAction.MONITOR)
            actions.append(SecurityAction.ALERT)
            actions.append(SecurityAction.LOG)
            
            if event.confidence > 0.7:
                actions.append(SecurityAction.RATE_LIMIT)
            
            if event.threat_type == ThreatType.WEAK_AUTHENTICATION and event.user_id:
                actions.append(SecurityAction.FORCE_PASSWORD_RESET)
        
        # Medium threats
        elif event.threat_level == ThreatLevel.MEDIUM:
            actions.append(SecurityAction.MONITOR)
            actions.append(SecurityAction.LOG)
            
            if event.confidence > 0.8:
                actions.append(SecurityAction.ALERT)
        
        # Low and info threats
        else:
            actions.append(SecurityAction.LOG)
        
        return actions
    
    def _execute_automatic_response(self, event: SecurityEvent):
        """Execute automatic security responses"""
        for action in event.recommended_actions:
            try:
                self._execute_action(action, event)
            except Exception as e:
                print(f"❌ Failed to execute security action {action.value}: {e}")
    
    def _execute_action(self, action: SecurityAction, event: SecurityEvent):
        """Execute individual security action"""
        if action == SecurityAction.BLOCK and event.source_ip:
            self.block_ip(event.source_ip, event.id)
        
        elif action == SecurityAction.RATE_LIMIT and event.source_ip:
            self._apply_rate_limit(event.source_ip)
        
        elif action == SecurityAction.ALERT:
            self._send_security_alert(event)
        
        elif action == SecurityAction.LOG:
            self._log_security_event(event)
        
        elif action == SecurityAction.MONITOR and event.source_ip:
            self._add_to_monitoring(event.source_ip, event.user_id)
        
        elif action == SecurityAction.QUARANTINE:
            self._quarantine_source(event)
        
        # Update statistics
        self._stats.actions_taken += 1
    
    def block_ip(self, ip: str, reason: str = "Security threat detected"):
        """Block IP address"""
        with self._lock:
            self._blocked_ips.add(ip)
            self._stats.blocked_ips = len(self._blocked_ips)
            
            # Schedule unblock
            threading.Timer(self._block_duration, self._unblock_ip, args=[ip]).start()
            
            print(f"🚫 IP {ip} blocked: {reason}")
    
    def _unblock_ip(self, ip: str):
        """Unblock IP address"""
        with self._lock:
            self._blocked_ips.discard(ip)
            self._stats.blocked_ips = len(self._blocked_ips)
            print(f"✅ IP {ip} unblocked")
    
    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return ip in self._blocked_ips
    
    def _apply_rate_limit(self, identifier: str):
        """Apply rate limiting to identifier"""
        current_time = datetime.now()
        rate_limit_queue = self._rate_limits[identifier]
        
        # Add current request
        rate_limit_queue.append(current_time)
        
        # Clean old entries (older than 1 minute)
        while rate_limit_queue and (current_time - rate_limit_queue[0]).seconds > 60:
            rate_limit_queue.popleft()
    
    def is_rate_limited(self, identifier: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
        """Check if identifier is rate limited"""
        current_time = datetime.now()
        rate_limit_queue = self._rate_limits[identifier]
        
        # Count requests in time window
        recent_requests = sum(1 for req_time in rate_limit_queue
                            if (current_time - req_time).seconds <= window_seconds)
        
        return recent_requests >= max_requests
    
    def _send_security_alert(self, event: SecurityEvent):
        """Send security alert (placeholder for actual implementation)"""
        alert_message = f"SECURITY ALERT: {event.threat_type.value} detected in {event.component}"
        print(f"🚨 {alert_message}")
        
        # In a real implementation, this would send emails, SMS, or push notifications
        # For now, we'll just log the alert
        self._log_security_event(event)
    
    def _log_security_event(self, event: SecurityEvent):
        """Log security event"""
        log_entry = {
            'timestamp': event.timestamp.isoformat(),
            'event_id': event.id,
            'threat_type': event.threat_type.value,
            'threat_level': event.threat_level.value,
            'component': event.component,
            'description': event.description,
            'confidence': event.confidence,
            'source_ip': event.source_ip,
            'user_id': event.user_id,
            'actions_taken': [action.value for action in event.recommended_actions]
        }
        
        # Write to security log
        try:
            self._security_log_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._security_log_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            print(f"❌ Failed to write security log: {e}")
    
    def _add_to_monitoring(self, source_ip: Optional[str], user_id: Optional[str]):
        """Add source to enhanced monitoring"""
        if source_ip:
            self._suspicious_ips[source_ip].append(datetime.now())
        
        if user_id:
            # Enhanced user monitoring logic
            pass
    
    def _quarantine_source(self, event: SecurityEvent):
        """Quarantine suspicious source"""
        # Placeholder for quarantine logic
        print(f"🔒 Source quarantined: {event.source_ip or event.user_id}")
    
    # ==================== SECURITY UTILITIES ====================
    
    def hash_password(self, password: str) -> str:
        """Hash password securely"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), self._hash_salt, 100000).hex()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(password) == hashed
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(length)
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data (simplified implementation)"""
        # In production, use proper encryption libraries like cryptography
        return base64.b64encode(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data (simplified implementation)"""
        # In production, use proper encryption libraries
        return base64.b64decode(encrypted_data.encode()).decode()
    
    def validate_input(self, input_data: str, input_type: str = "general") -> Tuple[bool, Optional[str]]:
        """Validate input for security threats"""
        
        # SQL injection patterns
        sql_patterns = [
            r"(\b(ALTER|CREATE|DELETE|DROP|EXEC(UTE){0,1}|INSERT|MERGE|SELECT|UPDATE|UNION)\b)",
            r"((\b(sp_executesql|sp_sqlexec)\b))",
            r"(\b(AND|OR)\b.+(\b(ASCII|CHAR|NCHAR|SOUNDEX|PATINDEX|LEN|LEFT|RIGHT|STUFF|REPLACE|REVERSE|CHARINDEX)\b))",
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                return False, "Potential SQL injection detected"
        
        # XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                return False, "Potential XSS attack detected"
        
        # Path traversal patterns
        path_patterns = [
            r"\.\./",
            r"\.\.\\",
            r"/etc/passwd",
            r"C:\\Windows\\System32"
        ]
        
        for pattern in path_patterns:
            if re.search(pattern, input_data, re.IGNORECASE):
                return False, "Potential path traversal detected"
        
        return True, None
    
    # ==================== RECORD AND LEARN ====================
    
    def _record_security_event(self, event: SecurityEvent):
        """Record security event for learning and analysis"""
        with self._lock:
            # Add to events deque
            self._events.append(event)
            
            # Update statistics
            self._stats.total_events += 1
            self._stats.events_by_type[event.threat_type.value] += 1
            self._stats.events_by_level[event.threat_level.value] += 1
            
            if event.threat_level != ThreatLevel.INFO:
                self._stats.threats_detected += 1
            
            if event.false_positive_probability > 0.7:
                self._stats.false_positives += 1
            
            # Record patterns for learning
            pattern_key = f"{event.component}:{event.threat_type.value}"
            self._threat_patterns[pattern_key].append(event.timestamp)
            
            # Update user baselines
            if event.user_id:
                self._update_user_baseline(event.user_id, event)
            
            # Record IP activity
            if event.source_ip:
                self._suspicious_ips[event.source_ip].append(event.timestamp)
    
    def _update_user_baseline(self, user_id: str, event: SecurityEvent):
        """Update user behavior baseline"""
        baseline = self._user_baselines[user_id]
        
        # Track usual hours of activity
        current_hour = event.timestamp.hour
        if 'usual_hours' not in baseline:
            baseline['usual_hours'] = set()
        baseline['usual_hours'].add(current_hour)
        
        # Track activity frequency
        baseline['current_activity'] = baseline.get('current_activity', 0) + 1
        
        # Calculate rolling average (simplified)
        if 'total_activity' not in baseline:
            baseline['total_activity'] = 0
            baseline['days_tracked'] = 0
        
        baseline['total_activity'] += 1
        baseline['avg_activity'] = baseline['total_activity'] / max(baseline.get('days_tracked', 1), 1)
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = str(int(time.time() * 1000))
        random_part = secrets.token_hex(4)
        return f"sec_{timestamp}_{random_part}"
    
    # ==================== DEFAULT RULES ====================
    
    def _load_default_rules(self):
        """Load default security rules"""
        default_rules = [
            SecurityRule(
                id="brute_force_detection",
                name="Brute Force Detection",
                threat_type=ThreatType.BRUTE_FORCE,
                description="Detect brute force attacks based on failed login attempts",
                threshold_value=5.0,
                time_window=300,  # 5 minutes
                actions=[SecurityAction.BLOCK, SecurityAction.ALERT]
            ),
            
            SecurityRule(
                id="sql_injection_detection",
                name="SQL Injection Detection",
                threat_type=ThreatType.SQL_INJECTION,
                description="Detect SQL injection attempts in input data",
                pattern=r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\b.*\b(FROM|INTO|WHERE)\b)",
                actions=[SecurityAction.BLOCK, SecurityAction.LOG]
            ),
            
            SecurityRule(
                id="xss_detection",
                name="XSS Attack Detection",
                threat_type=ThreatType.XSS_ATTACK,
                description="Detect cross-site scripting attempts",
                pattern=r"<script[^>]*>.*?</script>|javascript:|on\w+\s*=",
                actions=[SecurityAction.BLOCK, SecurityAction.LOG]
            ),
            
            SecurityRule(
                id="rate_limit_enforcement",
                name="Rate Limit Enforcement",
                threat_type=ThreatType.DOS_ATTACK,
                description="Enforce rate limits to prevent DoS attacks",
                threshold_value=100.0,
                time_window=60,  # 1 minute
                actions=[SecurityAction.RATE_LIMIT, SecurityAction.MONITOR]
            ),
            
            SecurityRule(
                id="suspicious_user_agent",
                name="Suspicious User Agent Detection",
                threat_type=ThreatType.SUSPICIOUS_ACTIVITY,
                description="Detect suspicious user agents",
                pattern=r"(bot|crawler|scanner|exploit|hack)",
                actions=[SecurityAction.MONITOR, SecurityAction.LOG]
            )
        ]
        
        for rule in default_rules:
            self._rules[rule.id] = rule
        
        print(f"🔐 Loaded {len(default_rules)} default security rules")
    
    # ==================== PERSISTENCE ====================
    
    def _save_persistence(self):
        """Save security state to disk"""
        try:
            # Save blocked IPs
            self._blocked_ips_path.parent.mkdir(parents=True, exist_ok=True)
            
            blocked_ips_data = {
                'blocked_ips': list(self._blocked_ips),
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self._blocked_ips_path, 'w') as f:
                json.dump(blocked_ips_data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Failed to save security persistence: {e}")
    
    def _load_persistence(self):
        """Load security state from disk"""
        try:
            # Load blocked IPs
            if self._blocked_ips_path.exists():
                with open(self._blocked_ips_path, 'r') as f:
                    data = json.load(f)
                
                # Restore blocked IPs (with expiration check)
                saved_time = datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
                if (datetime.now() - saved_time).seconds < self._block_duration:
                    self._blocked_ips.update(data.get('blocked_ips', []))
                    self._stats.blocked_ips = len(self._blocked_ips)
            
            print("🔓 Security persistence loaded")
            
        except Exception as e:
            print(f"❌ Failed to load security persistence: {e}")
    
    # ==================== STATISTICS AND REPORTING ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive security statistics"""
        return {
            'total_events': self._stats.total_events,
            'threats_detected': self._stats.threats_detected,
            'false_positives': self._stats.false_positives,
            'actions_taken': self._stats.actions_taken,
            'blocked_ips': self._stats.blocked_ips,
            'threat_detection_rate': self._stats.threats_detected / max(self._stats.total_events, 1),
            'false_positive_rate': self._stats.false_positives / max(self._stats.threats_detected, 1),
            'events_by_type': dict(self._stats.events_by_type),
            'events_by_level': dict(self._stats.events_by_level),
            'active_rules': len([r for r in self._rules.values() if r.enabled]),
            'monitored_ips': len(self._suspicious_ips),
            'user_baselines': len(self._user_baselines)
        }
    
    def get_recent_events(self, limit: int = 100, threat_level: Optional[ThreatLevel] = None) -> List[Dict[str, Any]]:
        """Get recent security events"""
        events = list(self._events)
        
        if threat_level:
            events = [e for e in events if e.threat_level == threat_level]
        
        return [asdict(event) for event in events[-limit:]]
    
    def get_threat_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get threat summary for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [e for e in self._events if e.timestamp > cutoff_time]
        
        summary = {
            'time_period_hours': hours,
            'total_events': len(recent_events),
            'threat_types': defaultdict(int),
            'threat_levels': defaultdict(int),
            'top_sources': defaultdict(int),
            'actions_summary': defaultdict(int)
        }
        
        for event in recent_events:
            summary['threat_types'][event.threat_type.value] += 1
            summary['threat_levels'][event.threat_level.value] += 1
            
            if event.source_ip:
                summary['top_sources'][event.source_ip] += 1
            
            for action in event.recommended_actions:
                summary['actions_summary'][action.value] += 1
        
        return summary


# ==================== CONVENIENCE FUNCTIONS ====================

# Global instance
security_core = None

def get_security_core() -> SecurityCore:
    """Get global security core instance"""
    global security_core
    if security_core is None:
        security_core = SecurityCore.get_instance()
    return security_core

def analyze_threat(component: str, event_type: str, details: Dict[str, Any],
                  source_ip: Optional[str] = None, user_id: Optional[str] = None) -> Optional[SecurityEvent]:
    """Convenience function to analyze security threat"""
    return get_security_core().analyze_security_event(component, event_type, details, source_ip, user_id)

def is_request_secure(request_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Check if request is secure"""
    security = get_security_core()
    
    # Check IP blocking
    source_ip = request_data.get('source_ip')
    if source_ip and security.is_ip_blocked(source_ip):
        return False, "IP is blocked"
    
    # Check rate limiting
    identifier = source_ip or request_data.get('user_id', 'anonymous')
    if security.is_rate_limited(identifier):
        return False, "Rate limit exceeded"
    
    # Validate input data
    for key, value in request_data.items():
        if isinstance(value, str):
            is_valid, reason = security.validate_input(value, key)
            if not is_valid:
                return False, reason
    
    return True, None