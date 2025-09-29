#!/usr/bin/env python3
"""
Real-time Document Collaboration System for EstateCore Phase 8B
Google Docs-style collaborative document editing with operational transforms
"""

import os
import json
import asyncio
import logging
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
from collections import defaultdict, deque
import difflib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentType(Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    LEASE_AGREEMENT = "lease_agreement"
    PROPERTY_REPORT = "property_report"
    MAINTENANCE_CHECKLIST = "maintenance_checklist"
    INSPECTION_FORM = "inspection_form"
    FINANCIAL_REPORT = "financial_report"

class OperationType(Enum):
    INSERT = "insert"
    DELETE = "delete"
    RETAIN = "retain"
    FORMAT = "format"

class PermissionLevel(Enum):
    OWNER = "owner"
    EDITOR = "editor"
    COMMENTER = "commenter"
    VIEWER = "viewer"

class DocumentStatus(Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"

@dataclass
class Operation:
    """Operational Transform operation"""
    operation_id: str
    user_id: str
    operation_type: OperationType
    position: int
    content: str
    length: int
    attributes: Dict[str, Any]
    timestamp: datetime
    revision: int

@dataclass
class Document:
    """Collaborative document"""
    document_id: str
    title: str
    content: str
    document_type: DocumentType
    created_by: str
    created_at: datetime
    updated_at: datetime
    current_revision: int
    status: DocumentStatus
    permissions: Dict[str, PermissionLevel]  # user_id -> permission
    property_id: Optional[str]
    project_id: Optional[str]
    template_id: Optional[str]
    metadata: Dict[str, Any]
    is_deleted: bool

@dataclass
class DocumentVersion:
    """Document version/revision"""
    version_id: str
    document_id: str
    revision_number: int
    content: str
    changed_by: str
    created_at: datetime
    change_summary: str
    diff_data: str

@dataclass
class Comment:
    """Document comment"""
    comment_id: str
    document_id: str
    user_id: str
    content: str
    position: int
    thread_id: Optional[str]
    parent_comment_id: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_resolved: bool
    mentions: List[str]

@dataclass
class Cursor:
    """User cursor position in document"""
    user_id: str
    document_id: str
    position: int
    selection_start: int
    selection_end: int
    last_seen: datetime

class DocumentCollaborationService:
    """Real-time document collaboration service"""
    
    def __init__(self, database_path: str = "document_collaboration.db"):
        self.database_path = database_path
        self.active_documents: Dict[str, Document] = {}
        self.active_cursors: Dict[str, Dict[str, Cursor]] = defaultdict(dict)  # doc_id -> {user_id: cursor}
        self.operation_queues: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))  # doc_id -> operations
        self.document_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        
        # Initialize database
        self._initialize_database()
        
        # Load default documents
        self._create_default_documents()
        
        logger.info("Document Collaboration Service initialized")
    
    def _initialize_database(self):
        """Initialize document collaboration database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                document_type TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                current_revision INTEGER DEFAULT 1,
                status TEXT DEFAULT 'draft',
                permissions TEXT,
                property_id TEXT,
                project_id TEXT,
                template_id TEXT,
                metadata TEXT,
                is_deleted BOOLEAN DEFAULT 0
            )
        """)
        
        # Document versions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_versions (
                version_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                revision_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                changed_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                change_summary TEXT,
                diff_data TEXT,
                FOREIGN KEY (document_id) REFERENCES documents (document_id),
                UNIQUE(document_id, revision_number)
            )
        """)
        
        # Operations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operations (
                operation_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                position INTEGER NOT NULL,
                content TEXT,
                length INTEGER DEFAULT 0,
                attributes TEXT,
                timestamp TEXT NOT NULL,
                revision INTEGER NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents (document_id)
            )
        """)
        
        # Comments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                comment_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                position INTEGER,
                thread_id TEXT,
                parent_comment_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                is_resolved BOOLEAN DEFAULT 0,
                mentions TEXT,
                FOREIGN KEY (document_id) REFERENCES documents (document_id)
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_operations_document_revision ON operations (document_id, revision)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_versions_document ON document_versions (document_id, revision_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comments_document ON comments (document_id, created_at)")
        
        conn.commit()
        conn.close()
    
    def _create_default_documents(self):
        """Create default document templates"""
        default_documents = [
            {
                "title": "Standard Lease Agreement Template",
                "content": """# RESIDENTIAL LEASE AGREEMENT

**Property Address:** [PROPERTY_ADDRESS]
**Landlord:** [LANDLORD_NAME]
**Tenant:** [TENANT_NAME]
**Lease Term:** [START_DATE] to [END_DATE]

## 1. RENT AND PAYMENT TERMS
Monthly Rent: $[MONTHLY_RENT]
Security Deposit: $[SECURITY_DEPOSIT]
Due Date: [DUE_DATE] of each month

## 2. PROPERTY DESCRIPTION
The leased premises consist of [PROPERTY_DESCRIPTION]

## 3. TENANT RESPONSIBILITIES
- Maintain property in good condition
- Pay rent on time
- Follow property rules and regulations

## 4. LANDLORD RESPONSIBILITIES
- Maintain structural integrity
- Provide necessary repairs
- Ensure habitability

[Additional terms and conditions...]
""",
                "document_type": DocumentType.LEASE_AGREEMENT,
                "template_id": "lease_template_001"
            },
            {
                "title": "Property Inspection Checklist",
                "content": """# PROPERTY INSPECTION CHECKLIST

**Property:** [PROPERTY_ADDRESS]
**Inspector:** [INSPECTOR_NAME]  
**Date:** [INSPECTION_DATE]
**Type:** [INSPECTION_TYPE]

## EXTERIOR INSPECTION
- [ ] Roof condition
- [ ] Gutters and downspouts
- [ ] Exterior walls and siding
- [ ] Windows and doors
- [ ] Landscaping

## INTERIOR INSPECTION
- [ ] Electrical systems
- [ ] Plumbing systems
- [ ] HVAC systems
- [ ] Flooring condition
- [ ] Wall and ceiling condition

## SAFETY CHECKS
- [ ] Smoke detectors
- [ ] Carbon monoxide detectors
- [ ] Security systems
- [ ] Emergency exits

## NOTES AND RECOMMENDATIONS
[Inspector notes...]

**Inspector Signature:** ________________
**Date:** ________________
""",
                "document_type": DocumentType.INSPECTION_FORM,
                "template_id": "inspection_template_001"
            }
        ]
        
        for doc_data in default_documents:
            try:
                document = Document(
                    document_id=str(uuid.uuid4()),
                    title=doc_data["title"],
                    content=doc_data["content"],
                    document_type=doc_data["document_type"],
                    created_by="system",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    current_revision=1,
                    status=DocumentStatus.PUBLISHED,
                    permissions={"system": PermissionLevel.OWNER},
                    property_id=None,
                    project_id=None,
                    template_id=doc_data.get("template_id"),
                    metadata={"is_template": True},
                    is_deleted=False
                )
                
                self._save_document(document)
                
            except Exception as e:
                logger.error(f"Failed to create default document: {e}")
    
    async def create_document(self, title: str, document_type: DocumentType, 
                            created_by: str, content: str = "",
                            property_id: Optional[str] = None,
                            project_id: Optional[str] = None,
                            template_id: Optional[str] = None) -> Document:
        """Create new collaborative document"""
        try:
            document_id = str(uuid.uuid4())
            now = datetime.now()
            
            # If template_id provided, load template content
            if template_id and not content:
                template = await self._get_document_by_template_id(template_id)
                if template:
                    content = template.content
            
            document = Document(
                document_id=document_id,
                title=title,
                content=content,
                document_type=document_type,
                created_by=created_by,
                created_at=now,
                updated_at=now,
                current_revision=1,
                status=DocumentStatus.DRAFT,
                permissions={created_by: PermissionLevel.OWNER},
                property_id=property_id,
                project_id=project_id,
                template_id=template_id,
                metadata={},
                is_deleted=False
            )
            
            # Save document
            await self._save_document(document)
            
            # Create initial version
            await self._create_version(document, "Document created")
            
            # Cache document
            self.active_documents[document_id] = document
            
            logger.info(f"Document created: {document_id}")
            return document
            
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise
    
    async def apply_operation(self, document_id: str, operation: Operation) -> bool:
        """Apply operation to document using operational transform"""
        try:
            with self.document_locks[document_id]:
                # Get current document
                document = await self._get_document(document_id)
                if not document:
                    raise ValueError("Document not found")
                
                # Transform operation against pending operations
                transformed_op = await self._transform_operation(document_id, operation)
                
                # Apply operation to document content
                new_content = self._apply_operation_to_content(
                    document.content, transformed_op
                )
                
                # Update document
                document.content = new_content
                document.updated_at = datetime.now()
                document.current_revision += 1
                
                # Save operation
                await self._save_operation(document_id, transformed_op)
                
                # Save document
                await self._save_document(document)
                
                # Add to operation queue
                self.operation_queues[document_id].append(transformed_op)
                
                # Broadcast operation to other users
                await self._broadcast_operation(document_id, transformed_op)
                
                # Update cached document
                self.active_documents[document_id] = document
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to apply operation: {e}")
            return False
    
    async def _transform_operation(self, document_id: str, operation: Operation) -> Operation:
        """Transform operation against concurrent operations"""
        # Get operations since this user's last known revision
        pending_ops = await self._get_operations_since_revision(
            document_id, operation.revision
        )
        
        transformed_op = operation
        
        # Apply operational transformation for each pending operation
        for pending_op in pending_ops:
            transformed_op = self._transform_against_operation(transformed_op, pending_op)
        
        # Update revision to current
        document = await self._get_document(document_id)
        transformed_op.revision = document.current_revision if document else operation.revision
        
        return transformed_op
    
    def _transform_against_operation(self, op1: Operation, op2: Operation) -> Operation:
        """Transform operation op1 against operation op2"""
        # Simplified operational transform implementation
        if op1.operation_type == OperationType.INSERT and op2.operation_type == OperationType.INSERT:
            # Both insertions
            if op1.position <= op2.position:
                return op1  # No change needed
            else:
                # Adjust position
                new_op = Operation(
                    operation_id=op1.operation_id,
                    user_id=op1.user_id,
                    operation_type=op1.operation_type,
                    position=op1.position + len(op2.content),
                    content=op1.content,
                    length=op1.length,
                    attributes=op1.attributes,
                    timestamp=op1.timestamp,
                    revision=op1.revision
                )
                return new_op
        
        elif op1.operation_type == OperationType.DELETE and op2.operation_type == OperationType.INSERT:
            # Delete vs Insert
            if op1.position < op2.position:
                return op1
            else:
                new_op = Operation(
                    operation_id=op1.operation_id,
                    user_id=op1.user_id,
                    operation_type=op1.operation_type,
                    position=op1.position + len(op2.content),
                    content=op1.content,
                    length=op1.length,
                    attributes=op1.attributes,
                    timestamp=op1.timestamp,
                    revision=op1.revision
                )
                return new_op
        
        elif op1.operation_type == OperationType.INSERT and op2.operation_type == OperationType.DELETE:
            # Insert vs Delete
            if op1.position <= op2.position:
                return op1
            elif op1.position >= op2.position + op2.length:
                new_op = Operation(
                    operation_id=op1.operation_id,
                    user_id=op1.user_id,
                    operation_type=op1.operation_type,
                    position=op1.position - op2.length,
                    content=op1.content,
                    length=op1.length,
                    attributes=op1.attributes,
                    timestamp=op1.timestamp,
                    revision=op1.revision
                )
                return new_op
            else:
                # Insert position is within deleted range
                new_op = Operation(
                    operation_id=op1.operation_id,
                    user_id=op1.user_id,
                    operation_type=op1.operation_type,
                    position=op2.position,
                    content=op1.content,
                    length=op1.length,
                    attributes=op1.attributes,
                    timestamp=op1.timestamp,
                    revision=op1.revision
                )
                return new_op
        
        # Default: return original operation
        return op1
    
    def _apply_operation_to_content(self, content: str, operation: Operation) -> str:
        """Apply operation to content string"""
        if operation.operation_type == OperationType.INSERT:
            # Insert content at position
            return content[:operation.position] + operation.content + content[operation.position:]
        
        elif operation.operation_type == OperationType.DELETE:
            # Delete content from position
            start = operation.position
            end = operation.position + operation.length
            return content[:start] + content[end:]
        
        elif operation.operation_type == OperationType.RETAIN:
            # No change to content
            return content
        
        return content
    
    async def update_cursor_position(self, document_id: str, user_id: str, 
                                   position: int, selection_start: int = None,
                                   selection_end: int = None):
        """Update user cursor position"""
        cursor = Cursor(
            user_id=user_id,
            document_id=document_id,
            position=position,
            selection_start=selection_start or position,
            selection_end=selection_end or position,
            last_seen=datetime.now()
        )
        
        self.active_cursors[document_id][user_id] = cursor
        
        # Broadcast cursor position to other users
        await self._broadcast_cursor_update(document_id, cursor)
    
    async def add_comment(self, document_id: str, user_id: str, content: str,
                         position: int, thread_id: Optional[str] = None,
                         parent_comment_id: Optional[str] = None) -> Comment:
        """Add comment to document"""
        try:
            comment_id = str(uuid.uuid4())
            
            comment = Comment(
                comment_id=comment_id,
                document_id=document_id,
                user_id=user_id,
                content=content,
                position=position,
                thread_id=thread_id or comment_id,  # Use comment_id as thread_id if not provided
                parent_comment_id=parent_comment_id,
                created_at=datetime.now(),
                updated_at=None,
                is_resolved=False,
                mentions=self._extract_mentions(content)
            )
            
            # Save comment
            await self._save_comment(comment)
            
            # Broadcast comment to document collaborators
            await self._broadcast_comment(document_id, comment)
            
            return comment
            
        except Exception as e:
            logger.error(f"Failed to add comment: {e}")
            raise
    
    async def share_document(self, document_id: str, user_id: str, 
                           permission: PermissionLevel, shared_by: str) -> bool:
        """Share document with user"""
        try:
            document = await self._get_document(document_id)
            if not document:
                raise ValueError("Document not found")
            
            # Check if sharer has permission to share
            sharer_permission = document.permissions.get(shared_by)
            if sharer_permission not in [PermissionLevel.OWNER, PermissionLevel.EDITOR]:
                raise ValueError("Insufficient permissions to share document")
            
            # Add user permission
            document.permissions[user_id] = permission
            document.updated_at = datetime.now()
            
            # Save document
            await self._save_document(document)
            
            # Update cached document
            self.active_documents[document_id] = document
            
            # Notify user about document share
            await self._notify_document_shared(document_id, user_id, shared_by, permission)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to share document: {e}")
            return False
    
    async def get_user_documents(self, user_id: str) -> List[Document]:
        """Get documents accessible to user"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM documents 
                WHERE permissions LIKE ? AND is_deleted = 0
                ORDER BY updated_at DESC
            """, [f'%{user_id}%'])
            
            rows = cursor.fetchall()
            conn.close()
            
            documents = []
            for row in rows:
                document = self._row_to_document(row)
                # Verify user actually has permission
                if user_id in document.permissions:
                    documents.append(document)
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to get user documents: {e}")
            return []
    
    async def get_document_history(self, document_id: str) -> List[DocumentVersion]:
        """Get document version history"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM document_versions 
                WHERE document_id = ?
                ORDER BY revision_number DESC
            """, [document_id])
            
            rows = cursor.fetchall()
            conn.close()
            
            versions = []
            for row in rows:
                version = DocumentVersion(
                    version_id=row[0],
                    document_id=row[1],
                    revision_number=row[2],
                    content=row[3],
                    changed_by=row[4],
                    created_at=datetime.fromisoformat(row[5]),
                    change_summary=row[6] or "",
                    diff_data=row[7] or ""
                )
                versions.append(version)
            
            return versions
            
        except Exception as e:
            logger.error(f"Failed to get document history: {e}")
            return []
    
    def _extract_mentions(self, content: str) -> List[str]:
        """Extract user mentions from content"""
        import re
        mention_pattern = r'@(\w+)'
        matches = re.findall(mention_pattern, content)
        return matches
    
    def _row_to_document(self, row) -> Document:
        """Convert database row to Document object"""
        return Document(
            document_id=row[0],
            title=row[1],
            content=row[2] or "",
            document_type=DocumentType(row[3]),
            created_by=row[4],
            created_at=datetime.fromisoformat(row[5]),
            updated_at=datetime.fromisoformat(row[6]),
            current_revision=row[7],
            status=DocumentStatus(row[8]),
            permissions=json.loads(row[9]) if row[9] else {},
            property_id=row[10],
            project_id=row[11],
            template_id=row[12],
            metadata=json.loads(row[13]) if row[13] else {},
            is_deleted=bool(row[14])
        )
    
    async def _save_document(self, document: Document):
        """Save document to database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO documents 
            (document_id, title, content, document_type, created_by, created_at,
             updated_at, current_revision, status, permissions, property_id,
             project_id, template_id, metadata, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document.document_id, document.title, document.content,
            document.document_type.value, document.created_by,
            document.created_at.isoformat(), document.updated_at.isoformat(),
            document.current_revision, document.status.value,
            json.dumps({k: v.value for k, v in document.permissions.items()}),
            document.property_id, document.project_id, document.template_id,
            json.dumps(document.metadata), document.is_deleted
        ))
        
        conn.commit()
        conn.close()
    
    def _save_document(self, document: Document):
        """Save document to database (sync version for initialization)"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO documents 
            (document_id, title, content, document_type, created_by, created_at,
             updated_at, current_revision, status, permissions, property_id,
             project_id, template_id, metadata, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            document.document_id, document.title, document.content,
            document.document_type.value, document.created_by,
            document.created_at.isoformat(), document.updated_at.isoformat(),
            document.current_revision, document.status.value,
            json.dumps({k: v.value for k, v in document.permissions.items()}),
            document.property_id, document.project_id, document.template_id,
            json.dumps(document.metadata), document.is_deleted
        ))
        
        conn.commit()
        conn.close()
    
    # Placeholder methods for real-time features
    async def _broadcast_operation(self, document_id: str, operation: Operation):
        """Broadcast operation to other collaborators"""
        logger.info(f"Broadcasting operation {operation.operation_id} for document {document_id}")
    
    async def _broadcast_cursor_update(self, document_id: str, cursor: Cursor):
        """Broadcast cursor position update"""
        logger.info(f"Broadcasting cursor update for {cursor.user_id} in document {document_id}")
    
    async def _broadcast_comment(self, document_id: str, comment: Comment):
        """Broadcast new comment"""
        logger.info(f"Broadcasting comment {comment.comment_id} for document {document_id}")

# Global instance
_document_service = None

def get_document_service() -> DocumentCollaborationService:
    """Get global document collaboration service instance"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentCollaborationService()
    return _document_service

# API convenience functions
async def create_collaborative_document_api(doc_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create collaborative document for API"""
    service = get_document_service()
    
    document = await service.create_document(
        title=doc_data["title"],
        document_type=DocumentType(doc_data.get("document_type", "text")),
        created_by=doc_data["created_by"],
        content=doc_data.get("content", ""),
        property_id=doc_data.get("property_id"),
        project_id=doc_data.get("project_id"),
        template_id=doc_data.get("template_id")
    )
    
    return asdict(document)

async def get_user_documents_api(user_id: str) -> Dict[str, Any]:
    """Get user documents for API"""
    service = get_document_service()
    
    documents = await service.get_user_documents(user_id)
    
    return {
        "user_id": user_id,
        "documents": [asdict(doc) for doc in documents],
        "count": len(documents)
    }

if __name__ == "__main__":
    # Test the document collaboration service
    async def test_document_collaboration():
        service = DocumentCollaborationService()
        
        print("Testing Document Collaboration Service")
        print("=" * 50)
        
        # Test creating a document
        document = await service.create_document(
            title="Test Collaboration Document",
            document_type=DocumentType.TEXT,
            created_by="test_user",
            content="This is a test document for collaboration."
        )
        print(f"Created document: {document.document_id}")
        
        # Test applying an operation
        operation = Operation(
            operation_id=str(uuid.uuid4()),
            user_id="test_user",
            operation_type=OperationType.INSERT,
            position=len(document.content),
            content=" Added text!",
            length=0,
            attributes={},
            timestamp=datetime.now(),
            revision=1
        )
        
        success = await service.apply_operation(document.document_id, operation)
        print(f"Applied operation: {success}")
        
        # Test getting user documents
        documents = await service.get_user_documents("test_user")
        print(f"User has {len(documents)} documents")
        
        print("\nDocument Collaboration Test Complete!")
    
    asyncio.run(test_document_collaboration())