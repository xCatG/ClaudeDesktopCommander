"""
Knowledge graph integration for Desktop Commander MCP Server.
Provides tools to expose project knowledge graphs as resources.

This module integrates with the memory tool to expose structured project knowledge
as queryable resources through the MCP protocol.
"""

import os
import sys
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class KnowledgeGraph:
    """Knowledge graph manager for storing and retrieving project information."""
    
    def __init__(self):
        self.entities = {}
        self.relations = []
        self.storage_dir = self._get_storage_dir()
        
    def _get_storage_dir(self) -> str:
        """Get the storage directory for knowledge graph files."""
        # Store in the user's home directory under .desktop_commander
        home_dir = os.path.expanduser("~")
        storage_dir = os.path.join(home_dir, ".desktop_commander", "knowledge")
        
        # Create directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        return storage_dir
    
    def get_graph_path(self, project_name: str) -> str:
        """Get the file path for a project's knowledge graph."""
        safe_name = project_name.replace("/", "_").replace("\\", "_")
        return os.path.join(self.storage_dir, f"{safe_name}_graph.json")
    
    def save_graph(self, project_name: str, graph_data: Dict[str, Any]) -> bool:
        """Save knowledge graph data for a project."""
        try:
            file_path = self.get_graph_path(project_name)
            
            with open(file_path, "w") as f:
                json.dump(graph_data, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving knowledge graph: {str(e)}", file=sys.stderr)
            return False
    
    def load_graph(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Load knowledge graph data for a project."""
        try:
            file_path = self.get_graph_path(project_name)
            
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading knowledge graph: {str(e)}", file=sys.stderr)
            return None
    
    def list_graphs(self) -> List[str]:
        """List all available knowledge graphs."""
        try:
            graphs = []
            for file in os.listdir(self.storage_dir):
                if file.endswith("_graph.json"):
                    graphs.append(file.replace("_graph.json", ""))
            return graphs
        except Exception as e:
            print(f"Error listing knowledge graphs: {str(e)}", file=sys.stderr)
            return []


# Global instance of the knowledge graph manager
graph_manager = KnowledgeGraph()


def register_tools(mcp):
    """Register knowledge graph tools with the MCP server."""
    
    # First, register resources
    @mcp.resource("knowledge://{project_name}/graph")
    def project_knowledge_graph(project_name: str) -> str:
        """Get the complete knowledge graph for a project."""
        graph_data = graph_manager.load_graph(project_name)
        
        if not graph_data:
            return f"No knowledge graph found for project: {project_name}"
            
        return json.dumps(graph_data, indent=2)
    
    @mcp.resource("knowledge://{project_name}/entities")
    def project_entities(project_name: str) -> str:
        """Get all entities in a project's knowledge graph."""
        graph_data = graph_manager.load_graph(project_name)
        
        if not graph_data or "entities" not in graph_data:
            return f"No entities found for project: {project_name}"
            
        return json.dumps(graph_data["entities"], indent=2)
    
    @mcp.resource("knowledge://{project_name}/relations")
    def project_relations(project_name: str) -> str:
        """Get all relations in a project's knowledge graph."""
        graph_data = graph_manager.load_graph(project_name)
        
        if not graph_data or "relations" not in graph_data:
            return f"No relations found for project: {project_name}"
            
        return json.dumps(graph_data["relations"], indent=2)
    
    @mcp.resource("knowledge://{project_name}/entity/{entity_name}")
    def project_entity(project_name: str, entity_name: str) -> str:
        """Get a specific entity from a project's knowledge graph."""
        graph_data = graph_manager.load_graph(project_name)
        
        if not graph_data or "entities" not in graph_data:
            return f"No entities found for project: {project_name}"
            
        for entity in graph_data["entities"]:
            if entity.get("name") == entity_name:
                return json.dumps(entity, indent=2)
                
        return f"Entity '{entity_name}' not found in project: {project_name}"
    
    @mcp.resource("knowledge://{project_name}/entity_type/{entity_type}")
    def project_entities_by_type(project_name: str, entity_type: str) -> str:
        """Get all entities of a specific type from a project's knowledge graph."""
        graph_data = graph_manager.load_graph(project_name)
        
        if not graph_data or "entities" not in graph_data:
            return f"No entities found for project: {project_name}"
            
        entities = [entity for entity in graph_data["entities"] 
                    if entity.get("entityType") == entity_type]
        
        if not entities:
            return f"No entities of type '{entity_type}' found in project: {project_name}"
            
        return json.dumps(entities, indent=2)
    
    # Now register tools for managing knowledge graphs
    @mcp.tool()
    def save_project_knowledge(project_name: str, graph_data: str) -> str:
        """
        Save knowledge graph data for a project.
        
        Args:
            project_name: Name of the project
            graph_data: JSON string containing the knowledge graph data
            
        Returns:
            Success or error message
        """
        try:
            # Parse the graph data from JSON
            data = json.loads(graph_data)
            
            # Save to the knowledge graph manager
            success = graph_manager.save_graph(project_name, data)
            
            if success:
                return f"Successfully saved knowledge graph for project: {project_name}"
            else:
                return f"Failed to save knowledge graph for project: {project_name}"
        except json.JSONDecodeError:
            return "Invalid JSON data provided for knowledge graph"
        except Exception as e:
            return f"Error saving project knowledge: {str(e)}"
    
    @mcp.tool()
    def list_knowledge_graphs() -> str:
        """
        List all available project knowledge graphs.
        
        Returns:
            List of projects with knowledge graphs
        """
        try:
            graphs = graph_manager.list_graphs()
            
            if not graphs:
                return "No knowledge graphs found"
                
            return "Available knowledge graphs:\n" + "\n".join(graphs)
        except Exception as e:
            return f"Error listing knowledge graphs: {str(e)}"
    
    @mcp.tool()
    def get_project_knowledge(project_name: str) -> str:
        """
        Get knowledge graph data for a project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Knowledge graph data as JSON string
        """
        try:
            graph_data = graph_manager.load_graph(project_name)
            
            if not graph_data:
                return f"No knowledge graph found for project: {project_name}"
                
            return json.dumps(graph_data, indent=2)
        except Exception as e:
            return f"Error getting project knowledge: {str(e)}"
