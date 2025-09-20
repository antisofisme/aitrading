# 🎯 MCP TOOLS REFERENCE CARD
*Always visible reminder for Claude Code and developers*

## **🚨 CRITICAL RULE: MCP-FIRST DEVELOPMENT**

**BEFORE using any bash command, CHECK if MCP tool exists!**

---

## **📋 AVAILABLE MCP TOOLS:**

### **🐳 Docker Operations**
```bash
# ❌ WRONG (Bash)          # ✅ CORRECT (MCP)
docker ps                  → mcp__mcp-server-docker__list_containers
docker start container     → mcp__mcp-server-docker__start_container  
docker stop container      → mcp__mcp-server-docker__stop_container
docker logs container      → mcp__mcp-server-docker__fetch_container_logs
docker build -t tag .      → mcp__mcp-server-docker__build_image
docker run image           → mcp__mcp-server-docker__run_container
```

### **📁 File System Operations**
```bash
# ❌ WRONG (Bash)          # ✅ CORRECT (MCP)
cat file.txt               → mcp__filesystem__read_file
ls /path/                  → mcp__filesystem__list_directory
find . -name "*.py"        → mcp__filesystem__search_files
mkdir /path/dir            → mcp__filesystem__create_directory
mv file1 file2             → mcp__filesystem__move_file
```

### **🌐 GitHub Operations**
```bash
# ❌ WRONG (Bash)          # ✅ CORRECT (MCP)
gh repo list               → mcp__github__search_repositories
gh pr list                 → mcp__github__list_pull_requests
gh issue create           → mcp__github__create_issue
git clone repo             → mcp__github__fork_repository
```

### **🧪 API Testing**
```bash
# ❌ WRONG (Bash)          # ✅ CORRECT (MCP)
curl http://api.com/test   → Use dkmaker-mcp-rest-api MCP server
wget http://api.com/data   → Use dkmaker-mcp-rest-api MCP server
```

### **🌐 WebSocket Testing**
```bash
# ❌ WRONG (Manual)        # ✅ CORRECT (MCP)
websocket manual test      → Use custom WebSocket MCP server
wscat ws://url             → Use websocket_test_neliti tool
```

---

## **🔧 HOW TO CHECK AVAILABLE MCP TOOLS:**

1. **List available MCP tools:**
   ```bash
   ListMcpResourcesTool
   ```

2. **Check specific MCP server:**
   ```bash
   ReadMcpResourceTool --server mcp-server-name --uri tool-uri
   ```

---

## **⚡ QUICK DECISION FLOWCHART:**

```
Need to do something? 
    ↓
Is there an MCP tool for this?
    ↓
YES → Use MCP tool (Always preferred)
NO  → Use Bash (Only as fallback)
    ↓
Document why no MCP tool exists
```

---

## **📈 MCP ADOPTION BENEFITS:**

- ✅ **Consistency**: Standardized operations across all tasks
- ✅ **Error Handling**: Better error messages and validation
- ✅ **Logging**: Comprehensive operation logging
- ✅ **Performance**: Optimized operations vs raw bash
- ✅ **Integration**: Works seamlessly with Claude Code
- ✅ **Maintenance**: Centralized tool management

---

## **🎯 ENFORCEMENT RULES:**

### **For Claude Code (AI Assistant):**
- ✅ Always check MCP tools first before using Bash
- ✅ Explain why using MCP tool vs bash command
- ✅ Show MCP tool usage in examples
- ❌ Never use Bash when MCP tool exists

### **For Developers:**
- ✅ Install and configure available MCP tools
- ✅ Add new MCP tools when patterns emerge
- ✅ Update this reference when tools change
- ✅ Use MCP tools in automation scripts

---

**Remember: MCP tools provide better integration, error handling, and consistency than raw bash commands!**