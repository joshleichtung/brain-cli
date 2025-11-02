"""
FastAPI observability service.

Provides HTTP and WebSocket endpoints for:
- Querying events
- Real-time event streaming
- Project analytics
- Agent timelines
"""

import asyncio
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .events import EventType, BaseEvent
from .storage import get_event_store
from .hooks import get_hooks


# Pydantic models for API

class EventQuery(BaseModel):
    """Query parameters for events."""
    event_type: Optional[str] = None
    project: Optional[str] = None
    agent_id: Optional[str] = None
    limit: int = 100
    offset: int = 0


class ProjectStatsResponse(BaseModel):
    """Project statistics response."""
    project: str
    total_agents: int
    completed: int
    failed: int
    total_cost: float
    total_tokens: int
    tool_usage: List[dict]


# FastAPI app

app = FastAPI(
    title="Brain CLI Observability API",
    description="Real-time observability and analytics for Brain CLI multi-agent orchestration",
    version="1.0.0"
)

# CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection manager

class ConnectionManager:
    """Manages WebSocket connections for real-time event streaming."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"⚠️  WebSocket send error: {e}")


manager = ConnectionManager()


# Subscribe to hooks and broadcast to WebSocket clients

async def broadcast_event(event: BaseEvent):
    """Broadcast event to all WebSocket clients."""
    await manager.broadcast(event.to_dict())


# Register hook subscriber for broadcasting
def register_websocket_subscriber():
    """Register WebSocket broadcaster to all event types."""
    hooks = get_hooks()
    for event_type in EventType:
        hooks.subscribe(event_type, broadcast_event)


# HTTP Endpoints

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "service": "Brain CLI Observability API",
        "version": "1.0.0",
        "endpoints": {
            "events": "/events",
            "projects": "/projects/{project}/stats",
            "agents": "/agents/{agent_id}/timeline",
            "websocket": "/ws"
        }
    }


@app.get("/events")
async def get_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    project: Optional[str] = Query(None, description="Filter by project"),
    agent_id: Optional[str] = Query(None, description="Filter by agent ID"),
    limit: int = Query(100, description="Maximum number of events"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    Get events from storage.

    Query parameters:
    - event_type: Filter by event type (e.g. 'agent_spawned')
    - project: Filter by project name
    - agent_id: Filter by agent ID
    - limit: Maximum events to return (default: 100)
    - offset: Pagination offset (default: 0)
    """
    store = get_event_store()

    # Convert event_type string to enum if provided
    event_type_enum = None
    if event_type:
        try:
            event_type_enum = EventType(event_type)
        except ValueError:
            return {"error": f"Invalid event_type: {event_type}"}

    events = store.get_events(
        event_type=event_type_enum,
        project=project,
        agent_id=agent_id,
        limit=limit,
        offset=offset
    )

    return {
        "events": events,
        "count": len(events),
        "limit": limit,
        "offset": offset
    }


@app.get("/projects/{project}/stats", response_model=ProjectStatsResponse)
async def get_project_stats(project: str):
    """
    Get aggregate statistics for a project.

    Returns:
    - total_agents: Total agents spawned
    - completed: Successfully completed agents
    - failed: Failed agents
    - total_cost: Total cost in USD
    - total_tokens: Total tokens used
    - tool_usage: Top 10 tools by usage count
    """
    store = get_event_store()
    stats = store.get_project_stats(project)

    return ProjectStatsResponse(
        project=project,
        **stats
    )


@app.get("/agents/{agent_id}/timeline")
async def get_agent_timeline(agent_id: str):
    """
    Get timeline of events for a specific agent.

    Returns events in chronological order from spawn to completion/failure.
    """
    store = get_event_store()
    timeline = store.get_agent_timeline(agent_id)

    return {
        "agent_id": agent_id,
        "events": timeline,
        "count": len(timeline)
    }


@app.get("/projects")
async def list_projects():
    """
    List all projects with event counts.
    """
    store = get_event_store()

    # Query distinct projects
    with store._get_connection() as conn:
        cursor = conn.execute("""
            SELECT project, COUNT(*) as event_count
            FROM events
            GROUP BY project
            ORDER BY event_count DESC
        """)
        projects = [dict(row) for row in cursor.fetchall()]

    return {
        "projects": projects,
        "count": len(projects)
    }


@app.delete("/projects/{project}/events")
async def clear_project_events(project: str):
    """
    Clear all events for a project.

    WARNING: This is destructive and cannot be undone.
    """
    store = get_event_store()
    store.clear_project_events(project)

    return {
        "message": f"Cleared all events for project: {project}",
        "project": project
    }


# WebSocket endpoint

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time event streaming.

    Clients connect and receive all events as they occur in real-time.
    """
    await manager.connect(websocket)

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "message": "Connected to Brain CLI observability stream"
        })

        # Keep connection alive
        while True:
            # Receive messages from client (for future commands)
            data = await websocket.receive_text()

            # Echo back (placeholder for future client commands)
            await websocket.send_json({
                "type": "echo",
                "data": data
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"⚠️  WebSocket error: {e}")
        manager.disconnect(websocket)


# Startup/shutdown events

@app.on_event("startup")
async def startup_event():
    """Initialize observability service on startup."""
    print("🚀 Starting Brain CLI Observability API...")
    register_websocket_subscriber()
    print("✅ WebSocket event broadcasting enabled")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("👋 Shutting down Brain CLI Observability API...")
