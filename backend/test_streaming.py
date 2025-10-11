"""
Test script for streaming chat endpoint
Run with: python -m backend.test_streaming
"""
import asyncio
import aiohttp
import json
import sys


async def test_streaming_endpoint():
    """Test the streaming chat endpoint"""
    url = "http://localhost:8000/chat/message/stream"
    
    # Test message
    payload = {
        "message": "What is the main topic of my documents?",
        "conversation_id": None,
        "agent_id": None,
        "document_ids": None
    }
    
    print("Testing streaming endpoint...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nStreaming response:")
    print("-" * 80)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    print(f"Error: HTTP {response.status}")
                    text = await response.text()
                    print(f"Response: {text}")
                    return
                
                # Read SSE stream
                accumulated_text = ""
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    
                    if not line_str or not line_str.startswith('data: '):
                        continue
                    
                    # Parse SSE data
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_str)
                        
                        # Print token
                        if data.get('token'):
                            token = data['token']
                            accumulated_text += token
                            print(token, end='', flush=True)
                        
                        # Check if done
                        if data.get('done'):
                            print("\n" + "-" * 80)
                            print(f"\nStream completed!")
                            print(f"Message ID: {data.get('message_id')}")
                            print(f"Conversation ID: {data.get('conversation_id')}")
                            print(f"Sources: {len(data.get('sources', []))} sources")
                            
                            if data.get('error'):
                                print(f"Error: {data['error']}")
                            
                            break
                    
                    except json.JSONDecodeError as e:
                        print(f"\nJSON decode error: {e}")
                        print(f"Raw data: {data_str}")
                
                print(f"\n\nTotal characters received: {len(accumulated_text)}")
                
    except aiohttp.ClientError as e:
        print(f"\nConnection error: {e}")
        print("\nMake sure the backend server is running:")
        print("  cd backend && uvicorn main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def test_regular_endpoint():
    """Test the regular (non-streaming) chat endpoint for comparison"""
    url = "http://localhost:8000/chat/message"
    
    payload = {
        "message": "What is the main topic of my documents?",
        "conversation_id": None,
        "agent_id": None,
        "document_ids": None
    }
    
    print("\n\nTesting regular endpoint for comparison...")
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nResponse:")
    print("-" * 80)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    print(f"Error: HTTP {response.status}")
                    text = await response.text()
                    print(f"Response: {text}")
                    return
                
                data = await response.json()
                print(json.dumps(data, indent=2))
                print("-" * 80)
                print(f"\nRegular endpoint completed!")
                
    except Exception as e:
        print(f"\nError: {e}")


async def main():
    """Run tests"""
    print("=" * 80)
    print("Backend Streaming Chat Test")
    print("=" * 80)
    print()
    
    # Test streaming endpoint
    await test_streaming_endpoint()
    
    # Optionally test regular endpoint for comparison
    # await test_regular_endpoint()
    
    print("\n" + "=" * 80)
    print("Test completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

