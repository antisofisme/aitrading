#!/usr/bin/env python3
"""
security_scan.py - Security Scanning Utility

🎯 PURPOSE:
Business: Automated security scanning for vulnerabilities and compliance
Technical: Security audit with vulnerability detection and reporting
Domain: Security/Vulnerability Scanning/Compliance

🤖 AI GENERATION INFO:
Generated: 2025-08-25T02:45:28.071Z
Session: client-side-ai-brain-full-compliance
Confidence: 87%
Complexity: medium

🧩 PATTERNS USED:
- AI_BRAIN_SECURITY_SCANNING: Automated security vulnerability scanning

📦 DEPENDENCIES:
Internal: security_core, logger_manager
External: subprocess, json, pathlib, hashlib

💡 AI DECISION REASONING:
Trading systems require regular security scanning to identify vulnerabilities and ensure compliance with financial regulations.

🚀 USAGE:
python security_scan.py --full-scan --report

See also:
- ai-brain/memory/pattern-registry.json
- implementations/ for domain-specific examples
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib

@dataclass
class SecurityViolation:
    """Security violation data structure"""
    file_path: str
    line_number: int
    violation_type: str
    severity: str
    content: str
    context: str
    recommendation: str
    risk_score: int  # 0-100

class SecurityScanner:
    """
    Comprehensive security scanner for credential detection and validation
    """
    
    def __init__(self):
        self.violations: List[SecurityViolation] = []
        self.scan_stats = {
            'files_scanned': 0,
            'violations_found': 0,
            'critical_violations': 0,
            'high_violations': 0,
            'medium_violations': 0,
            'low_violations': 0
        }
        
        # Define security patterns to detect
        self.security_patterns = {
            'hardcoded_password': {
                'patterns': [
                    r'["\']?password["\']?\s*[:=]\s*["\'][^"\']{8,}["\']',
                    r'["\']?PASSWORD["\']?\s*[:=]\s*["\'][^"\']{8,}["\']',
                    r'["\']?pwd["\']?\s*[:=]\s*["\'][^"\']{6,}["\']',
                    r'["\']?secret["\']?\s*[:=]\s*["\'][^"\']{8,}["\']',
                ],
                'severity': 'CRITICAL',
                'risk_score': 95,
                'recommendation': 'Replace with environment variable or secure vault'
            },
            'api_key': {
                'patterns': [
                    r'["\']?api[_-]?key["\']?\s*[:=]\s*["\'][A-Za-z0-9]{20,}["\']',
                    r'["\']?apikey["\']?\s*[:=]\s*["\'][A-Za-z0-9]{20,}["\']',
                    r'["\']?API[_-]?KEY["\']?\s*[:=]\s*["\'][A-Za-z0-9]{20,}["\']',
                ],
                'severity': 'CRITICAL',
                'risk_score': 90,
                'recommendation': 'Use environment variables for API keys'
            },
            'database_connection': {
                'patterns': [
                    r'["\']?connection[_-]?string["\']?\s*[:=]\s*["\'][^"\']*://[^"\']*["\']',
                    r'["\']?database[_-]?url["\']?\s*[:=]\s*["\'][^"\']*://[^"\']*["\']',
                    r'["\']?db[_-]?url["\']?\s*[:=]\s*["\'][^"\']*://[^"\']*["\']',
                ],
                'severity': 'HIGH',
                'risk_score': 80,
                'recommendation': 'Use environment variables for database connections'
            },
            'jwt_secret': {
                'patterns': [
                    r'["\']?jwt[_-]?secret["\']?\s*[:=]\s*["\'][^"\']{16,}["\']',
                    r'["\']?JWT[_-]?SECRET["\']?\s*[:=]\s*["\'][^"\']{16,}["\']',
                    r'["\']?token[_-]?secret["\']?\s*[:=]\s*["\'][^"\']{16,}["\']',
                ],
                'severity': 'CRITICAL',
                'risk_score': 90,
                'recommendation': 'Generate JWT secret at runtime or use secure vault'
            },
            'ip_address': {
                'patterns': [
                    r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                ],
                'severity': 'MEDIUM',
                'risk_score': 40,
                'recommendation': 'Consider using hostname or environment variable'
            },
            'hardcoded_port': {
                'patterns': [
                    r'["\']?port["\']?\s*[:=]\s*["\']?[0-9]{4,5}["\']?(?!\s*#.*localhost)',
                ],
                'severity': 'LOW',
                'risk_score': 20,
                'recommendation': 'Use environment variable for port configuration'
            }
        }
        
        # Whitelist patterns (safe to ignore)
        self.whitelist_patterns = [
            r'example\.com',
            r'localhost',
            r'127\.0\.0\.1',
            r'0\.0\.0\.0',
            r'your_.*_here',
            r'placeholder',
            r'dummy',
            r'test_.*_value',
            r'\.env\.example',
        ]
    
    def scan_file(self, file_path: Path) -> List[SecurityViolation]:
        """Scan a single file for security violations"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Skip empty lines and comments
                if not line_stripped or line_stripped.startswith('#'):
                    continue
                
                # Check each security pattern
                for violation_type, pattern_config in self.security_patterns.items():
                    for pattern in pattern_config['patterns']:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        
                        for match in matches:
                            # Check if this is in whitelist
                            if self._is_whitelisted(line):
                                continue
                            
                            # Get context (surrounding lines)
                            context = self._get_context(lines, line_num)
                            
                            violation = SecurityViolation(
                                file_path=str(file_path),
                                line_number=line_num,
                                violation_type=violation_type,
                                severity=pattern_config['severity'],
                                content=match.group(),
                                context=context,
                                recommendation=pattern_config['recommendation'],
                                risk_score=pattern_config['risk_score']
                            )
                            
                            violations.append(violation)
                            
        except Exception as e:
            print(f"Error scanning {file_path}: {e}")
        
        return violations
    
    def scan_directory(self, directory: Path, file_extensions: List[str] = None) -> List[SecurityViolation]:
        """Scan entire directory for security violations"""
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.ts', '.json', '.yaml', '.yml', '.env', '.cfg', '.conf']
        
        all_violations = []
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                # Check file extension
                if file_extensions and file_path.suffix not in file_extensions:
                    # Special case for env files without extension
                    if not (file_path.name.startswith('.env') or 'env' in file_path.name.lower()):
                        continue
                
                # Skip binary files and common ignore patterns
                if self._should_skip_file(file_path):
                    continue
                
                self.scan_stats['files_scanned'] += 1
                violations = self.scan_file(file_path)
                all_violations.extend(violations)
        
        self.violations.extend(all_violations)
        self._update_stats(all_violations)
        
        return all_violations
    
    def _is_whitelisted(self, line: str) -> bool:
        """Check if line matches whitelist patterns"""
        for pattern in self.whitelist_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return True
        return False
    
    def _get_context(self, lines: List[str], line_num: int, context_lines: int = 2) -> str:
        """Get context around the violation"""
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        
        context = []
        for i in range(start, end):
            prefix = ">>> " if i == line_num - 1 else "    "
            context.append(f"{prefix}{i+1:3d}: {lines[i].rstrip()}")
        
        return '\n'.join(context)
    
    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            '__pycache__',
            '.git',
            '.venv',
            'venv',
            'node_modules',
            '.pytest_cache',
            '.coverage',
            '.pyc',
            '.pyo',
            '.so',
            '.exe',
            '.dll',
            '.bin',
            'logs',
            '.log'
        ]
        
        for pattern in skip_patterns:
            if pattern in str(file_path):
                return True
        
        return False
    
    def _update_stats(self, violations: List[SecurityViolation]):
        """Update scan statistics"""
        self.scan_stats['violations_found'] += len(violations)
        
        for violation in violations:
            severity = violation.severity.lower()
            self.scan_stats[f'{severity}_violations'] += 1
    
    def generate_report(self, output_format: str = 'text') -> str:
        """Generate security report"""
        if output_format == 'json':
            return self._generate_json_report()
        else:
            return self._generate_text_report()
    
    def _generate_text_report(self) -> str:
        """Generate text format report"""
        report = []
        report.append("=" * 80)
        report.append("SECURITY SCAN REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Statistics
        report.append("SCAN STATISTICS:")
        report.append(f"Files Scanned: {self.scan_stats['files_scanned']}")
        report.append(f"Total Violations: {self.scan_stats['violations_found']}")
        report.append(f"  - Critical: {self.scan_stats['critical_violations']}")
        report.append(f"  - High: {self.scan_stats['high_violations']}")
        report.append(f"  - Medium: {self.scan_stats['medium_violations']}")
        report.append(f"  - Low: {self.scan_stats['low_violations']}")
        report.append("")
        
        # Overall status
        if self.scan_stats['critical_violations'] > 0:
            report.append("🚨 CRITICAL ISSUES FOUND - IMMEDIATE ACTION REQUIRED")
        elif self.scan_stats['high_violations'] > 0:
            report.append("⚠️  HIGH PRIORITY ISSUES FOUND - ACTION REQUIRED")
        elif self.scan_stats['violations_found'] > 0:
            report.append("📝 MEDIUM/LOW ISSUES FOUND - REVIEW RECOMMENDED")
        else:
            report.append("✅ NO SECURITY VIOLATIONS DETECTED")
        
        report.append("")
        
        # Detailed violations
        if self.violations:
            report.append("DETAILED VIOLATIONS:")
            report.append("-" * 50)
            
            # Group by severity
            severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
            for severity in severity_order:
                severity_violations = [v for v in self.violations if v.severity == severity]
                
                if severity_violations:
                    report.append(f"\n{severity} SEVERITY ({len(severity_violations)} issues):")
                    report.append("-" * 30)
                    
                    for violation in severity_violations:
                        report.append(f"\n📍 File: {violation.file_path}:{violation.line_number}")
                        report.append(f"   Type: {violation.violation_type}")
                        report.append(f"   Content: {violation.content}")
                        report.append(f"   Risk Score: {violation.risk_score}/100")
                        report.append(f"   Recommendation: {violation.recommendation}")
                        report.append(f"   Context:")
                        for line in violation.context.split('\n'):
                            report.append(f"     {line}")
        
        return '\n'.join(report)
    
    def _generate_json_report(self) -> str:
        """Generate JSON format report"""
        report_data = {
            'scan_timestamp': datetime.now().isoformat(),
            'statistics': self.scan_stats,
            'violations': []
        }
        
        for violation in self.violations:
            report_data['violations'].append({
                'file_path': violation.file_path,
                'line_number': violation.line_number,
                'violation_type': violation.violation_type,
                'severity': violation.severity,
                'content': violation.content,
                'context': violation.context,
                'recommendation': violation.recommendation,
                'risk_score': violation.risk_score
            })
        
        return json.dumps(report_data, indent=2)
    
    def save_report(self, filename: str, output_format: str = 'text'):
        """Save report to file"""
        report = self.generate_report(output_format)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"Report saved to: {filename}")
    
    def get_exit_code(self) -> int:
        """Get appropriate exit code based on violations"""
        if self.scan_stats['critical_violations'] > 0:
            return 2  # Critical issues
        elif self.scan_stats['high_violations'] > 0:
            return 1  # High priority issues
        else:
            return 0  # No critical/high issues

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Security Scanner for Credential Detection')
    parser.add_argument('--scan-all', action='store_true', help='Scan all files in current directory')
    parser.add_argument('--directory', '-d', type=str, help='Directory to scan')
    parser.add_argument('--file', '-f', type=str, help='Single file to scan')
    parser.add_argument('--output', '-o', type=str, help='Output file for report')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Report format')
    parser.add_argument('--exit-code', action='store_true', help='Exit with non-zero code if violations found')
    
    args = parser.parse_args()
    
    scanner = SecurityScanner()
    
    # Determine what to scan
    if args.file:
        # Scan single file
        file_path = Path(args.file)
        if file_path.exists():
            violations = scanner.scan_file(file_path)
            scanner.violations.extend(violations)
            scanner._update_stats(violations)
            scanner.scan_stats['files_scanned'] = 1
        else:
            print(f"File not found: {args.file}")
            sys.exit(1)
    else:
        # Scan directory
        directory = Path(args.directory) if args.directory else Path.cwd()
        if args.scan_all or args.directory:
            violations = scanner.scan_directory(directory)
        else:
            print("Please specify --scan-all, --directory, or --file")
            sys.exit(1)
    
    # Generate and display report
    report = scanner.generate_report(args.format)
    print(report)
    
    # Save report if requested
    if args.output:
        scanner.save_report(args.output, args.format)
    
    # Exit with appropriate code
    if args.exit_code:
        sys.exit(scanner.get_exit_code())

if __name__ == '__main__':
    main()