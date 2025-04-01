"""
JSON-structured memo tools for the Desktop Commander MCP Server.
Provides tools for updating specific sections of the JSON-structured project memos.

The JSON memo format follows a structured schema that includes:
- Project information and overview
- Current status with branch info and highlights
- Action items (todo, in progress, blocked, completed)
- Knowledge base with implementation details, configuration, environment
- Architecture decisions and terminology glossary
- File index for important project files
- Change log for tracking project changes
- Implementation plans with objectives, steps, and completion criteria

Available tools include:
- Task management: add_todo_item, mark_task_in_progress, mark_task_blocked, complete_task
- Knowledge management: add_knowledge_entry, add_architecture_decision, add_glossary_term
- Project planning: add_implementation_plan, update_plan_status
- Documentation: add_change_log_entry, index_project_file
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class JsonMemoTool:
    """Class for managing JSON-structured project memos."""
    
    def __init__(self):
        """Initialize the JSON memo tool."""
        pass
        
    def _load_memo(self, project_path: str) -> Dict[str, Any]:
        """Load the JSON memo for a project."""
        memo_path = os.path.join(project_path, "claude_memo.json")
        if not os.path.exists(memo_path):
            raise FileNotFoundError(f"No JSON memo found at {memo_path}. Use create_structured_project_memo first.")
            
        with open(memo_path, "r") as f:
            return json.load(f)
    
    def _save_memo(self, project_path: str, memo_data: Dict[str, Any]) -> str:
        """Save the JSON memo back to disk."""
        memo_path = os.path.join(project_path, "claude_memo.json")
        
        # Update metadata timestamp
        if "metaData" in memo_data:
            memo_data["metaData"]["lastUpdated"] = datetime.now().isoformat()
        
        with open(memo_path, "w") as f:
            json.dump(memo_data, f, indent=2)
            
        return memo_path
    
    def add_todo(self, project_path: str, task: str, priority: str = "Medium", category: str = None) -> str:
        """
        Add a new TODO item to the JSON memo.
        
        Args:
            project_path: Path to the project
            task: Description of the task
            priority: Priority level (High, Medium, Low)
            category: Optional category for the task
            
        Returns:
            Success message or error
        """
        try:
            memo_data = self._load_memo(project_path)
            
            # Validate priority
            if priority not in ["High", "Medium", "Low"]:
                priority = "Medium"
            
            # Create the new todo item
            todo_item = {
                "task": task,
                "priority": priority
            }
            
            if category:
                todo_item["category"] = category
                
            # Add to the todo list
            if "actionItems" not in memo_data:
                memo_data["actionItems"] = {}
            if "todo" not in memo_data["actionItems"]:
                memo_data["actionItems"]["todo"] = []
                
            memo_data["actionItems"]["todo"].append(todo_item)
            
            # Save the updated memo
            self._save_memo(project_path, memo_data)
            
            return f"Added TODO: {priority}: {task}"
        except Exception as e:
            return f"Error adding TODO: {str(e)}"
    
    def mark_todo_in_progress(self, project_path: str, task_pattern: str, assignee: str = None) -> str:
        """
        Move a todo item to the in-progress section.
        
        Args:
            project_path: Path to the project
            task_pattern: Text pattern to identify the task
            assignee: Optional person working on the task
            
        Returns:
            Success message or error
        """
        try:
            memo_data = self._load_memo(project_path)
            
            # Find the task in the todo list
            found = False
            todo_item = None
            
            if "actionItems" in memo_data and "todo" in memo_data["actionItems"]:
                todos = memo_data["actionItems"]["todo"]
                for i, item in enumerate(todos):
                    if task_pattern.lower() in item["task"].lower():
                        todo_item = item
                        memo_data["actionItems"]["todo"].pop(i)
                        found = True
                        break
            
            if not found:
                return f"No todo item found matching: {task_pattern}"
            
            # Create in-progress entry
            in_progress_item = {
                "task": todo_item["task"],
                "startDate": datetime.now().strftime("%Y-%m-%d")
            }
            
            if assignee:
                in_progress_item["assignee"] = assignee
            
            # Add to in-progress list
            if "inProgress" not in memo_data["actionItems"]:
                memo_data["actionItems"]["inProgress"] = []
                
            memo_data["actionItems"]["inProgress"].append(in_progress_item)
            
            # Save the updated memo
            self._save_memo(project_path, memo_data)
            
            return f"Moved task to In Progress: {todo_item['task']}"
        except Exception as e:
            return f"Error updating task status: {str(e)}"
    
    def mark_todo_blocked(self, project_path: str, task_pattern: str, reason: str, blocked_by: str = None) -> str:
        """
        Move a todo item to the blocked section.
        
        Args:
            project_path: Path to the project
            task_pattern: Text pattern to identify the task
            reason: Why the task is blocked
            blocked_by: Optional reference to blocking task or dependency
            
        Returns:
            Success message or error
        """
        try:
            memo_data = self._load_memo(project_path)
            
            # Find the task in the todo or in-progress list
            found = False
            task_item = None
            source_section = None
            
            # Check todo items
            if "actionItems" in memo_data and "todo" in memo_data["actionItems"]:
                todos = memo_data["actionItems"]["todo"]
                for i, item in enumerate(todos):
                    if task_pattern.lower() in item["task"].lower():
                        task_item = item
                        memo_data["actionItems"]["todo"].pop(i)
                        source_section = "todo"
                        found = True
                        break
            
            # Check in-progress items if not found in todo
            if not found and "actionItems" in memo_data and "inProgress" in memo_data["actionItems"]:
                in_progress = memo_data["actionItems"]["inProgress"]
                for i, item in enumerate(in_progress):
                    if task_pattern.lower() in item["task"].lower():
                        task_item = item
                        memo_data["actionItems"]["inProgress"].pop(i)
                        source_section = "inProgress"
                        found = True
                        break
            
            if not found:
                return f"No task found matching: {task_pattern}"
            
            # Create blocked entry
            blocked_item = {
                "task": task_item["task"],
                "reason": reason
            }
            
            if blocked_by:
                blocked_item["blockedBy"] = blocked_by
            
            # Add to blocked list
            if "blocked" not in memo_data["actionItems"]:
                memo_data["actionItems"]["blocked"] = []
                
            memo_data["actionItems"]["blocked"].append(blocked_item)
            
            # Save the updated memo
            self._save_memo(project_path, memo_data)
            
            return f"Moved task from {source_section} to Blocked: {task_item['task']} - Reason: {reason}"
        except Exception as e:
            return f"Error marking task as blocked: {str(e)}"
    
    def complete_todo(self, project_path: str, task_pattern: str) -> str:
        """
        Mark a task as completed and move it to the completed section.
        
        Args:
            project_path: Path to the project
            task_pattern: Text pattern to identify the task
            
        Returns:
            Success message or error
        """
        try:
            memo_data = self._load_memo(project_path)
            
            # Find the task in any of the task lists
            found = False
            task_item = None
            source_section = None
            
            sections = ["todo", "inProgress", "blocked"]
            for section in sections:
                if "actionItems" in memo_data and section in memo_data["actionItems"]:
                    items = memo_data["actionItems"][section]
                    for i, item in enumerate(items):
                        if task_pattern.lower() in item["task"].lower():
                            task_item = item
                            memo_data["actionItems"][section].pop(i)
                            source_section = section
                            found = True
                            break
                if found:
                    break
            
            if not found:
                return f"No task found matching: {task_pattern}"
            
            # Create completed entry
            completed_item = {
                "task": task_item["task"],
                "completionDate": datetime.now().strftime("%Y-%m-%d")
            }
            
            # Add to completed list
            if "completed" not in memo_data["actionItems"]:
                memo_data["actionItems"]["completed"] = []
                
            memo_data["actionItems"]["completed"].append(completed_item)
            
            # Add to change log
            self._add_to_change_log(memo_data, f"Completed task: {task_item['task']}")
            
            # Save the updated memo
            self._save_memo(project_path, memo_data)
            
            return f"Completed task: {task_item['task']}"
        except Exception as e:
            return f"Error completing task: {str(e)}"
    
    def add_knowledge_item(self, project_path: str, section: str, content: str) -> str:
        """
        Add a knowledge item to a specific section of the knowledgeBase.
        
        Args:
            project_path: Path to the project
            section: Section to add to (implementation, configuration, environment)
            content: The knowledge content to add
            
        Returns:
            Success message or error
        """
        try:
            memo_data = self._load_memo(project_path)
            
            # Validate section
            valid_sections = ["implementation", "configuration", "environment"]
            if section.lower() not in valid_sections:
                return f"Invalid knowledge section: {section}. Must be one of: {', '.join(valid_sections)}"
            
            section = section.lower()
            
            # Initialize knowledgeBase if needed
            if "knowledgeBase" not in memo_data:
                memo_data["knowledgeBase"] = {}
            
            if section not in memo_data["knowledgeBase"]:
                memo_data["knowledgeBase"][section] = []
                
            # Add the content
            memo_data["knowledgeBase"][section].append(content)
            
            # Save the updated memo
            self._save_memo(project_path, memo_data)
            
            return f"Added knowledge to {section}: {content[:50]}..."
        except Exception as e:
            return f"Error adding knowledge item: {str(e)}"
    
    def add_architecture_decision(self, project_path: str, title: str, description: str, 
                                  alternatives: List[str] = None) -> str:
        """
        Add an architecture decision record.
        
        Args:
            project_path: Path to the project
            title: Title of the decision
            description: Detailed description
            alternatives: Optional list of alternatives considered
            
        Returns:
            Success message or error
        """
        try:
            memo_data = self._load_memo(project_path)
            
            # Initialize knowledgeBase if needed
            if "knowledgeBase" not in memo_data:
                memo_data["knowledgeBase"] = {}
            
            if "architectureDecisions" not in memo_data["knowledgeBase"]:
                memo_data["knowledgeBase"]["architectureDecisions"] = []
                
            # Create decision record
            decision = {
                "title": title,
                "description": description,
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            
            if alternatives:
                decision["alternatives"] = alternatives
                
            # Add the decision
            memo_data["knowledgeBase"]["architectureDecisions"].append(decision)
            
            # Add to change log
            self._add_to_change_log(memo_data, f"Added architecture decision: {title}")
            
            # Save the updated memo
            self._save_memo(project_path, memo_data)
            
            return f"Added architecture decision: {title}"
        except Exception as e:
            return f"Error adding architecture decision: {str(e)}"
    
    def add_term_to_glossary(self, project_path: str, term: str, definition: str) -> str:
        """
        Add a term to the project terminology glossary.
        
        Args:
            project_path: Path to the project
            term: The term to define
            definition: The definition of the term
            
        Returns:
            Success message or error
        """
        try:
            memo_data = self._load_memo(project_path)
            
            # Initialize knowledgeBase if needed
            if "knowledgeBase" not in memo_data:
                memo_data["knowledgeBase"] = {}
            
            if "terminology" not in memo_data["knowledgeBase"]:
                memo_data["knowledgeBase"]["terminology"] = {}
                
            # Add the term
            memo_data["knowledgeBase"]["terminology"][term] = definition
            
            # Save the updated memo
            self._save_memo(project_path, memo_data)
            
            return f"Added term to glossary: {term}"
        except Exception as e:
            return f"Error adding term to glossary: {str(e)}"
    
    def add_implementation_plan(self, project_path: str, plan_name: str, objective: str, 
                               steps: List[str], testing: List[str] = None, 
                               completion_criteria: List[str] = None) -> str:
        """
        Add an implementation plan to the memo.
        
        Args:
            project_path: Path to the project
            plan_name: Name/identifier for the plan
            objective: Main objective of the plan
            steps: List of implementation steps
            testing: Optional list of testing steps
            completion_criteria: Optional list of completion criteria
            
        Returns:
            Success message or error
        """
        try:
            memo_data = self._load_memo(project_path)
            
            # Initialize implementationPlans if needed
            if "implementationPlans" not in memo_data:
                memo_data["implementationPlans"] = {}
                
            # Create plan record
            plan = {
                "objective": objective,
                "steps": steps,
                "status": "Not Started"
            }
            
            if testing:
                plan["testing"] = testing
                
            if completion_criteria:
                plan["completionCriteria"] = completion_criteria
                
            # Add the plan
            memo_data["implementationPlans"][plan_name] = plan
            
            # Add to change log
            self._add_to_change_log(memo_data, f"Added implementation plan: {plan_name}")
            
            # Save the updated memo
            self._save_memo(project_path, memo_data)
            
            return f"Added implementation plan: {plan_name}"
        except Exception as e:
            return f"Error adding implementation plan: {str(e)}"
    
    def update_implementation_plan_status(self, project_path: str, plan_name: str, status: str) -> str:
        """
        Update the status of an implementation plan.
        
        Args:
            project_path: Path to the project
            plan_name: Name/identifier of the plan
            status: New status (Not Started, In Progress, Completed, Blocked)
            
        Returns:
            Success message or error
        """
        try:
            memo_data = self._load_memo(project_path)
            
            # Validate status
            valid_statuses = ["Not Started", "In Progress", "Completed", "Blocked"]
            if status not in valid_statuses:
                return f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}"
            
            # Check if plan exists
            if "implementationPlans" not in memo_data or plan_name not in memo_data["implementationPlans"]:
                return f"Implementation plan not found: {plan_name}"
                
            # Update status
            old_status = memo_data["implementationPlans"][plan_name]["status"]
            memo_data["implementationPlans"][plan_name]["status"] = status
            
            # Add to change log if status changed
            if old_status != status:
                self._add_to_change_log(memo_data, f"Updated plan status: {plan_name} from {old_status} to {status}")
            
            # Save the updated memo
            self._save_memo(project_path, memo_data)
            
            return f"Updated status of plan {plan_name} to {status}"
        except Exception as e:
            return f"Error updating plan status: {str(e)}"
    
    def add_change_log_entry(self, project_path: str, change: str, version: str = None) -> str:
        """
        Add an entry to the change log.
        
        Args:
            project_path: Path to the project
            change: Description of the change
            version: Optional version number or identifier
            
        Returns:
            Success message or error
        """
        try:
            memo_data = self._load_memo(project_path)
            
            # Add the change
            self._add_to_change_log(memo_data, change, version)
            
            # Save the updated memo
            self._save_memo(project_path, memo_data)
            
            return f"Added change log entry: {change}"
        except Exception as e:
            return f"Error adding change log entry: {str(e)}"
    
    def _add_to_change_log(self, memo_data: Dict[str, Any], change: str, version: str = None) -> None:
        """
        Helper function to add a change to the change log.
        
        Args:
            memo_data: The memo data dictionary
            change: The change description
            version: Optional version
        """
        # Initialize changeLog if needed
        if "changeLog" not in memo_data:
            memo_data["changeLog"] = []
            
        # Use today's date if no version provided
        today = datetime.now().strftime("%Y-%m-%d")
        version = version or today
        
        # Check if there's an entry for this version
        entry = None
        for log_entry in memo_data["changeLog"]:
            if log_entry.get("date") == today or log_entry.get("version") == version:
                entry = log_entry
                break
                
        if entry:
            # Add to existing entry
            if "changes" not in entry:
                entry["changes"] = []
            entry["changes"].append(change)
        else:
            # Create new entry
            new_entry = {
                "date": today,
                "changes": [change]
            }
            
            if version and version != today:
                new_entry["version"] = version
                
            memo_data["changeLog"].append(new_entry)
    
    def index_file(self, project_path: str, file_path: str, description: str, category: str = None) -> str:
        """
        Add or update a file in the file index.
        
        Args:
            project_path: Path to the project
            file_path: Path to the file (relative to project root)
            description: Description of the file's purpose
            category: Optional file category
            
        Returns:
            Success message or error
        """
        try:
            memo_data = self._load_memo(project_path)
            
            # Resolve path to verify file exists
            absolute_path = file_path
            if not os.path.isabs(file_path):
                absolute_path = os.path.join(project_path, file_path)
                
            if not os.path.exists(absolute_path):
                return f"File not found: {file_path}"
                
            # Generate a unique key for the file
            key = file_path.replace("/", "_").replace(".", "_")
            
            # Create file index entry
            entry = {
                "path": file_path,
                "description": description,
                "lastModified": datetime.now().isoformat()
            }
            
            if category:
                entry["category"] = category
                
            # Initialize fileIndex if needed
            if "fileIndex" not in memo_data:
                memo_data["fileIndex"] = {}
                
            # Add/update the file entry
            memo_data["fileIndex"][key] = entry
            
            # Save the updated memo
            self._save_memo(project_path, memo_data)
            
            return f"Indexed file: {file_path}"
        except Exception as e:
            return f"Error indexing file: {str(e)}"
    
    def get_todos(self, project_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all task items from the JSON memo.
        
        Args:
            project_path: Path to the project
            
        Returns:
            Dictionary with task lists by status
        """
        try:
            memo_data = self._load_memo(project_path)
            
            if "actionItems" not in memo_data:
                return {
                    "todo": [],
                    "inProgress": [],
                    "blocked": [],
                    "completed": []
                }
            
            # Extract task lists with defaults for missing sections
            result = {}
            for section in ["todo", "inProgress", "blocked", "completed"]:
                result[section] = memo_data["actionItems"].get(section, [])
                
            return result
        except Exception as e:
            logger.error(f"Error getting todos: {str(e)}")
            return {
                "todo": [],
                "inProgress": [],
                "blocked": [],
                "completed": []
            }

def get_memo_tools_guide() -> str:
    """
    Get a documentation guide for the JSON memo tools.
    """
    guide = """## JSON Memo Tools Guide

### Task Management
- `add_todo_item(task, priority, category)`: Add a new task with optional priority and category
- `mark_task_in_progress(task_pattern, assignee)`: Move a task to in-progress status with optional assignee
- `mark_task_blocked(task_pattern, reason, blocked_by)`: Mark a task as blocked with reason
- `complete_task(task_pattern)`: Mark a task as completed
- `list_project_tasks()`: Get a formatted list of all tasks by status

### Knowledge Management
- `add_knowledge_entry(section, content)`: Add content to implementation, configuration, or environment sections
- `add_architecture_decision(title, description, alternatives)`: Document architectural decisions
- `add_glossary_term(term, definition)`: Add a term to the project glossary

### Project Planning
- `add_implementation_plan(plan_name, objective, steps, testing, completion_criteria)`: Create a detailed plan
- `update_plan_status(plan_name, status)`: Update a plan's status (Not Started, In Progress, Completed, Blocked)

### Documentation
- `add_change_log_entry(change, version)`: Record a change with optional version
- `index_project_file(file_path, description, category)`: Document an important project file

### Best Practices
- Add TODOs with clear descriptions and appropriate priorities
- Document important decisions with rationale
- Update task status as work progresses
- Record changes and contributions through the change log
- Use the glossary to maintain consistent terminology
- Index key files to help with codebase navigation
"""
    return guide


def register_tools(mcp):
    """Register JSON memo tools with the MCP server."""
    
    # Create a single instance of the tool
    memo_tool = JsonMemoTool()
    
    @mcp.tool()
    def add_todo_item(task: str, priority: str = "Medium", category: str = None) -> str:
        """
        Add a new TODO item to the structured JSON memo.
        
        Args:
            task: Description of the task
            priority: Priority level (High, Medium, Low)
            category: Optional category for the task
        """
        from desktop_commander.tools.project import current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        return memo_tool.add_todo(current_project["path"], task, priority, category)
    
    @mcp.tool()
    def mark_task_in_progress(task_pattern: str, assignee: str = None) -> str:
        """
        Move a todo item to the in-progress section.
        
        Args:
            task_pattern: Text pattern to identify the task
            assignee: Optional person working on the task
        """
        from desktop_commander.tools.project import current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        return memo_tool.mark_todo_in_progress(current_project["path"], task_pattern, assignee)
    
    @mcp.tool()
    def mark_task_blocked(task_pattern: str, reason: str, blocked_by: str = None) -> str:
        """
        Move a task to the blocked section.
        
        Args:
            task_pattern: Text pattern to identify the task
            reason: Why the task is blocked
            blocked_by: Optional reference to blocking task or dependency
        """
        from desktop_commander.tools.project import current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        return memo_tool.mark_todo_blocked(current_project["path"], task_pattern, reason, blocked_by)
    
    @mcp.tool()
    def complete_task(task_pattern: str) -> str:
        """
        Mark a task as completed and move it to the completed section.
        
        Args:
            task_pattern: Text pattern to identify the task
        """
        from desktop_commander.tools.project import current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        return memo_tool.complete_todo(current_project["path"], task_pattern)
    
    @mcp.tool()
    def list_project_tasks() -> str:
        """
        Get a formatted list of all project tasks.
        """
        from desktop_commander.tools.project import current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        try:
            tasks = memo_tool.get_todos(current_project["path"])
            
            # Format the result as a readable string
            result = ["# Project Tasks"]
            
            # Format todo items
            result.append("\n## Todo")
            if not tasks["todo"]:
                result.append("No todo items")
            else:
                for item in tasks["todo"]:
                    priority = item.get("priority", "Medium")
                    category = f" ({item.get('category')})" if "category" in item else ""
                    result.append(f"- [{priority}] {item['task']}{category}")
            
            # Format in progress items
            result.append("\n## In Progress")
            if not tasks["inProgress"]:
                result.append("No in-progress items")
            else:
                for item in tasks["inProgress"]:
                    assignee = f" (Assignee: {item.get('assignee')})" if "assignee" in item else ""
                    start_date = f" (Started: {item.get('startDate', '')})" if "startDate" in item else ""
                    result.append(f"- {item['task']}{assignee}{start_date}")
            
            # Format blocked items
            result.append("\n## Blocked")
            if not tasks["blocked"]:
                result.append("No blocked items")
            else:
                for item in tasks["blocked"]:
                    reason = f"\n  - Reason: {item.get('reason', 'Unknown')}"
                    blocked_by = f"\n  - Blocked by: {item.get('blockedBy')}" if "blockedBy" in item else ""
                    result.append(f"- {item['task']}{reason}{blocked_by}")
            
            # Format completed items (limit to 5)
            result.append("\n## Recently Completed")
            if not tasks["completed"]:
                result.append("No completed items")
            else:
                for item in tasks["completed"][-5:]:  # Show only the 5 most recent
                    date = f" (Completed: {item.get('completionDate', '')})" if "completionDate" in item else ""
                    result.append(f"- ✓ {item['task']}{date}")
            
            return "\n".join(result)
        except Exception as e:
            return f"Error listing tasks: {str(e)}"
    
    @mcp.tool()
    def add_knowledge_entry(section: str, content: str) -> str:
        """
        Add a knowledge item to a specific section of the knowledgeBase.
        
        Args:
            section: Section to add to (implementation, configuration, environment)
            content: The knowledge content to add
        """
        from desktop_commander.tools.project import current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        return memo_tool.add_knowledge_item(current_project["path"], section, content)
    
    @mcp.tool()
    def add_architecture_decision(title: str, description: str, alternatives: List[str] = None) -> str:
        """
        Add an architecture decision record to the memo.
        
        Args:
            title: Title of the decision
            description: Detailed description
            alternatives: Optional list of alternatives considered
        """
        from desktop_commander.tools.project import current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        return memo_tool.add_architecture_decision(
            current_project["path"], title, description, alternatives
        )
    
    @mcp.tool()
    def add_glossary_term(term: str, definition: str) -> str:
        """
        Add a term to the project terminology glossary.
        
        Args:
            term: The term to define
            definition: The definition of the term
        """
        from desktop_commander.tools.project import current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        return memo_tool.add_term_to_glossary(current_project["path"], term, definition)
    
    @mcp.tool()
    def add_implementation_plan(plan_name: str, objective: str, steps: List[str], 
                              testing: List[str] = None, completion_criteria: List[str] = None) -> str:
        """
        Add an implementation plan to the memo.
        
        Args:
            plan_name: Name/identifier for the plan
            objective: Main objective of the plan
            steps: List of implementation steps
            testing: Optional list of testing steps
            completion_criteria: Optional list of completion criteria
        """
        from desktop_commander.tools.project import current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        return memo_tool.add_implementation_plan(
            current_project["path"], plan_name, objective, steps, 
            testing, completion_criteria
        )
    
    @mcp.tool()
    def update_plan_status(plan_name: str, status: str) -> str:
        """
        Update the status of an implementation plan.
        
        Args:
            plan_name: Name/identifier of the plan
            status: New status (Not Started, In Progress, Completed, Blocked)
        """
        from desktop_commander.tools.project import current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        return memo_tool.update_implementation_plan_status(
            current_project["path"], plan_name, status
        )
    
    @mcp.tool()
    def add_change_log_entry(change: str, version: str = None) -> str:
        """
        Add an entry to the change log.
        
        Args:
            change: Description of the change
            version: Optional version number or identifier
        """
        from desktop_commander.tools.project import current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        return memo_tool.add_change_log_entry(current_project["path"], change, version)
    
    @mcp.tool()
    def index_project_file(file_path: str, description: str, category: str = None) -> str:
        """
        Add or update a file in the file index.
        
        Args:
            file_path: Path to the file (relative to project root)
            description: Description of the file's purpose
            category: Optional file category
        """
        from desktop_commander.tools.project import current_project
        if not current_project["path"]:
            return "No active project. Use discover_projects and use_project to select a project."
            
        return memo_tool.index_file(current_project["path"], file_path, description, category)
        
    @mcp.tool()
    def get_memo_tools_documentation() -> str:
        """
        Get comprehensive documentation about available JSON memo tools
        and best practices for using them.
        """
        return get_memo_tools_guide()