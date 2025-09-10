# Copyright OpenSearch Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from typing import Optional, Any, Dict
from fastmcp import FastMCP
from mcp_server_opensearch.clusters_information import load_clusters_from_yaml
from tools.tool_filter import get_tools
from tools.tool_generator import generate_tools_from_openapi
from tools.tools import TOOL_REGISTRY
from tools.config import apply_custom_tool_config
from tools.tool_params import (
    GetAllocationArgs,
    GetClusterStateArgs,
    GetIndexInfoArgs,
    GetIndexMappingArgs,
    GetIndexStatsArgs,
    GetLongRunningTasksArgs,
    CatNodesArgs,
    GetNodesArgs,
    GetNodesHotThreadsArgs,
    GetQueryInsightsArgs,
    GetSegmentsArgs,
    GetShardsArgs,
    ListIndicesArgs,
    SearchIndexArgs,
)
from tools.utils import is_tool_compatible
from opensearch.helper import (
    get_allocation,
    get_cluster_state,
    get_index,
    get_index_info,
    get_index_mapping,
    get_index_stats,
    get_long_running_tasks,
    get_nodes,
    get_nodes_info,
    get_nodes_hot_threads,
    get_opensearch_version,
    get_query_insights,
    get_segments,
    get_shards,
    list_indices,
    search_index,
)

# Global variables for configuration
_mode = 'single'
_profile = ''
_config_file_path = ''
_cli_tool_overrides = {}
_enabled_tools = {}

# Create FastMCP instance
mcp = FastMCP("opensearch-mcp-server")

def check_tool_compatibility(tool_name: str, opensearch_cluster_name: str = ''):
    """Check if a tool is compatible with the current OpenSearch version."""
    from tools.tool_params import baseToolArgs
    
    args = baseToolArgs(opensearch_cluster_name=opensearch_cluster_name)
    opensearch_version = get_opensearch_version(args)
    
    if not is_tool_compatible(opensearch_version, TOOL_REGISTRY[tool_name]):
        tool_display_name = TOOL_REGISTRY[tool_name].get('display_name', tool_name)
        min_version = TOOL_REGISTRY[tool_name].get('min_version', '')
        max_version = TOOL_REGISTRY[tool_name].get('max_version', '')

        version_info = (
            f'{min_version} to {max_version}'
            if min_version and max_version
            else f'{min_version} or later'
            if min_version
            else f'up to {max_version}'
            if max_version
            else None
        )

        error_message = f"Tool '{tool_display_name}' is not supported for this OpenSearch version (current version: {opensearch_version})."
        if version_info:
            error_message += f' Supported version: {version_info}.'

        raise Exception(error_message)

@mcp.tool
def list_indices(
    opensearch_cluster_name: str = '',
    index: str = '',
    include_detail: bool = True
) -> str:
    """
    Lists all indices in OpenSearch with full information including docs.count, docs.deleted, store.size, etc.
    If an index parameter is provided, returns detailed information about that specific index.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        index: The name of the index to get detailed information for. If provided, returns detailed information about this specific index instead of listing all indices.
        include_detail: Whether to include detailed information. When listing indices (no index specified), if False, returns only a pure list of index names. If True, returns full metadata. When a specific index is provided, detailed information (including mappings) will be returned.
    """
    check_tool_compatibility('ListIndexTool', opensearch_cluster_name)
    
    args = ListIndicesArgs(
        opensearch_cluster_name=opensearch_cluster_name,
        index=index,
        include_detail=include_detail
    )
    
    # If index is provided, always return detailed information for that specific index
    if args.index:
        index_info = get_index(args)
        formatted_info = json.dumps(index_info, indent=2)
        return f'Index information for {args.index}:\n{formatted_info}'

    # Otherwise, list all indices
    indices = list_indices(args)

    # If include_detail is False, return only pure list of index names
    if not args.include_detail:
        index_names = [
            item.get('index')
            for item in indices
            if isinstance(item, dict) and 'index' in item
        ]
        formatted_names = json.dumps(index_names, indent=2)
        return f'Indices:\n{formatted_names}'

    # include_detail is True: return full information
    formatted_indices = json.dumps(indices, indent=2)
    return f'All indices information:\n{formatted_indices}'

@mcp.tool
def get_index_mapping(opensearch_cluster_name: str = '', index: str = '') -> str:
    """
    Retrieves index mapping and setting information for an index in OpenSearch.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        index: The name of the index to get mapping information for
    """
    check_tool_compatibility('IndexMappingTool', opensearch_cluster_name)
    
    args = GetIndexMappingArgs(opensearch_cluster_name=opensearch_cluster_name, index=index)
    mapping = get_index_mapping(args)
    formatted_mapping = json.dumps(mapping, indent=2)
    return f'Mapping for {args.index}:\n{formatted_mapping}'

@mcp.tool
def search_index_tool(opensearch_cluster_name: str = '', index: str = '', query: Any = None) -> str:
    """
    Searches an index using a query written in query domain-specific language (DSL) in OpenSearch.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        index: The name of the index to search in
        query: The search query in OpenSearch query DSL format
    """
    check_tool_compatibility('SearchIndexTool', opensearch_cluster_name)
    
    args = SearchIndexArgs(opensearch_cluster_name=opensearch_cluster_name, index=index, query=query)
    result = search_index(args)
    formatted_result = json.dumps(result, indent=2)
    return f'Search results from {args.index}:\n{formatted_result}'

@mcp.tool
def get_shards(opensearch_cluster_name: str = '', index: str = '') -> str:
    """
    Gets information about shards in OpenSearch.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        index: The name of the index to get shard information for
    """
    check_tool_compatibility('GetShardsTool', opensearch_cluster_name)
    
    args = GetShardsArgs(opensearch_cluster_name=opensearch_cluster_name, index=index)
    result = get_shards(args)

    if isinstance(result, dict) and 'error' in result:
        return f'Error getting shards: {result["error"]}'
        
    formatted_text = 'index | shard | prirep | state | docs | store | ip | node\n'

    # Format each shard row
    for shard in result:
        formatted_text += f'{shard["index"]} | '
        formatted_text += f'{shard["shard"]} | '
        formatted_text += f'{shard["prirep"]} | '
        formatted_text += f'{shard["state"]} | '
        formatted_text += f'{shard["docs"]} | '
        formatted_text += f'{shard["store"]} | '
        formatted_text += f'{shard["ip"]} | '
        formatted_text += f'{shard["node"]}\n'

    return formatted_text

@mcp.tool
def get_cluster_state(
    opensearch_cluster_name: str = '',
    metric: Optional[str] = None,
    index: Optional[str] = None
) -> str:
    """
    Gets the current state of the cluster including node information, index settings, and more.
    Can be filtered by specific metrics and indices.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        metric: Limit the information returned to the specified metrics. Options include: _all, blocks, metadata, nodes, routing_table, routing_nodes, master_node, version
        index: Limit the information returned to the specified indices
    """
    check_tool_compatibility('GetClusterStateTool', opensearch_cluster_name)
    
    args = GetClusterStateArgs(
        opensearch_cluster_name=opensearch_cluster_name,
        metric=metric,
        index=index
    )
    result = get_cluster_state(args)
    
    # Format the response for better readability
    formatted_result = json.dumps(result, indent=2)
    
    # Create response message based on what was requested
    message = "Cluster state information"
    if args.metric:
        message += f" for metric: {args.metric}"
    if args.index:
        message += f", filtered by index: {args.index}"
        
    return f'{message}:\n{formatted_result}'

@mcp.tool
def get_segments(opensearch_cluster_name: str = '', index: Optional[str] = None) -> str:
    """
    Gets information about Lucene segments in indices, including memory usage, document counts, and segment sizes.
    Can be filtered by specific indices.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        index: Limit the information returned to the specified indices
    """
    check_tool_compatibility('GetSegmentsTool', opensearch_cluster_name)
    
    args = GetSegmentsArgs(opensearch_cluster_name=opensearch_cluster_name, index=index)
    result = get_segments(args)
    
    if isinstance(result, dict) and 'error' in result:
        return f'Error getting segments: {result["error"]}'
    
    # Create a formatted table for better readability
    formatted_text = 'index | shard | prirep | segment | generation | docs.count | docs.deleted | size | memory.bookkeeping | memory.vectors | memory.docvalues | memory.terms | version\n'
    
    # Format each segment row
    for segment in result:
        formatted_text += f'{segment.get("index", "N/A")} | '
        formatted_text += f'{segment.get("shard", "N/A")} | '
        formatted_text += f'{segment.get("prirep", "N/A")} | '
        formatted_text += f'{segment.get("segment", "N/A")} | '
        formatted_text += f'{segment.get("generation", "N/A")} | '
        formatted_text += f'{segment.get("docs.count", "N/A")} | '
        formatted_text += f'{segment.get("docs.deleted", "N/A")} | '
        formatted_text += f'{segment.get("size", "N/A")} | '
        formatted_text += f'{segment.get("memory.bookkeeping", "N/A")} | '
        formatted_text += f'{segment.get("memory.vectors", "N/A")} | '
        formatted_text += f'{segment.get("memory.docvalues", "N/A")} | '
        formatted_text += f'{segment.get("memory.terms", "N/A")} | '
        formatted_text += f'{segment.get("version", "N/A")}\n'
    
    return formatted_text

@mcp.tool
def cat_nodes(
    opensearch_cluster_name: str = '',
    metrics: Optional[str] = None
) -> str:
    """
    Lists node-level information, including node roles and load metrics.
    Gets information about nodes metrics in the OpenSearch cluster.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        metrics: A comma-separated list of metrics to display
    """
    check_tool_compatibility('CatNodesTool', opensearch_cluster_name)
    
    args = CatNodesArgs(opensearch_cluster_name=opensearch_cluster_name, metrics=metrics)
    result = get_nodes(args)
    
    if isinstance(result, dict) and 'error' in result:
        return f'Error getting nodes information: {result["error"]}'
    
    # Format the response
    formatted_result = json.dumps(result, indent=2)
    return f'Nodes information:\n{formatted_result}'

@mcp.tool  
def get_index_info(opensearch_cluster_name: str = '', index: str = '') -> str:
    """
    Gets detailed information about an index including mappings, settings, and aliases.
    Supports wildcards in index names.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        index: The name of the index to get information for
    """
    check_tool_compatibility('GetIndexInfoTool', opensearch_cluster_name)
    
    args = GetIndexInfoArgs(opensearch_cluster_name=opensearch_cluster_name, index=index)
    result = get_index_info(args)
    formatted_result = json.dumps(result, indent=2)
    return f'Index information for {args.index}:\n{formatted_result}'

@mcp.tool
def get_index_stats(
    opensearch_cluster_name: str = '',
    index: str = '',
    metric: Optional[str] = None
) -> str:
    """
    Gets statistics about an index including document count, store size, indexing and search performance metrics.
    Can be filtered to specific metrics.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        index: The name of the index to get statistics for
        metric: Limit the statistics returned to the specified metrics
    """
    check_tool_compatibility('GetIndexStatsTool', opensearch_cluster_name)
    
    args = GetIndexStatsArgs(
        opensearch_cluster_name=opensearch_cluster_name,
        index=index,
        metric=metric
    )
    result = get_index_stats(args)
    formatted_result = json.dumps(result, indent=2)
    return f'Index statistics for {args.index}:\n{formatted_result}'

@mcp.tool
def get_query_insights(opensearch_cluster_name: str = '') -> str:
    """
    Gets query insights from the /_insights/top_queries endpoint, showing information about query patterns and performance.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
    """
    check_tool_compatibility('GetQueryInsightsTool', opensearch_cluster_name)
    
    args = GetQueryInsightsArgs(opensearch_cluster_name=opensearch_cluster_name)
    result = get_query_insights(args)
    formatted_result = json.dumps(result, indent=2)
    return f'Query insights:\n{formatted_result}'

@mcp.tool
def get_nodes_hot_threads(opensearch_cluster_name: str = '') -> str:
    """
    Gets information about hot threads in the cluster nodes from the /_nodes/hot_threads endpoint.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
    """
    check_tool_compatibility('GetNodesHotThreadsTool', opensearch_cluster_name)
    
    args = GetNodesHotThreadsArgs(opensearch_cluster_name=opensearch_cluster_name)
    result = get_nodes_hot_threads(args)
    return f'Hot threads information:\n{result}'

@mcp.tool
def get_allocation(opensearch_cluster_name: str = '') -> str:
    """
    Gets information about shard allocation across nodes in the cluster from the /_cat/allocation endpoint.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
    """
    check_tool_compatibility('GetAllocationTool', opensearch_cluster_name)
    
    args = GetAllocationArgs(opensearch_cluster_name=opensearch_cluster_name)
    result = get_allocation(args)
    
    if isinstance(result, dict) and 'error' in result:
        return f'Error getting allocation information: {result["error"]}'
    
    formatted_result = json.dumps(result, indent=2)
    return f'Allocation information:\n{formatted_result}'

@mcp.tool
def get_long_running_tasks(
    opensearch_cluster_name: str = '',
    limit: Optional[int] = 10
) -> str:
    """
    Gets information about long-running tasks in the cluster, sorted by running time in descending order.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        limit: The maximum number of tasks to return
    """
    check_tool_compatibility('GetLongRunningTasksTool', opensearch_cluster_name)
    
    args = GetLongRunningTasksArgs(
        opensearch_cluster_name=opensearch_cluster_name,
        limit=limit
    )
    result = get_long_running_tasks(args)
    formatted_result = json.dumps(result, indent=2)
    return f'Long running tasks:\n{formatted_result}'

@mcp.tool
def get_nodes_detail(
    opensearch_cluster_name: str = '',
    node_id: Optional[str] = None,
    metric: Optional[str] = None
) -> str:
    """
    Gets detailed information about nodes in the OpenSearch cluster, including static information like host system details,
    JVM info, processor type, node settings, thread pools, installed plugins, and more.
    Can be filtered by specific nodes and metrics.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        node_id: A comma-separated list of node IDs or names to limit the returned information
        metric: Limit the information returned to the specified metrics
    """
    check_tool_compatibility('GetNodesTool', opensearch_cluster_name)
    
    args = GetNodesArgs(
        opensearch_cluster_name=opensearch_cluster_name,
        node_id=node_id,
        metric=metric
    )
    result = get_nodes_info(args)
    formatted_result = json.dumps(result, indent=2)
    return f'Detailed nodes information:\n{formatted_result}'

# Dynamic tools generated from OpenAPI spec
@mcp.tool
def cluster_health(opensearch_cluster_name: str = '', index: Optional[str] = None) -> str:
    """
    Returns basic information about the health of the cluster.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        index: Limit health reporting to a specific index
    """
    from opensearch.client import initialize_client
    from tools.tool_params import baseToolArgs
    
    args = baseToolArgs(opensearch_cluster_name=opensearch_cluster_name)
    client = initialize_client(args)
    
    if index:
        result = client.cluster.health(index=index)
    else:
        result = client.cluster.health()
    
    formatted_result = json.dumps(result, indent=2)
    return f'Cluster health:\n{formatted_result}'

@mcp.tool
def count_documents(
    opensearch_cluster_name: str = '',
    index: Optional[str] = None,
    body: Optional[Any] = None
) -> str:
    """
    Returns number of documents matching a query.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        index: The name of the index to count documents in
        body: Query in JSON format to filter documents
    """
    from opensearch.client import initialize_client
    from tools.tool_params import baseToolArgs
    
    args = baseToolArgs(opensearch_cluster_name=opensearch_cluster_name)
    client = initialize_client(args)
    
    kwargs = {}
    if index:
        kwargs['index'] = index
    if body:
        kwargs['body'] = body
    
    result = client.count(**kwargs)
    formatted_result = json.dumps(result, indent=2)
    return f'Document count:\n{formatted_result}'

@mcp.tool
def explain_document(
    opensearch_cluster_name: str = '',
    index: str = '',
    id: str = '',
    body: Any = None
) -> str:
    """
    Returns information about why a specific document matches (or doesn't match) a query.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        index: The name of the index to retrieve the document from
        id: The document ID to explain
        body: Query in JSON format to explain against the document
    """
    from opensearch.client import initialize_client
    from tools.tool_params import baseToolArgs
    
    args = baseToolArgs(opensearch_cluster_name=opensearch_cluster_name)
    client = initialize_client(args)
    
    result = client.explain(index=index, id=id, body=body)
    formatted_result = json.dumps(result, indent=2)
    return f'Explain result for document {id}:\n{formatted_result}'

@mcp.tool
def msearch(
    opensearch_cluster_name: str = '',
    index: Optional[str] = None,
    body: Any = None
) -> str:
    """
    Allows to execute several search operations in one request.
    
    Args:
        opensearch_cluster_name: The name of the OpenSearch cluster
        index: Default index to search in
        body: Multi-search request body in NDJSON format
    """
    from opensearch.client import initialize_client
    from tools.tool_params import baseToolArgs
    
    args = baseToolArgs(opensearch_cluster_name=opensearch_cluster_name)
    client = initialize_client(args)
    
    # Process body for msearch - convert array to NDJSON if needed
    if isinstance(body, list):
        processed_body = ''.join(json.dumps(item) + '\n' for item in body)
    elif isinstance(body, str):
        try:
            parsed = json.loads(body)
            if isinstance(parsed, list):
                processed_body = ''.join(json.dumps(item) + '\n' for item in parsed)
            else:
                processed_body = body if body.endswith('\n') else body + '\n'
        except json.JSONDecodeError:
            processed_body = body if body.endswith('\n') else body + '\n'
    else:
        processed_body = body
    
    kwargs = {'body': processed_body}
    if index:
        kwargs['index'] = index
    
    result = client.msearch(**kwargs)
    formatted_result = json.dumps(result, indent=2)
    return f'Multi-search results:\n{formatted_result}'

async def initialize_server(
    mode: str = 'single',
    profile: str = '',
    config_file_path: str = '',
    cli_tool_overrides: dict = None,
) -> None:
    """Initialize the server with configuration."""
    global _mode, _profile, _config_file_path, _cli_tool_overrides, _enabled_tools
    
    _mode = mode
    _profile = profile
    _config_file_path = config_file_path
    _cli_tool_overrides = cli_tool_overrides or {}
    
    # Set the global profile if provided
    if profile:
        from opensearch.client import set_profile
        set_profile(profile)

    # Load clusters from YAML file
    if mode == 'multi':
        load_clusters_from_yaml(config_file_path)

    # Call tool generator
    await generate_tools_from_openapi()
    
    # Apply custom tool config (custom name and description)
    customized_registry = apply_custom_tool_config(
        TOOL_REGISTRY, config_file_path, cli_tool_overrides
    )
    
    # Get enabled tools (tool filter)
    _enabled_tools = get_tools(
        tool_registry=customized_registry, mode=mode, config_file_path=config_file_path
    )
    logging.info(f'Enabled tools: {list(_enabled_tools.keys())}')

def get_mcp_server():
    """Get the configured FastMCP server instance."""
    return mcp

async def serve_fastmcp(
    mode: str = 'single',
    profile: str = '',
    config_file_path: str = '',
    cli_tool_overrides: dict = None,
) -> None:
    """Serve using FastMCP."""
    try:
        # Initialize the server configuration
        await initialize_server(mode, profile, config_file_path, cli_tool_overrides)
        
        # Get the FastMCP server instance
        mcp_server = get_mcp_server()
        
        # Run the FastMCP server - FastMCP handles stdio automatically
        await mcp_server.run()
        
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
    except Exception as e:
        logging.error(f"Server error: {e}")
        raise
