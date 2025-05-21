# agent.py
from contextlib import AsyncExitStack
from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams


async def create_agent():
    """Gets tools from MCP Server."""
    common_exit_stack = AsyncExitStack()

    remote_tools, _ = await MCPToolset.from_server(
        connection_params=SseServerParams(
            # TODO: IMPORTANT! Change the path below to your remote MCP Server path
            url="http://0.0.0.0:8081/sse"
        ),
        async_exit_stack=common_exit_stack
    )

    agent_with_tools = LlmAgent(
        model=LiteLlm(model="openai/gpt-4o"),
        name='assistant',
        instruction=(
            'Help user interact with atlassian via tools'
        ),
        tools=[
            *remote_tools,
        ],
    )

    return agent_with_tools, common_exit_stack


root_agent = create_agent()
