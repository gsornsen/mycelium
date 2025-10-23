# Source: troubleshooting/discovery-coordination.md
# Line: 830
# Valid syntax: True
# Has imports: True
# Has assignments: True

# Solution 1: Use file references
# Before:
context = {
    "data": read_large_file()  # 50MB
}

# After:
context = {
    "data_path": "/path/to/large_file.txt",
    "data_format": "CSV",
    "row_count": 1000000
}

# Solution 2: Compress context
import gzip
import json
import base64

def compress_context(context):
    json_data = json.dumps(context).encode('utf-8')
    compressed = gzip.compress(json_data)
    return base64.b64encode(compressed).decode('utf-8')

def decompress_context(compressed):
    decoded = base64.b64decode(compressed.encode('utf-8'))
    decompressed = gzip.decompress(decoded)
    return json.loads(decompressed.decode('utf-8'))

# Use compressed context
compressed = compress_context(large_context)
result = handoff_to_agent(
    "agent",
    "task",
    context={"compressed_data": compressed}
)

# Solution 3: Stream large data
# Instead of passing all at once, stream in chunks
def stream_data_to_agent(agent_id, data_chunks):
    handoff_id = initiate_streaming_handoff(agent_id)

    for chunk in data_chunks:
        send_chunk(handoff_id, chunk)

    finalize_handoff(handoff_id)