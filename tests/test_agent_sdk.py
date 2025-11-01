"""Test Claude Agent SDK integration."""

import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions


async def test_simple_query():
    """Test a simple query using the Agent SDK."""
    print("\n🧪 Testing Claude Agent SDK...")
    print("=" * 60)

    prompt = "What is 2 + 2? Just give the answer, nothing else."

    print(f"\n📝 Query: {prompt}")
    print("\n💬 Streaming Response:")
    print("-" * 60)

    full_response = []
    session_id = None
    total_cost = 0.0
    total_tokens = 0

    try:
        async for message in query(prompt=prompt):
            msg_type = type(message).__name__

            if msg_type == 'SystemMessage':
                session_id = message.data.get('session_id')
                print(f"\n🔧 System initialized (session: {session_id[:8]}...)")

            elif msg_type == 'AssistantMessage':
                # Extract text from content blocks
                for content in message.content:
                    if hasattr(content, 'text'):
                        print(f"\n💬 {content.text}")
                        full_response.append(content.text)
                    elif hasattr(content, 'name'):  # Tool use
                        print(f"\n🔧 Tool: {content.name}")

            elif msg_type == 'ResultMessage':
                total_cost = message.total_cost_usd
                usage = message.usage
                total_tokens = usage['input_tokens'] + usage['output_tokens']
                print(f"\n📊 Complete!")
                print(f"   Duration: {message.duration_ms}ms")
                print(f"   Tokens: {total_tokens} (in: {usage['input_tokens']}, out: {usage['output_tokens']})")
                print(f"   Cost: ${total_cost:.6f}")

        print("\n" + "-" * 60)
        print("\n✅ Agent SDK test successful!")
        print(f"📝 Response: {''.join(full_response)}")

        return True

    except Exception as e:
        print(f"\n❌ Agent SDK test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_with_options():
    """Test with custom options."""
    print("\n\n🧪 Testing with ClaudeAgentOptions...")
    print("=" * 60)

    options = ClaudeAgentOptions(
        system_prompt="You are a helpful math tutor. Be concise.",
        permission_mode="bypassPermissions",  # Auto-approve tools for testing
        cwd="/Users/josh/brain/brain-cli"
    )

    prompt = "What is 5 * 8?"

    print(f"\n📝 Query: {prompt}")
    print("\n💬 Response:")
    print("-" * 60)

    try:
        async for message in query(prompt=prompt, options=options):
            if type(message).__name__ == 'AssistantMessage':
                for content in message.content:
                    if hasattr(content, 'text'):
                        print(content.text)

        print("-" * 60)
        print("\n✅ Options test successful!")

        return True

    except Exception as e:
        print(f"\n❌ Options test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🧠 Claude Agent SDK Integration Tests")
    print("=" * 60)

    results = []

    # Test 1: Simple query
    results.append(await test_simple_query())

    # Test 2: With options
    results.append(await test_with_options())

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60 + "\n")

    return all(results)


if __name__ == '__main__':
    success = asyncio.run(main())
    exit(0 if success else 1)
