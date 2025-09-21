# Consul Configuration for AI Trading Platform
# Service Discovery and Configuration Management

datacenter = "aitrading-dc1"
data_dir = "/consul/data"
log_level = "INFO"
node_name = "aitrading-consul-server"
bind_addr = "0.0.0.0"
client_addr = "0.0.0.0"

# Server configuration
server = true
bootstrap_expect = 1
ui_config {
  enabled = true
}

# Performance
performance {
  raft_multiplier = 1
}

# Connect (Service Mesh)
connect {
  enabled = true
}

# Services auto-registration
services {
  id = "consul"
  name = "consul"
  tags = ["infrastructure", "service-discovery"]
  port = 8500
  check {
    http = "http://localhost:8500/v1/status/leader"
    interval = "10s"
  }
}

# ACL system (disabled for development)
acl = {
  enabled = false
  default_policy = "allow"
  enable_token_persistence = true
}

# Logging
log_json = true
enable_syslog = false

# Telemetry
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
}