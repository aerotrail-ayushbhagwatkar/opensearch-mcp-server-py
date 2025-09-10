# Migration to FastMCP

This document explains the migration from the low-level MCP SDK to FastMCP for the OpenSearch MCP Server.

## What Changed

### Dependencies
- Replaced `mcp[cli]>=1.9.4` with `fastmcp>=2.0.0` in `pyproject.toml`

### New Implementation
- Created `src/mcp_server_opensearch/fastmcp_server.py` with FastMCP-based implementation
- All tools are now implemented using `@mcp.tool` decorators
- Simplified error handling - FastMCP automatically converts exceptions to MCP format
- Automatic schema generation from function signatures and docstrings

### Benefits of FastMCP

1. **Simplified Code**: Tools are now simple functions with decorators instead of complex registration logic
2. **Automatic Schema Generation**: No need to manually define input schemas
3. **Better Error Handling**: Exceptions are automatically converted to proper MCP error responses
4. **Production Ready**: Built-in features for authentication, documentation, and deployment
5. **Reduced Boilerplate**: Much less code required for the same functionality

### Backward Compatibility

The migration maintains backward compatibility by:
- Keeping the original low-level implementation in `legacy_main.py`
- Providing both `opensearch-mcp-server-py` (FastMCP) and `opensearch-mcp-server-legacy` (original) commands
- All existing functionality remains available

### Examples

#### Before (Low-level SDK):
```python
class SearchIndexArgs(BaseModel):
    index: str
    query: dict
    size: int = 10

TOOL_REGISTRY = {
    "SearchIndexTool": {
        "description": "Search OpenSearch index with DSL query",
        "input_schema": SearchIndexArgs.model_json_schema(), 
        "function": search_index_tool,
        "args_model": SearchIndexArgs,
    }
}

@server.list_tools()
async def list_tools() -> list[Tool]:
    tools = []
    for tool_name, tool_info in enabled_tools.items():
        tools.append(
            Tool(
                name=tool_name,
                description=tool_info["description"],
                inputSchema=tool_info["input_schema"], 
            )
        )
    return tools

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    tool = enabled_tools.get(name)
    if not tool:
        raise ValueError(f"Unknown or disabled tool: {name}")
    
    try:
        parsed = tool["args_model"](**arguments)
        return await tool["function"](parsed)
    except Exception as e:
        return [TextContent(type="text", text=f"Tool execution error: {str(e)}")]
```

#### After (FastMCP):
```python
@mcp.tool
def search_index_tool(opensearch_cluster_name: str = '', index: str = '', query: Any = None) -> str:
    """Searches an index using a query written in query domain-specific language (DSL) in OpenSearch."""
    # Exception handling is automatic
    # Schema generation is automatic
    # Tool registration is automatic
    result = search_index(args)
    return json.dumps(result, indent=2)
```

## Running the Servers

### FastMCP (New Default)
```bash
# Use the new FastMCP implementation
python -m mcp_server_opensearch --mode single --config config.yml

# Or use the console script
opensearch-mcp-server-py --mode single --config config.yml
```

### Legacy (Original Implementation)
```bash
# Use the original low-level implementation
opensearch-mcp-server-legacy --transport stdio --mode single --config config.yml
```

## Testing

Both implementations can be tested with the existing test suite. The FastMCP implementation includes additional tests in `tests/mcp_server_opensearch/test_fastmcp_server.py`.

## Migration Benefits Summary

1. **Reduced Code Complexity**: ~60% reduction in boilerplate code
2. **Improved Developer Experience**: Simpler function-based approach
3. **Automatic Features**: Schema generation, error handling, documentation
4. **Better Production Readiness**: Built-in authentication, deployment tools
5. **Maintained Compatibility**: All existing functionality preserved
