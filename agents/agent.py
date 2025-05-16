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

    # # Define individual agents
    # agent = LlmAgent(
    #     model=LiteLlm(model="openai/gpt-4o-mini"),
    #     name='assistant',
    #     instruction=(
    #         'Help user summarize conversation, document. Help user merging, combine document'
    #     ))

    # # Create parent agent and assign children via sub_agents
    # coordinator = LlmAgent(
    #     name="assistant",
    #     model=LiteLlm("openai/gpt-4o-mini"),
    #     description="I coordinate agent and agent_with_tools.",
    #     sub_agents=[  # Assign sub_agents here
    #         agent,
    #         agent_with_tools
    #     ]
    # )

    return agent_with_tools, common_exit_stack


root_agent = create_agent()
