"""Test FastAPI observability service."""

import asyncio
import os
import shutil
from fastapi.testclient import TestClient

from brain.observability.api import app
from brain.observability import get_event_store, get_hooks, EventType, AgentEvent
from datetime import datetime


client = TestClient(app)


def test_api_root():
    """Test API root endpoint."""
    print("\n🧪 Testing API - Root Endpoint")
    print("=" * 60)

    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data['service'] == "Brain CLI Observability API"
    assert 'endpoints' in data

    print(f"\n✅ API root works!")
    print(f"   Service: {data['service']}")
    print(f"   Endpoints: {list(data['endpoints'].keys())}")

    return True


def test_get_events():
    """Test GET /events endpoint."""
    print("\n\n🧪 Testing API - GET /events")
    print("=" * 60)

    # Clean database
    db_path = '/tmp/brain-test-api/events.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    store = get_event_store()
    store.db_path = db_path
    store._init_database()

    # Store some test events
    event = AgentEvent(
        event_type=EventType.AGENT_COMPLETED,
        timestamp=datetime.now(),
        project="test-api-project",
        metadata={},
        agent_id="api-test-agent",
        agent_name="claude-code",
        task="Test task",
        workspace_path="/tmp",
        tokens_used=100,
        cost=0.003,
        time_taken=5.0,
        response="Test response"
    )
    store.store_event(event)

    # Query via API
    response = client.get("/events?project=test-api-project")
    assert response.status_code == 200

    data = response.json()
    assert data['count'] == 1
    assert data['events'][0]['agent_id'] == "api-test-agent"

    print(f"\n✅ GET /events works!")
    print(f"   Events returned: {data['count']}")
    print(f"   Agent ID: {data['events'][0]['agent_id']}")

    # Cleanup
    shutil.rmtree('/tmp/brain-test-api', ignore_errors=True)

    return True


def test_project_stats():
    """Test GET /projects/{project}/stats endpoint."""
    print("\n\n🧪 Testing API - GET /projects/{project}/stats")
    print("=" * 60)

    # Clean database
    db_path = '/tmp/brain-test-api/events.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    store = get_event_store()
    store.db_path = db_path
    store._init_database()

    # Store events
    events = [
        AgentEvent(
            event_type=EventType.AGENT_SPAWNED,
            timestamp=datetime.now(),
            project="stats-project",
            metadata={},
            agent_id=f"agent-{i}",
            agent_name="claude-code",
            task="Test",
            workspace_path="/tmp"
        )
        for i in range(3)
    ]

    for event in events:
        store.store_event(event)

    # Store completed event
    completed = AgentEvent(
        event_type=EventType.AGENT_COMPLETED,
        timestamp=datetime.now(),
        project="stats-project",
        metadata={},
        agent_id="agent-1",
        agent_name="claude-code",
        task="Test",
        workspace_path="/tmp",
        tokens_used=150,
        cost=0.0045,
        time_taken=6.0,
        response="Done"
    )
    store.store_event(completed)

    # Query stats via API
    response = client.get("/projects/stats-project/stats")
    assert response.status_code == 200

    data = response.json()
    assert data['project'] == "stats-project"
    assert data['total_agents'] == 3
    assert data['completed'] == 1
    assert data['total_cost'] == 0.0045

    print(f"\n✅ GET /projects/{{project}}/stats works!")
    print(f"   Project: {data['project']}")
    print(f"   Total agents: {data['total_agents']}")
    print(f"   Completed: {data['completed']}")
    print(f"   Total cost: ${data['total_cost']}")

    # Cleanup
    shutil.rmtree('/tmp/brain-test-api', ignore_errors=True)

    return True


def test_agent_timeline():
    """Test GET /agents/{agent_id}/timeline endpoint."""
    print("\n\n🧪 Testing API - GET /agents/{agent_id}/timeline")
    print("=" * 60)

    # Clean database
    db_path = '/tmp/brain-test-api/events.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    store = get_event_store()
    store.db_path = db_path
    store._init_database()

    agent_id = "timeline-agent"

    # Store lifecycle events
    events = [
        AgentEvent(
            event_type=EventType.AGENT_SPAWNED,
            timestamp=datetime.now(),
            project="test",
            metadata={},
            agent_id=agent_id,
            agent_name="claude-code",
            task="Test",
            workspace_path="/tmp"
        ),
        AgentEvent(
            event_type=EventType.AGENT_STARTED,
            timestamp=datetime.now(),
            project="test",
            metadata={},
            agent_id=agent_id,
            agent_name="claude-code",
            task="Test",
            workspace_path="/tmp"
        ),
        AgentEvent(
            event_type=EventType.AGENT_COMPLETED,
            timestamp=datetime.now(),
            project="test",
            metadata={},
            agent_id=agent_id,
            agent_name="claude-code",
            task="Test",
            workspace_path="/tmp",
            tokens_used=100,
            cost=0.003,
            time_taken=5.0,
            response="Done"
        )
    ]

    for event in events:
        store.store_event(event)

    # Query timeline via API
    response = client.get(f"/agents/{agent_id}/timeline")
    assert response.status_code == 200

    data = response.json()
    assert data['agent_id'] == agent_id
    assert data['count'] == 3
    assert data['events'][0]['event_type'] == 'agent_spawned'

    print(f"\n✅ GET /agents/{{agent_id}}/timeline works!")
    print(f"   Agent ID: {data['agent_id']}")
    print(f"   Timeline events: {data['count']}")
    for i, event in enumerate(data['events'], 1):
        print(f"   {i}. {event['event_type']}")

    # Cleanup
    shutil.rmtree('/tmp/brain-test-api', ignore_errors=True)

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧠 FastAPI Observability API Tests")
    print("=" * 60)

    results = []

    try:
        results.append(test_api_root())
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(test_get_events())
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(test_project_stats())
    except Exception as e:
        print(f"\n❌ Test 3 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(test_agent_timeline())
    except Exception as e:
        print(f"\n❌ Test 4 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60 + "\n")

    return all(results)


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
