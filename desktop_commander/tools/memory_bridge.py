"""
Memory Bridge for Desktop Commander MCP Server.
Acts as a bridge to the external Memory MCP server, allowing Desktop Commander
to expose memory contents as its own resources.

This module enables communication with the Memory MCP server and provides
tools and resources to interact with the knowledge graph maintained by that server.
"""

import os
import sys
import json
import subprocess
from typing import Dict, List, Optional, Any, Tuple
import tempfile
import time

# Constants
MEMORY_SERVER_NAME = "memory"  # The name as configured in claude_desktop_config.json


class MemoryBridge:
    """Bridge to the Memory MCP server."""
    
    def __init__(self):
        self.cache = {}
        self.cache_expiry = {}
        self.cache_timeout = 60  # Cache timeout in seconds
    
    def _run_memory_command(self, command: str, args: List[str] = None) -> Tuple[bool, Any]:
        """
        Run a command against the Memory MCP server.
        
        Args:
            command: The command to run (read_graph, create_entities, etc.)
            args: List of arguments for the command
            
        Returns:
            Tuple of (success, result data)
        """
        try:
            # Create a temporary file to store the script
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.js', delete=False) as script_file:
                script_path = script_file.name
                
                # Write a simple script to call the memory server
                script_content = f"""
                const {{ Client }} = require('@modelcontextprotocol/sdk/client/index.js');
                const {{ StdioClientTransport }} = require('@modelcontextprotocol/sdk/client/stdio.js');

                async function main() {{
                    // Get configuration
                    const configPath = process.env.HOME + '/Library/Application Support/Claude/claude_desktop_config.json';
                    const config = require(configPath);
                    
                    // Get memory server config
                    if (!config.mcpServers || !config.mcpServers.{MEMORY_SERVER_NAME}) {{
                        console.error('Memory server not configured in claude_desktop_config.json');
                        process.exit(1);
                    }}
                    
                    const memoryConfig = config.mcpServers.{MEMORY_SERVER_NAME};
                    
                    // Create client
                    const client = new Client({{
                        name: 'desktop-commander-memory-bridge',
                        version: '1.0.0'
                    }});
                    
                    // Create transport
                    const transport = new StdioClientTransport({{
                        command: memoryConfig.command,
                        args: memoryConfig.args,
                        env: memoryConfig.env || {{}}
                    }});
                    
                    try {{
                        // Connect and initialize
                        await client.connect(transport);
                        
                        // Execute the specified command
                        let result;
                        switch ('{command}') {{
                            case 'read_graph':
                                result = await client.request({{
                                    method: 'read_graph',
                                    params: {{}}
                                }}, {{}});
                                break;
                            case 'search_nodes':
                                result = await client.request({{
                                    method: 'search_nodes',
                                    params: {{ query: '{args[0] if args else ""}' }}
                                }}, {{}});
                                break;
                            case 'open_nodes':
                                result = await client.request({{
                                    method: 'open_nodes',
                                    params: {{ names: {json.dumps(args) if args else []} }}
                                }}, {{}});
                                break;
                            // Add other commands as needed
                            default:
                                console.error(`Unknown command: {command}`);
                                process.exit(1);
                        }}
                        
                        // Output the result as JSON
                        console.log(JSON.stringify(result));
                        
                        // Close the client
                        await client.close();
                    }} catch (error) {{
                        console.error('Error:', error.message);
                        process.exit(1);
                    }}
                }}

                main().catch(error => {{
                    console.error('Unhandled error:', error);
                    process.exit(1);
                }});
                """
                
                script_file.write(script_content)
            
            # Execute the script with node
            cmd = ["node", script_path]
            result = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True)
            
            # Clean up the temporary file
            os.unlink(script_path)
            
            # Parse the result as JSON
            try:
                data = json.loads(result)
                return True, data
            except json.JSONDecodeError:
                return False, f"Invalid JSON response: {result}"
                
        except subprocess.CalledProcessError as e:
            return False, f"Command failed: {e.stderr}"
        except Exception as e:
            return False, f"Error executing memory command: {str(e)}"
    
    def read_graph(self) -> Optional[Dict[str, Any]]:
        """Read the complete knowledge graph from the Memory MCP server."""
        # Check cache first
        if "graph" in self.cache:
            import time
            if time.time() < self.cache_expiry.get("graph", 0):
                return self.cache["graph"]
        
        # Execute the command
        success, result = self._run_memory_command("read_graph")
        
        if success:
            # Cache the result
            import time
            self.cache["graph"] = result
            self.cache_expiry["graph"] = time.time() + self.cache_timeout
            return result
        else:
            print(f"Error reading memory graph: {result}", file=sys.stderr)
            return None
    
    def search_nodes(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """
        Search for nodes in the memory graph.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching nodes
        """
        # Cannot cache search results as query changes
        success, result = self._run_memory_command("search_nodes", [query])
        
        if success:
            return result.get("nodes", [])
        else:
            print(f"Error searching memory nodes: {result}", file=sys.stderr)
            return None
    
    def open_nodes(self, names: List[str]) -> Optional[Dict[str, Any]]:
        """
        Get specific nodes by name.
        
        Args:
            names: List of node names to retrieve
            
        Returns:
            Dictionary with entities and relations for the requested nodes
        """
        # Cache key based on sorted names
        cache_key = "open_" + "_".join(sorted(names))
        
        # Check cache first
        if cache_key in self.cache:
            import time
            if time.time() < self.cache_expiry.get(cache_key, 0):
                return self.cache[cache_key]
        
        # Execute the command
        success, result = self._run_memory_command("open_nodes", names)
        
        if success:
            # Cache the result
            import time
            self.cache[cache_key] = result
            self.cache_expiry[cache_key] = time.time() + self.cache_timeout
            return result
        else:
            print(f"Error opening memory nodes: {result}", file=sys.stderr)
            return None


# Global instance of the memory bridge
memory_bridge = MemoryBridge()


def register_tools(mcp):
    """Register memory bridge tools and resources with the MCP server."""
    
    # Register resources
    @mcp.resource("memory://graph")
    def memory_graph() -> str:
        """Get the complete knowledge graph from the Memory MCP server."""
        graph_data = memory_bridge.read_graph()
        
        if not graph_data:
            return "Error retrieving memory graph"
            
        return json.dumps(graph_data, indent=2)
    
    @mcp.resource("memory://search/{query}")
    def memory_search(query: str) -> str:
        """Search for nodes in the memory graph."""
        nodes = memory_bridge.search_nodes(query)
        
        if nodes is None:
            return f"Error searching memory for: {query}"
            
        if not nodes:
            return f"No results found for query: {query}"
            
        return json.dumps(nodes, indent=2)
    
    @mcp.resource("memory://entity/{entity_name}")
    def memory_entity(entity_name: str) -> str:
        """Get a specific entity from the memory graph."""
        result = memory_bridge.open_nodes([entity_name])
        
        if not result:
            return f"Error retrieving entity: {entity_name}"
            
        # Extract the entity from the result
        entities = result.get("entities", [])
        if not entities:
            return f"Entity not found: {entity_name}"
            
        # Get the first matching entity
        for entity in entities:
            if entity.get("name") == entity_name:
                return json.dumps(entity, indent=2)
                
        return f"Entity not found: {entity_name}"
    
    # Register tools
    @mcp.tool()
    def query_memory_graph() -> str:
        """
        Query the complete knowledge graph from the Memory MCP server.
        
        Returns:
            Complete knowledge graph as JSON
        """
        graph_data = memory_bridge.read_graph()
        
        if not graph_data:
            return "Error retrieving memory graph"
            
        return json.dumps(graph_data, indent=2)
    
    @mcp.tool()
    def search_memory_nodes(query: str) -> str:
        """
        Search for nodes in the memory graph.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching nodes as JSON
        """
        nodes = memory_bridge.search_nodes(query)
        
        if nodes is None:
            return f"Error searching memory for: {query}"
            
        return json.dumps(nodes, indent=2)
    
    @mcp.tool()
    def get_memory_entities(entity_names: str) -> str:
        """
        Get specific entities from the memory graph.
        
        Args:
            entity_names: Comma-separated list of entity names
            
        Returns:
            Entities and their relations as JSON
        """
        names = [name.strip() for name in entity_names.split(",")]
        result = memory_bridge.open_nodes(names)
        
        if not result:
            return f"Error retrieving entities: {entity_names}"
            
        return json.dumps(result, indent=2)
    
    @mcp.tool()
    def sync_memory_to_project_knowledge(project_name: str) -> str:
        """
        Sync memory graph to project knowledge graph.
        
        This tool extracts relevant information from the Memory MCP server
        and stores it in the project knowledge graph.
        
        Args:
            project_name: Name of the project to sync to
            
        Returns:
            Success or error message
        """
        try:
            # Import the knowledge_graph manager
            from desktop_commander.tools.knowledge_graph import graph_manager
            
            # Get the complete memory graph
            memory_data = memory_bridge.read_graph()
            
            if not memory_data:
                return "Error retrieving memory graph"
                
            # Extract entities and relations
            entities = memory_data.get("entities", [])
            relations = memory_data.get("relations", [])
            
            # Prepare the graph data
            graph_data = {
                "entities": entities,
                "relations": relations,
                "metadata": {
                    "synced_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "memory_mcp_server",
                    "entity_count": len(entities),
                    "relation_count": len(relations)
                }
            }
            
            # Save to the knowledge graph
            success = graph_manager.save_graph(project_name, graph_data)
            
            if success:
                return f"""Successfully synced memory graph to project: {project_name}
                
Synced {len(entities)} entities and {len(relations)} relations.
Memory graph is now available as:
- Complete graph: knowledge://{project_name}/graph
- Entities only: knowledge://{project_name}/entities
- Relations only: knowledge://{project_name}/relations
- Entity by name: knowledge://{project_name}/entity/{{entity_name}}
- Entities by type: knowledge://{project_name}/entity_type/{{entity_type}}"""
            else:
                return f"Failed to sync memory graph to project: {project_name}"
        except Exception as e:
            return f"Error syncing memory to project knowledge: {str(e)}"
