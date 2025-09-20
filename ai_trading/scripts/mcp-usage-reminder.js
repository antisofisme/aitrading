#!/usr/bin/env node
/**
 * MCP Usage Reminder System
 * Displays available MCP tools for common operations
 */

const availableMCPTools = {
    docker: {
        description: "Docker container operations",
        tools: [
            "mcp__mcp-server-docker__list_containers",
            "mcp__mcp-server-docker__start_container", 
            "mcp__mcp-server-docker__stop_container",
            "mcp__mcp-server-docker__fetch_container_logs",
            "mcp__mcp-server-docker__build_image",
            "mcp__mcp-server-docker__run_container"
        ],
        bashEquivalents: [
            "docker ps → list_containers",
            "docker start → start_container",
            "docker stop → stop_container", 
            "docker logs → fetch_container_logs",
            "docker build → build_image",
            "docker run → run_container"
        ]
    },
    filesystem: {
        description: "File system operations",
        tools: [
            "mcp__filesystem__read_file",
            "mcp__filesystem__write_file",
            "mcp__filesystem__list_directory",
            "mcp__filesystem__search_files",
            "mcp__filesystem__create_directory",
            "mcp__filesystem__move_file"
        ],
        bashEquivalents: [
            "cat file.txt → read_file",
            "touch/echo → write_file",
            "ls /path/ → list_directory",
            "find . -name → search_files",
            "mkdir → create_directory",
            "mv file1 file2 → move_file"
        ]
    },
    github: {
        description: "GitHub repository operations",
        tools: [
            "mcp__github__search_repositories",
            "mcp__github__list_pull_requests",
            "mcp__github__create_issue",
            "mcp__github__get_file_contents",
            "mcp__github__create_pull_request"
        ],
        bashEquivalents: [
            "gh repo list → search_repositories",
            "gh pr list → list_pull_requests",
            "gh issue create → create_issue",
            "gh repo view → get_file_contents",
            "gh pr create → create_pull_request"
        ]
    },
    api_testing: {
        description: "API endpoint testing",
        tools: [
            "dkmaker-mcp-rest-api (HTTP/REST)",
            "websocket-mcp-server (WebSocket)"
        ],
        bashEquivalents: [
            "curl http://api.com/test → MCP REST server",
            "wscat ws://api.com/ws → WebSocket MCP server"
        ]
    }
};

function displayMCPReminder(category = null) {
    console.log('🎯 MCP TOOLS USAGE REMINDER\n');
    console.log('⚠️  CRITICAL: Always check MCP tools before using Bash!\n');
    
    if (category && availableMCPTools[category]) {
        // Show specific category
        const cat = availableMCPTools[category];
        console.log(`📋 ${category.toUpperCase()} - ${cat.description}:`);
        console.log('\nAvailable MCP Tools:');
        cat.tools.forEach(tool => console.log(`   ✅ ${tool}`));
        console.log('\nBash → MCP Equivalents:');
        cat.bashEquivalents.forEach(equiv => console.log(`   🔄 ${equiv}`));
    } else {
        // Show all categories
        Object.keys(availableMCPTools).forEach(key => {
            const cat = availableMCPTools[key];
            console.log(`📋 ${key.toUpperCase()} - ${cat.description}:`);
            console.log(`   Tools: ${cat.tools.length} available`);
            console.log(`   Example: ${cat.bashEquivalents[0]}\n`);
        });
        
        console.log('💡 Usage: node mcp-usage-reminder.js [category]');
        console.log('   Categories: docker, filesystem, github, api_testing');
    }
    
    console.log('\n🎯 Remember: MCP tools provide better error handling and integration!');
}

// Handle command line arguments
const category = process.argv[2];
displayMCPReminder(category);

module.exports = { availableMCPTools, displayMCPReminder };