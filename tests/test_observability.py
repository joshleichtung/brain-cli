"""Test observability system (hooks and event storage)."""

import asyncio
import os
import shutil
from datetime import datetime
from brain.observability import (
    EventType,
    get_hooks,
    get_event_store,
    AgentEvent,
    ToolEvent
)


async def test_hook_system():
    """Test hook subscription and emission."""
    print("\n🧪 Testing Observability - Hook System")
    print("=" * 60)

    hooks = get_hooks()
    received_events = []

    # Subscribe to agent events
    def on_agent_spawned(event):
        received_events.append(event)
        print(f"   📨 Received: {event.event_type.value}")

    hooks.subscribe(EventType.AGENT_SPAWNED, on_agent_spawned)

    # Emit event
    await hooks.agent_spawned(
        agent_id="test-agent-123",
        agent_name="claude-code",
        task="Test task",
        workspace_path="/tmp/test",
        project="test-project"
    )

    # Verify event received
    assert len(received_events) == 1, "Should receive 1 event"
    event = received_events[0]
    assert event.agent_id == "test-agent-123"
    assert event.event_type == EventType.AGENT_SPAWNED

    print(f"\n✅ Hook system works!")
    print(f"   Event type: {event.event_type.value}")
    print(f"   Agent ID: {event.agent_id}")

    # Cleanup
    hooks.unsubscribe(EventType.AGENT_SPAWNED, on_agent_spawned)

    return True


async def test_event_storage():
    """Test storing events to database."""
    print("\n\n🧪 Testing Observability - Event Storage")
    print("=" * 60)

    # Clean database
    db_path = '/tmp/brain-test-observability/events.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    store = get_event_store()
    store.db_path = db_path
    store._init_database()

    # Create and store an event
    event = AgentEvent(
        event_type=EventType.AGENT_COMPLETED,
        timestamp=datetime.now(),
        project="test-project",
        metadata={"test": "data"},
        agent_id="test-agent-456",
        agent_name="claude-code",
        task="Calculate 2+2",
        workspace_path="/tmp/test",
        tokens_used=100,
        cost=0.003,
        time_taken=5.2,
        response="4"
    )

    store.store_event(event)

    print(f"\n✅ Stored event to database")

    # Query events
    events = store.get_events(
        event_type=EventType.AGENT_COMPLETED,
        project="test-project"
    )

    assert len(events) == 1, "Should have 1 event"
    retrieved = events[0]
    assert retrieved['agent_id'] == "test-agent-456"
    assert retrieved['tokens_used'] == 100

    print(f"✅ Retrieved event from database")
    print(f"   Agent: {retrieved['agent_name']}")
    print(f"   Tokens: {retrieved['tokens_used']}")
    print(f"   Cost: ${retrieved['cost']}")

    # Test project stats
    stats = store.get_project_stats("test-project")
    print(f"\n✅ Project stats:")
    print(f"   Completed: {stats['completed']}")
    print(f"   Total cost: ${stats['total_cost']}")

    # Cleanup
    shutil.rmtree('/tmp/brain-test-observability', ignore_errors=True)

    return True


async def test_integrated_hooks_and_storage():
    """Test that hooks automatically store events."""
    print("\n\n🧪 Testing Observability - Integrated Hooks + Storage")
    print("=" * 60)

    # Clean database
    db_path = '/tmp/brain-test-observability/events.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    store = get_event_store()
    store.db_path = db_path
    store._init_database()

    # Subscribe database subscriber
    from brain.observability.subscribers import DatabaseEventSubscriber
    subscriber = DatabaseEventSubscriber()
    subscriber.store = store

    hooks = get_hooks()
    hooks.subscribe(EventType.AGENT_SPAWNED, subscriber.handle_event)

    # Emit event
    await hooks.agent_spawned(
        agent_id="integrated-test-789",
        agent_name="claude-code",
        task="Test integration",
        workspace_path="/tmp/test",
        project="integration-project"
    )

    # Small delay for async operations
    await asyncio.sleep(0.1)

    # Query events
    events = store.get_events(project="integration-project")
    assert len(events) == 1, "Should have 1 event automatically stored"

    print(f"\n✅ Event automatically stored via hook!")
    print(f"   Events in DB: {len(events)}")
    print(f"   Agent ID: {events[0]['agent_id']}")

    # Cleanup
    hooks.unsubscribe(EventType.AGENT_SPAWNED, subscriber.handle_event)
    shutil.rmtree('/tmp/brain-test-observability', ignore_errors=True)

    return True


async def test_agent_timeline():
    """Test retrieving agent timeline."""
    print("\n\n🧪 Testing Observability - Agent Timeline")
    print("=" * 60)

    # Clean database
    db_path = '/tmp/brain-test-observability/events.db'
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)

    store = get_event_store()
    store.db_path = db_path
    store._init_database()

    agent_id = "timeline-agent-001"

    # Store multiple events for same agent
    events_to_store = [
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
            tokens_used=50,
            cost=0.0015,
            time_taken=3.0,
            response="Done"
        )
    ]

    for event in events_to_store:
        store.store_event(event)

    # Get timeline
    timeline = store.get_agent_timeline(agent_id)

    assert len(timeline) == 3, "Should have 3 events in timeline"
    assert timeline[0]['event_type'] == 'agent_spawned'
    assert timeline[1]['event_type'] == 'agent_started'
    assert timeline[2]['event_type'] == 'agent_completed'

    print(f"\n✅ Agent timeline retrieved!")
    print(f"   Total events: {len(timeline)}")
    for i, event in enumerate(timeline, 1):
        print(f"   {i}. {event['event_type']}")

    # Cleanup
    shutil.rmtree('/tmp/brain-test-observability', ignore_errors=True)

    return True


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧠 Observability System Tests")
    print("=" * 60)

    results = []

    try:
        results.append(await test_hook_system())
    except Exception as e:
        print(f"\n❌ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(await test_event_storage())
    except Exception as e:
        print(f"\n❌ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(await test_integrated_hooks_and_storage())
    except Exception as e:
        print(f"\n❌ Test 3 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)

    try:
        results.append(await test_agent_timeline())
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
    success = asyncio.run(main())
    exit(0 if success else 1)
