# Copyright OpenSearch Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock
from mcp_server_opensearch.fastmcp_server import (
    initialize_server,
    get_mcp_server,
    serve_fastmcp,
    mcp
)


class TestFastMCPServer:
    @pytest_asyncio.fixture
    async def mock_server_setup(self):
        """Provides mocked server setup for testing."""
        with (
            patch('mcp_server_opensearch.fastmcp_server.get_tools', return_value={}),
            patch('mcp_server_opensearch.fastmcp_server.generate_tools_from_openapi', return_value=None),
            patch('mcp_server_opensearch.fastmcp_server.load_clusters_from_yaml', return_value=None),
            patch('mcp_server_opensearch.fastmcp_server.apply_custom_tool_config', return_value={}),
        ):
            yield

    @pytest.mark.asyncio
    async def test_initialize_server(self, mock_server_setup):
        """Test server initialization."""
        await initialize_server(
            mode='single',
            profile='test-profile',
            config_file_path='test-config.yml',
            cli_tool_overrides={'key': 'value'}
        )

    def test_get_mcp_server(self):
        """Test getting the FastMCP server instance."""
        server = get_mcp_server()
        assert server is not None
        assert server.name == "opensearch-mcp-server"

    @pytest.mark.asyncio
    async def test_serve_fastmcp(self, mock_server_setup):
        """Test serving with FastMCP."""
        mock_mcp = Mock()
        mock_mcp.run = AsyncMock()
        
        with patch('mcp_server_opensearch.fastmcp_server.get_mcp_server', return_value=mock_mcp):
            await serve_fastmcp(
                mode='single',
                profile='test-profile',
                config_file_path='test-config.yml',
                cli_tool_overrides={'key': 'value'}
            )
            
            mock_mcp.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_serve_fastmcp_keyboard_interrupt(self, mock_server_setup):
        """Test serving with FastMCP handles KeyboardInterrupt."""
        mock_mcp = Mock()
        mock_mcp.run = AsyncMock(side_effect=KeyboardInterrupt())
        
        with patch('mcp_server_opensearch.fastmcp_server.get_mcp_server', return_value=mock_mcp):
            # Should not raise an exception
            await serve_fastmcp()

    @pytest.mark.asyncio
    async def test_serve_fastmcp_exception(self, mock_server_setup):
        """Test serving with FastMCP handles other exceptions."""
        mock_mcp = Mock()
        mock_mcp.run = AsyncMock(side_effect=Exception("Test error"))
        
        with patch('mcp_server_opensearch.fastmcp_server.get_mcp_server', return_value=mock_mcp):
            with pytest.raises(Exception, match="Test error"):
                await serve_fastmcp()

    @pytest.mark.asyncio
    async def test_tool_functionality(self, mock_server_setup):
        """Test that tools are properly registered."""
        # Check that the mcp server has tools registered
        server = get_mcp_server()
        
        # FastMCP uses decorators to register tools, so we can check if the tools exist
        # This is a basic test to ensure the server is properly configured
        assert hasattr(server, '_tools') or hasattr(server, 'tools') or callable(getattr(server, 'list_tools', None))
