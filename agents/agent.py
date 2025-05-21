# agent.py
from contextlib import AsyncExitStack
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams
from . import prompt

atlassian_agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o"),
    name='atlassian_agent',
    instruction=prompt.atlassian_agent__instruction,
    output_key="origin_wiki_content"
)

summarizer_agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o"),
    name='summarizer_agent',
    instruction=prompt.summarizer_agent_instruction,
    output_key="new_technical_specifications"
)

modify_agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o"),
    name='modify_agent',
    instruction=prompt.modify_agent,
    output_key="updated_wiki_content"
)

coordinator_agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o"),
    name='coordinator_agent',
    instruction=prompt.coordinator_agent_instruction,
    sub_agents=[summarizer_agent, atlassian_agent, modify_agent]
)


def find_agent(agent, targat_name):
    """A convenient function to find an agent from an existing agent graph."""
    result = None
    print("Matching...", agent.name)
    if agent.name == targat_name:
        return agent
    for sub_agent in agent.sub_agents:
        result = find_agent(sub_agent, targat_name)
        if result:
            break

    return result


async def get_tools_async():
    """Gets tools from MCP Server."""
    common_exit_stack = AsyncExitStack()

    remote_tools, _ = await MCPToolset.from_server(
        connection_params=SseServerParams(
            # TODO: IMPORTANT! Change the path below to your remote MCP Server path
            url="http://0.0.0.0:8081/sse"
        ),
        async_exit_stack=common_exit_stack
    )

    return remote_tools, common_exit_stack


async def create_agent():
    """Gets tools from MCP Server."""
    tools, exit_stack = await get_tools_async()
    agent = find_agent(coordinator_agent, "atlassian_agent")
    if agent:
        agent.tools.extend(tools)

    return coordinator_agent, exit_stack


root_agent = create_agent()
