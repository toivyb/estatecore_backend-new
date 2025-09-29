#!/usr/bin/env python3
"""
Project Management & Task Tracking System for EstateCore Phase 8B
Kanban-style project management with task tracking, deadlines, and team collaboration
"""

import os
import json
import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class ProjectStatus(Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskType(Enum):
    FEATURE = "feature"
    BUG = "bug"
    MAINTENANCE = "maintenance"
    INSPECTION = "inspection"
    DOCUMENTATION = "documentation"
    MEETING = "meeting"
    PROPERTY_VISIT = "property_visit"

class CommentType(Enum):
    GENERAL = "general"
    STATUS_UPDATE = "status_update"
    BLOCKER = "blocker"
    QUESTION = "question"

@dataclass
class Project:
    """Project information"""
    project_id: str
    name: str
    description: str
    status: ProjectStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    start_date: Optional[datetime]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    members: List[str]
    managers: List[str]
    property_id: Optional[str]
    client_id: Optional[str]
    budget: Optional[float]
    progress_percentage: float
    tags: List[str]
    metadata: Dict[str, Any]

@dataclass
class Task:
    """Task information"""
    task_id: str
    project_id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    task_type: TaskType
    created_by: str
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    start_date: Optional[datetime]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    parent_task_id: Optional[str]
    dependencies: List[str]  # Task IDs this task depends on
    subtasks: List[str]  # Child task IDs
    attachments: List[Dict[str, Any]]
    labels: List[str]
    checklist: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@dataclass
class TaskComment:
    """Task comment"""
    comment_id: str
    task_id: str
    user_id: str
    content: str
    comment_type: CommentType
    created_at: datetime
    updated_at: Optional[datetime]
    attachments: List[Dict[str, Any]]
    mentions: List[str]
    is_internal: bool

@dataclass
class TimeEntry:
    """Time tracking entry"""
    entry_id: str
    task_id: str
    user_id: str
    description: str
    hours: float
    date: datetime
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    is_billable: bool
    rate: Optional[float]

@dataclass
class TaskActivity:
    """Task activity log"""
    activity_id: str
    task_id: str
    user_id: str
    action: str
    field_changed: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    description: str
    timestamp: datetime

class ProjectManagementService:
    """Project management and task tracking service"""
    
    def __init__(self, database_path: str = "project_management.db"):
        self.database_path = database_path
        self.active_projects: Dict[str, Project] = {}
        self.active_tasks: Dict[str, Task] = {}
        
        # Initialize database
        self._initialize_database()
        
        # Create default projects
        self._create_default_projects()
        
        logger.info("Project Management Service initialized")
    
    def _initialize_database(self):
        """Initialize project management database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                start_date TEXT,
                due_date TEXT,
                completed_at TEXT,
                members TEXT,
                managers TEXT,
                property_id TEXT,
                client_id TEXT,
                budget REAL,
                progress_percentage REAL DEFAULT 0,
                tags TEXT,
                metadata TEXT
            )
        """)
        
        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL,
                priority TEXT NOT NULL,
                task_type TEXT NOT NULL,
                created_by TEXT NOT NULL,
                assigned_to TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                start_date TEXT,
                due_date TEXT,
                completed_at TEXT,
                estimated_hours REAL,
                actual_hours REAL,
                parent_task_id TEXT,
                dependencies TEXT,
                subtasks TEXT,
                attachments TEXT,
                labels TEXT,
                checklist TEXT,
                metadata TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (project_id)
            )
        """)
        
        # Task comments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_comments (
                comment_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                comment_type TEXT DEFAULT 'general',
                created_at TEXT NOT NULL,
                updated_at TEXT,
                attachments TEXT,
                mentions TEXT,
                is_internal BOOLEAN DEFAULT 0,
                FOREIGN KEY (task_id) REFERENCES tasks (task_id)
            )
        """)
        
        # Time entries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS time_entries (
                entry_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                description TEXT,
                hours REAL NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                is_billable BOOLEAN DEFAULT 1,
                rate REAL,
                FOREIGN KEY (task_id) REFERENCES tasks (task_id)
            )
        """)
        
        # Task activities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_activities (
                activity_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                field_changed TEXT,
                old_value TEXT,
                new_value TEXT,
                description TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (task_id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks (project_id, status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks (assigned_to, status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activities_task ON task_activities (task_id, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_time_entries_task ON time_entries (task_id, date)")
        
        conn.commit()
        conn.close()
    
    def _create_default_projects(self):
        """Create default sample projects"""
        default_projects = [
            {
                "name": "Property Maintenance Schedule",
                "description": "Quarterly maintenance tasks for all properties",
                "property_id": "prop_001",
                "tags": ["maintenance", "quarterly", "properties"]
            },
            {
                "name": "New Tenant Onboarding",
                "description": "Streamline tenant onboarding process",
                "tags": ["onboarding", "tenants", "process"]
            },
            {
                "name": "Property Marketing Campaign",
                "description": "Digital marketing campaign for vacant units",
                "property_id": "prop_002",
                "tags": ["marketing", "vacancy", "digital"]
            }
        ]
        
        for proj_data in default_projects:
            try:
                project = Project(
                    project_id=str(uuid.uuid4()),
                    name=proj_data["name"],
                    description=proj_data["description"],
                    status=ProjectStatus.ACTIVE,
                    created_by="system",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    start_date=datetime.now(),
                    due_date=datetime.now() + timedelta(days=90),
                    completed_at=None,
                    members=["system", "admin_001"],
                    managers=["admin_001"],
                    property_id=proj_data.get("property_id"),
                    client_id=None,
                    budget=None,
                    progress_percentage=0.0,
                    tags=proj_data.get("tags", []),
                    metadata={}
                )
                
                self._save_project(project)
                
                # Create sample tasks for each project
                self._create_sample_tasks(project.project_id)
                
            except Exception as e:
                logger.error(f"Failed to create default project: {e}")
    
    def _create_sample_tasks(self, project_id: str):
        """Create sample tasks for a project"""
        if "Maintenance" in project_id:
            sample_tasks = [
                {
                    "title": "HVAC System Inspection",
                    "description": "Quarterly inspection of all HVAC systems",
                    "task_type": TaskType.INSPECTION,
                    "priority": TaskPriority.HIGH,
                    "estimated_hours": 8.0
                },
                {
                    "title": "Plumbing Maintenance Check",
                    "description": "Check all plumbing fixtures and pipes",
                    "task_type": TaskType.MAINTENANCE,
                    "priority": TaskPriority.MEDIUM,
                    "estimated_hours": 4.0
                }
            ]
        elif "Onboarding" in project_id:
            sample_tasks = [
                {
                    "title": "Create Welcome Package",
                    "description": "Design and create tenant welcome materials",
                    "task_type": TaskType.DOCUMENTATION,
                    "priority": TaskPriority.MEDIUM,
                    "estimated_hours": 6.0
                },
                {
                    "title": "Setup Digital Onboarding Portal",
                    "description": "Configure online portal for new tenants",
                    "task_type": TaskType.FEATURE,
                    "priority": TaskPriority.HIGH,
                    "estimated_hours": 16.0
                }
            ]
        else:
            sample_tasks = [
                {
                    "title": "Social Media Content Creation",
                    "description": "Create engaging content for property listings",
                    "task_type": TaskType.FEATURE,
                    "priority": TaskPriority.MEDIUM,
                    "estimated_hours": 12.0
                }
            ]
        
        for task_data in sample_tasks:
            try:
                task = Task(
                    task_id=str(uuid.uuid4()),
                    project_id=project_id,
                    title=task_data["title"],
                    description=task_data["description"],
                    status=TaskStatus.TODO,
                    priority=task_data["priority"],
                    task_type=task_data["task_type"],
                    created_by="system",
                    assigned_to=None,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    start_date=None,
                    due_date=datetime.now() + timedelta(days=30),
                    completed_at=None,
                    estimated_hours=task_data["estimated_hours"],
                    actual_hours=None,
                    parent_task_id=None,
                    dependencies=[],
                    subtasks=[],
                    attachments=[],
                    labels=[],
                    checklist=[],
                    metadata={}
                )
                
                self._save_task(task)
                
            except Exception as e:
                logger.error(f"Failed to create sample task: {e}")
    
    async def create_project(self, name: str, description: str, created_by: str,
                           start_date: Optional[datetime] = None,
                           due_date: Optional[datetime] = None,
                           property_id: Optional[str] = None,
                           client_id: Optional[str] = None,
                           budget: Optional[float] = None,
                           members: List[str] = None,
                           tags: List[str] = None) -> Project:
        """Create new project"""
        try:
            project_id = str(uuid.uuid4())
            now = datetime.now()
            
            project = Project(
                project_id=project_id,
                name=name,
                description=description,
                status=ProjectStatus.PLANNING,
                created_by=created_by,
                created_at=now,
                updated_at=now,
                start_date=start_date,
                due_date=due_date,
                completed_at=None,
                members=members or [created_by],
                managers=[created_by],
                property_id=property_id,
                client_id=client_id,
                budget=budget,
                progress_percentage=0.0,
                tags=tags or [],
                metadata={}
            )
            
            # Save project
            await self._save_project(project)
            
            # Cache project
            self.active_projects[project_id] = project
            
            logger.info(f"Project created: {project_id}")
            return project
            
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise
    
    async def create_task(self, project_id: str, title: str, description: str,
                         created_by: str, task_type: TaskType = TaskType.FEATURE,
                         priority: TaskPriority = TaskPriority.MEDIUM,
                         assigned_to: Optional[str] = None,
                         due_date: Optional[datetime] = None,
                         estimated_hours: Optional[float] = None,
                         parent_task_id: Optional[str] = None,
                         dependencies: List[str] = None,
                         labels: List[str] = None) -> Task:
        """Create new task"""
        try:
            task_id = str(uuid.uuid4())
            now = datetime.now()
            
            task = Task(
                task_id=task_id,
                project_id=project_id,
                title=title,
                description=description,
                status=TaskStatus.TODO,
                priority=priority,
                task_type=task_type,
                created_by=created_by,
                assigned_to=assigned_to,
                created_at=now,
                updated_at=now,
                start_date=None,
                due_date=due_date,
                completed_at=None,
                estimated_hours=estimated_hours,
                actual_hours=None,
                parent_task_id=parent_task_id,
                dependencies=dependencies or [],
                subtasks=[],
                attachments=[],
                labels=labels or [],
                checklist=[],
                metadata={}
            )
            
            # Save task
            await self._save_task(task)
            
            # Log activity
            await self._log_task_activity(
                task_id, created_by, "task_created", 
                description=f"Task '{title}' created"
            )
            
            # Update parent task if this is a subtask
            if parent_task_id:
                await self._add_subtask(parent_task_id, task_id)
            
            # Cache task
            self.active_tasks[task_id] = task
            
            # Notify assigned user
            if assigned_to and assigned_to != created_by:
                await self._notify_task_assigned(task_id, assigned_to, created_by)
            
            logger.info(f"Task created: {task_id}")
            return task
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise
    
    async def update_task_status(self, task_id: str, new_status: TaskStatus, 
                               updated_by: str) -> bool:
        """Update task status"""
        try:
            task = await self._get_task(task_id)
            if not task:
                raise ValueError("Task not found")
            
            old_status = task.status
            task.status = new_status
            task.updated_at = datetime.now()
            
            # Set completion date if completed
            if new_status == TaskStatus.COMPLETED:
                task.completed_at = datetime.now()
            
            # Save task
            await self._save_task(task)
            
            # Log activity
            await self._log_task_activity(
                task_id, updated_by, "status_changed",
                field_changed="status",
                old_value=old_status.value,
                new_value=new_status.value,
                description=f"Status changed from {old_status.value} to {new_status.value}"
            )
            
            # Update project progress
            await self._update_project_progress(task.project_id)
            
            # Update cached task
            self.active_tasks[task_id] = task
            
            # Notify stakeholders
            await self._notify_task_status_changed(task_id, old_status, new_status, updated_by)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            return False
    
    async def assign_task(self, task_id: str, assigned_to: str, assigned_by: str) -> bool:
        """Assign task to user"""
        try:
            task = await self._get_task(task_id)
            if not task:
                raise ValueError("Task not found")
            
            old_assignee = task.assigned_to
            task.assigned_to = assigned_to
            task.updated_at = datetime.now()
            
            # Save task
            await self._save_task(task)
            
            # Log activity
            await self._log_task_activity(
                task_id, assigned_by, "task_assigned",
                field_changed="assigned_to",
                old_value=old_assignee,
                new_value=assigned_to,
                description=f"Task assigned to {assigned_to}"
            )
            
            # Update cached task
            self.active_tasks[task_id] = task
            
            # Notify new assignee
            await self._notify_task_assigned(task_id, assigned_to, assigned_by)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to assign task: {e}")
            return False
    
    async def add_task_comment(self, task_id: str, user_id: str, content: str,
                             comment_type: CommentType = CommentType.GENERAL,
                             is_internal: bool = False,
                             attachments: List[Dict[str, Any]] = None) -> TaskComment:
        """Add comment to task"""
        try:
            comment_id = str(uuid.uuid4())
            
            comment = TaskComment(
                comment_id=comment_id,
                task_id=task_id,
                user_id=user_id,
                content=content,
                comment_type=comment_type,
                created_at=datetime.now(),
                updated_at=None,
                attachments=attachments or [],
                mentions=self._extract_mentions(content),
                is_internal=is_internal
            )
            
            # Save comment
            await self._save_task_comment(comment)
            
            # Log activity
            await self._log_task_activity(
                task_id, user_id, "comment_added",
                description=f"Comment added: {content[:50]}..."
            )
            
            # Notify mentioned users
            if comment.mentions:
                await self._notify_users_mentioned(task_id, comment.mentions, user_id)
            
            return comment
            
        except Exception as e:
            logger.error(f"Failed to add task comment: {e}")
            raise
    
    async def log_time_entry(self, task_id: str, user_id: str, hours: float,
                           description: str = "", date: datetime = None,
                           is_billable: bool = True, rate: Optional[float] = None) -> TimeEntry:
        """Log time entry for task"""
        try:
            entry_id = str(uuid.uuid4())
            
            time_entry = TimeEntry(
                entry_id=entry_id,
                task_id=task_id,
                user_id=user_id,
                description=description,
                hours=hours,
                date=date or datetime.now(),
                start_time=None,
                end_time=None,
                is_billable=is_billable,
                rate=rate
            )
            
            # Save time entry
            await self._save_time_entry(time_entry)
            
            # Update task actual hours
            await self._update_task_actual_hours(task_id)
            
            # Log activity
            await self._log_task_activity(
                task_id, user_id, "time_logged",
                description=f"Logged {hours} hours: {description}"
            )
            
            return time_entry
            
        except Exception as e:
            logger.error(f"Failed to log time entry: {e}")
            raise
    
    async def get_project_tasks(self, project_id: str, status_filter: List[TaskStatus] = None) -> List[Task]:
        """Get tasks for project"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM tasks WHERE project_id = ?"
            params = [project_id]
            
            if status_filter:
                placeholders = ','.join(['?' for _ in status_filter])
                query += f" AND status IN ({placeholders})"
                params.extend([status.value for status in status_filter])
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            tasks = []
            for row in rows:
                task = self._row_to_task(row)
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to get project tasks: {e}")
            return []
    
    async def get_user_tasks(self, user_id: str, status_filter: List[TaskStatus] = None) -> List[Task]:
        """Get tasks assigned to user"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM tasks WHERE assigned_to = ?"
            params = [user_id]
            
            if status_filter:
                placeholders = ','.join(['?' for _ in status_filter])
                query += f" AND status IN ({placeholders})"
                params.extend([status.value for status in status_filter])
            
            query += " ORDER BY priority DESC, due_date ASC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            tasks = []
            for row in rows:
                task = self._row_to_task(row)
                tasks.append(task)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to get user tasks: {e}")
            return []
    
    async def get_project_analytics(self, project_id: str) -> Dict[str, Any]:
        """Get project analytics and metrics"""
        try:
            project = await self._get_project(project_id)
            if not project:
                return {}
            
            tasks = await self.get_project_tasks(project_id)
            
            # Task status distribution
            status_counts = {}
            for status in TaskStatus:
                status_counts[status.value] = len([t for t in tasks if t.status == status])
            
            # Priority distribution
            priority_counts = {}
            for priority in TaskPriority:
                priority_counts[priority.value] = len([t for t in tasks if t.priority == priority])
            
            # Progress metrics
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
            progress_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Time tracking metrics
            total_estimated = sum([t.estimated_hours or 0 for t in tasks])
            total_actual = sum([t.actual_hours or 0 for t in tasks])
            
            # Overdue tasks
            now = datetime.now()
            overdue_tasks = [
                t for t in tasks 
                if t.due_date and t.due_date < now and t.status != TaskStatus.COMPLETED
            ]
            
            return {
                "project_id": project_id,
                "project_name": project.name,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "progress_percentage": progress_percentage,
                "status_distribution": status_counts,
                "priority_distribution": priority_counts,
                "time_metrics": {
                    "total_estimated_hours": total_estimated,
                    "total_actual_hours": total_actual,
                    "time_variance": total_actual - total_estimated
                },
                "overdue_tasks": len(overdue_tasks),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get project analytics: {e}")
            return {}
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract user mentions from content"""
        import re
        mention_pattern = r'@(\w+)'
        matches = re.findall(mention_pattern, content)
        return matches
    
    def _row_to_task(self, row) -> Task:
        """Convert database row to Task object"""
        return Task(
            task_id=row[0],
            project_id=row[1],
            title=row[2],
            description=row[3] or "",
            status=TaskStatus(row[4]),
            priority=TaskPriority(row[5]),
            task_type=TaskType(row[6]),
            created_by=row[7],
            assigned_to=row[8],
            created_at=datetime.fromisoformat(row[9]),
            updated_at=datetime.fromisoformat(row[10]),
            start_date=datetime.fromisoformat(row[11]) if row[11] else None,
            due_date=datetime.fromisoformat(row[12]) if row[12] else None,
            completed_at=datetime.fromisoformat(row[13]) if row[13] else None,
            estimated_hours=row[14],
            actual_hours=row[15],
            parent_task_id=row[16],
            dependencies=json.loads(row[17]) if row[17] else [],
            subtasks=json.loads(row[18]) if row[18] else [],
            attachments=json.loads(row[19]) if row[19] else [],
            labels=json.loads(row[20]) if row[20] else [],
            checklist=json.loads(row[21]) if row[21] else [],
            metadata=json.loads(row[22]) if row[22] else {}
        )
    
    # Placeholder notification methods
    async def _notify_task_assigned(self, task_id: str, assigned_to: str, assigned_by: str):
        """Notify user about task assignment"""
        logger.info(f"Notifying {assigned_to} about task assignment: {task_id}")
    
    async def _notify_task_status_changed(self, task_id: str, old_status: TaskStatus, 
                                        new_status: TaskStatus, updated_by: str):
        """Notify stakeholders about status change"""
        logger.info(f"Notifying about status change for task {task_id}: {old_status.value} -> {new_status.value}")

# Global instance
_project_service = None

def get_project_service() -> ProjectManagementService:
    """Get global project management service instance"""
    global _project_service
    if _project_service is None:
        _project_service = ProjectManagementService()
    return _project_service

# API convenience functions
async def create_project_api(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create project for API"""
    service = get_project_service()
    
    project = await service.create_project(
        name=project_data["name"],
        description=project_data.get("description", ""),
        created_by=project_data["created_by"],
        start_date=datetime.fromisoformat(project_data["start_date"]) if project_data.get("start_date") else None,
        due_date=datetime.fromisoformat(project_data["due_date"]) if project_data.get("due_date") else None,
        property_id=project_data.get("property_id"),
        client_id=project_data.get("client_id"),
        budget=project_data.get("budget"),
        members=project_data.get("members", []),
        tags=project_data.get("tags", [])
    )
    
    return asdict(project)

async def create_task_api(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create task for API"""
    service = get_project_service()
    
    task = await service.create_task(
        project_id=task_data["project_id"],
        title=task_data["title"],
        description=task_data.get("description", ""),
        created_by=task_data["created_by"],
        task_type=TaskType(task_data.get("task_type", "feature")),
        priority=TaskPriority(task_data.get("priority", "medium")),
        assigned_to=task_data.get("assigned_to"),
        due_date=datetime.fromisoformat(task_data["due_date"]) if task_data.get("due_date") else None,
        estimated_hours=task_data.get("estimated_hours"),
        parent_task_id=task_data.get("parent_task_id"),
        dependencies=task_data.get("dependencies", []),
        labels=task_data.get("labels", [])
    )
    
    return asdict(task)

async def get_project_analytics_api(project_id: str) -> Dict[str, Any]:
    """Get project analytics for API"""
    service = get_project_service()
    return await service.get_project_analytics(project_id)

if __name__ == "__main__":
    # Test the project management service
    async def test_project_management():
        service = ProjectManagementService()
        
        print("Testing Project Management Service")
        print("=" * 50)
        
        # Test creating a project
        project = await service.create_project(
            name="Test Project",
            description="A test project for demonstration",
            created_by="test_user",
            due_date=datetime.now() + timedelta(days=60),
            tags=["test", "demo"]
        )
        print(f"Created project: {project.project_id}")
        
        # Test creating a task
        task = await service.create_task(
            project_id=project.project_id,
            title="Test Task",
            description="A test task for the project",
            created_by="test_user",
            task_type=TaskType.FEATURE,
            priority=TaskPriority.HIGH,
            estimated_hours=8.0
        )
        print(f"Created task: {task.task_id}")
        
        # Test getting project analytics
        analytics = await service.get_project_analytics(project.project_id)
        print(f"Project has {analytics['total_tasks']} tasks")
        
        print("\nProject Management Test Complete!")
    
    asyncio.run(test_project_management())