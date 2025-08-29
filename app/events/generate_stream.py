import json

def create_sse_event(data: dict) -> str:
    """Create a properly formatted SSE event"""
    json_data = json.dumps(data)
    return f"data: {json_data}\n\n"