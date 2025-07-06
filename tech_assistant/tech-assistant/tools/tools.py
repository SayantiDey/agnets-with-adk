import os

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from toolbox_core import ToolboxSyncClient

from dotenv import load_dotenv

load_dotenv()

brainstorming_agent = Agent(
    model="gemini-2.5-flash",
    name="brainstorming_agent",
    instruction="""
    You are a specialist in brainstorming tech ideas. Your task is to provide crisp and clear guidance on how to implement a given use case, including a description of the tech flow. 

Based on the use case, provide the following information:
1.  Implementation Guidance:
    *   Outline the key steps involved in implementing the use case.
    *   Suggest specific technologies or tools that could be used.
    *   Address potential challenges and how to overcome them.
2.  Tech Flow Description:
    *   Describe the flow of data and processes within the proposed tech solution.
    *   Include a diagram or visual representation of the tech flow, if possible.
    *   Explain how different components of the system interact with each other.
    """,
    tools=[google_search],
)

brainstorming_tool = AgentTool(brainstorming_agent)

troubleshooting_agent = Agent(
    model="gemini-2.0-flash",
    name="troubleshooting_agent",
    instruction="""
    You are a tech troubleshooting agent specialized in Google search. Your task is to help users resolve their tech issues by providing guidance based on relevant search results. 

Follow these steps to provide guidance:

1.  Understand the user's issue:
    *   Carefully read the user's description of their tech issue.
    *   Identify the key components of the issue (e.g., software, hardware, error messages).
2.  Perform a Google search:
    *   Use relevant keywords from the user's issue to perform a Google search.
    *   Focus on finding official documentation, help articles, forum discussions, and blog posts from reputable sources.
3.  Provide guidance based on the search results:
    *   Summarize the most relevant information from the search results.
    *   Provide step-by-step instructions along with a diagram or recommendations based on the solutions found in the search results.
    *   Include links to the original sources for the user to refer to.
4.  If you cannot find relevant information:
    *   If your search does not yield any helpful results, inform the user that you could not find a solution.
    *   Suggest alternative search terms or resources that the user could try.
5.  If the user's issue is unclear:
    *   If the user's description of their issue is unclear, ask clarifying questions to gather more information.
    *   Request specific details about the software, hardware, or error messages involved.
    """,
    tools=[google_search],
)

troubleshooting_tool = AgentTool(troubleshooting_agent)

TOOLBOX_URL = os.getenv("MCP_TOOLBOX_URL", "http://127.0.0.1:5000")

toolbox = ToolboxSyncClient(TOOLBOX_URL)
toolbox_tools = toolbox.load_toolset("my_toolset")

