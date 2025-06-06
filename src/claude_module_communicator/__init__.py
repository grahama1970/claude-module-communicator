"""
Claude Module Communicator - Simple interface for SPARTA integration
"""

from typing import Dict, Any, Optional
import json
import sqlite3
from pathlib import Path
from datetime import datetime


class ModuleCommunicator:
    """Simple module communicator for SPARTA."""
    
    def __init__(self, module_name: str, db_path: str = "~/.sparta/module_comm.db"):
        self.module_name = module_name
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for communication."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                source TEXT,
                target TEXT,
                content TEXT,
                timestamp TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY,
                module TEXT,
                task TEXT,
                completed INTEGER,
                total INTEGER,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def get_version(self) -> str:
        """Get module version."""
        return "0.1.0"
    
    def negotiate_schema(self, target_module: str, sample_data: Dict[str, Any]) -> Dict[str, Any]:
        """Negotiate schema with target module."""
        # For now, return a simple schema based on sample data
        schema = {
            "type": "object",
            "properties": {}
        }
        
        for key, value in sample_data.items():
            if isinstance(value, str):
                schema["properties"][key] = {"type": "string"}
            elif isinstance(value, int):
                schema["properties"][key] = {"type": "integer"}
            elif isinstance(value, dict):
                schema["properties"][key] = {"type": "object"}
            elif isinstance(value, list):
                schema["properties"][key] = {"type": "array"}
        
        # Add compatibility info
        return {
            "schema": schema,
            "compatibility": {
                "status": "compatible",
                "version": "1.0"
            }
        }
    
    def track_progress(self, task: str, completed: int, total: int):
        """Track progress of a task."""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT OR REPLACE INTO progress (module, task, completed, total, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (self.module_name, task, completed, total, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def get_progress(self, task: str) -> Dict[str, Any]:
        """Get progress of a task."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("""
            SELECT completed, total FROM progress
            WHERE module = ? AND task = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (self.module_name, task))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            completed, total = row
            return {
                "completed": completed,
                "total": total,
                "percentage": (completed / total * 100) if total > 0 else 0
            }
        
        return {"completed": 0, "total": 0, "percentage": 0}
    
    async def send_async(self, target: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send async message to target module."""
        # For now, just store the message
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("""
            INSERT INTO messages (source, target, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (self.module_name, target, json.dumps(message), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return {"status": "sent", "id": datetime.now().timestamp()}
    
    def send_message(self, source: str, target: str, data: Dict[str, Any]) -> str:
        """Send a message from source to target."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (source, target, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (source, target, json.dumps(data), datetime.now().isoformat()))
        msg_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return str(msg_id)
    
    def get_messages(self, target: str) -> list:
        """Get messages for a target module."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.execute("""
            SELECT id, source, content, timestamp FROM messages
            WHERE target = ?
            ORDER BY timestamp DESC
        """, (target,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                "id": row[0],
                "source": row[1],
                "data": json.loads(row[2]),
                "timestamp": row[3]
            })
        
        conn.close()
        return messages


class SchemaNegotiator:
    """Schema negotiation helper."""
    
    def __init__(self):
        pass
    
    def negotiate(self, source_schema: Dict[str, Any], target_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Negotiate between two schemas."""
        # Simple merge for now
        merged = {
            "type": "object",
            "properties": {}
        }
        
        # Merge properties from both schemas
        if "properties" in source_schema:
            merged["properties"].update(source_schema["properties"])
        if "properties" in target_schema:
            merged["properties"].update(target_schema["properties"])
        
        return merged


from .graph_backend import GraphBackend
from .graph_communicator import GraphModuleCommunicator
from .arango_expert import ArangoExpert

__version__ = "0.4.0"
__all__ = ["ModuleCommunicator", "SchemaNegotiator", "GraphBackend", "GraphModuleCommunicator", "ArangoExpert"]