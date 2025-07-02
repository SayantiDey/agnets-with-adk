from google.adk.agents import Agent

from .prompt import agent_prompt
from .tools.tools import brainstorming_tool, troubleshooting_tool, toolbox_tools


root_agent = Agent(
    model="gemini-2.5-flash",
    name="technical_assistant",
    instruction=agent_prompt,
    tools=[brainstorming_tool, troubleshooting_tool, *toolbox_tools],
)
