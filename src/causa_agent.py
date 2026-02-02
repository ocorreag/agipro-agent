"""
CAUSA Agent - Conversational AI agent for social media content generation.

This agent uses LangGraph to provide a flexible, tool-based approach to
content creation. It can research topics, check past publications,
generate content, and create images - all based on conversation with the user.
"""

import os
from typing import Annotated, List, TypedDict, Literal, Optional
from datetime import datetime
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

# Local imports
from tools import ALL_TOOLS, WRITE_TOOLS
from path_manager import setup_environment
from safe_print import safe_print

load_dotenv()


# ============================================================================
# State Definition
# ============================================================================

class AgentState(TypedDict):
    """State for the CAUSA agent conversation."""
    messages: Annotated[List[BaseMessage], add_messages]
    pending_posts: List[dict]  # Posts awaiting image approval
    pending_image_request: Optional[dict]  # Image generation waiting for confirmation


# ============================================================================
# System Prompt
# ============================================================================

def get_system_prompt():
    """Generate system prompt with current date."""
    from datetime import datetime

    current_date = datetime.now()
    date_str = current_date.strftime("%Y-%m-%d")
    day_names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    month_names = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                   "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

    day_name = day_names[current_date.weekday()]
    month_name = month_names[current_date.month - 1]
    formatted_date = f"{day_name} {current_date.day} de {month_name} de {current_date.year}"

    return f"""You are the CAUSA Agent - an AI assistant for the Colectivo Ambiental de Usaca (CAUSA), an environmental and social collective based in Bogotá, Colombia.

## IMPORTANT: Current Date
**Today is: {formatted_date} ({date_str})**

When creating content, ALWAYS use dates relative to TODAY ({date_str}):
- "Next week" means the week starting from {date_str}
- "Tomorrow" means the day after {date_str}
- Ignore dates from old files - they are historical records, not the current date

## CRITICAL: Ephemerides Date Validation
When using ephemerides (historical events), you MUST:
1. VERIFY that the ephemeride's day and month match the publication date
2. Example: If creating a post for February 3rd, ONLY use ephemerides that happened on February 3rd (any year)
3. NEVER use an ephemeride from a different day/month - this is a serious error
4. If unsure about an ephemeride's date, DO NOT use it - choose a different topic instead

## Your Role
You help create engaging social media content that promotes:
- Environmental awareness and conservation
- Animal rights and welfare
- Human rights and social justice
- Sustainable urban development
- Local culture and historical memory
- Community education and participation

## Available Tools
You have access to these tools:

**Research Tools:**
- `search_web`: Search for current news and information (use specific queries)
- `search_ephemerides`: Find historical events for specific dates
- `query_collective_memory`: Search the collective's documents and history
- `get_collective_themes`: Get an overview of the collective's focus areas
- `get_activities`: Get confirmed activities from the collective's calendar

**Publication Tools:**
- `read_past_publications`: Check recent posts to avoid repetition
- `save_draft_post`: Save a post as a draft (requires user approval first)
- `update_post_image_path`: Link a generated image to a post

**Image Tools:**
- `preview_image_prompt`: Preview the DALL-E prompt before generating
- `generate_image`: Create an image with DALL-E (only after user approval)
- `regenerate_image`: Regenerate an image with modifications based on user feedback

## Workflow Guidelines

1. **Before creating content:**
   - Use `get_current_date` if you need to verify today's date
   - ALWAYS use `read_past_publications` to check what has been posted recently
   - Use research tools to gather relevant information
   - Consider the collective's themes and values

2. **When creating a post:**
   - Present the draft to the user for approval
   - Include: fecha (date), titulo (title), imagen (image description), descripcion (content)
   - **For ephemerides**: VERIFY the historical event's day/month matches the post date
   - Wait for user confirmation before saving

3. **For images:**
   - Only generate images AFTER the user approves the post content
   - Use `preview_image_prompt` if the user wants to see the prompt first
   - The image description should be detailed and specific
   - If the user wants CHANGES to an image, use `regenerate_image` with their feedback
   - Remember the original image description so you can use it for regeneration

4. **Content style:**
   - Write in Spanish (the collective's primary language)
   - Include relevant hashtags
   - Use emojis appropriately
   - Keep a positive, hopeful, and educational tone
   - Be informative but also engaging

## Important Rules
- NEVER generate images without explicit user approval
- ALWAYS check past publications before suggesting new content
- Be proactive in researching before creating content
- Ask clarifying questions if the user's request is unclear
- Provide options when multiple approaches are possible

## Response Format
When presenting a draft post, format it clearly:

**Fecha:** [date]
**Título:** [title]
**Imagen:** [image description]
**Descripción:** [full post content with hashtags]

Then ask if the user wants to:
1. Approve and save the post
2. Generate the image
3. Make changes
"""


# ============================================================================
# Agent Creation
# ============================================================================

def create_causa_agent(model_name: str = "gpt-5.2"):
    """
    Create the CAUSA agent with all tools and conversation support.

    Args:
        model_name: The OpenAI model to use (default: gpt-4o-mini)

    Returns:
        A compiled LangGraph that can be invoked with messages.
    """

    # Create the LLM with tools bound
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.7,
        max_tokens=4096
    )

    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    # ========================================================================
    # Node Functions
    # ========================================================================

    def agent_node(state: AgentState) -> dict:
        """
        The main agent node that processes messages and decides actions.
        """
        messages = state["messages"]

        # Add system message with current date if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            system_prompt = get_system_prompt()  # Get prompt with current date
            messages = [SystemMessage(content=system_prompt)] + list(messages)

        # Get response from LLM
        response = llm_with_tools.invoke(messages)

        return {"messages": [response]}

    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        """
        Determine if we should continue to tools or end the conversation.
        """
        messages = state["messages"]
        last_message = messages[-1]

        # If the LLM made tool calls, continue to tool node
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        # Otherwise, end the turn (wait for user input)
        return "end"

    # ========================================================================
    # Build the Graph
    # ========================================================================

    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(ALL_TOOLS))

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )

    # Tools always return to agent
    workflow.add_edge("tools", "agent")

    # Compile with memory for conversation persistence
    memory = MemorySaver()
    agent = workflow.compile(checkpointer=memory)

    return agent


# ============================================================================
# Convenience Functions
# ============================================================================

def chat(agent, message: str, thread_id: str = "default") -> str:
    """
    Send a message to the agent and get a response.

    Args:
        agent: The compiled agent
        message: User message
        thread_id: Conversation thread ID for persistence

    Returns:
        The agent's response text
    """
    config = {"configurable": {"thread_id": thread_id}}

    result = agent.invoke(
        {"messages": [HumanMessage(content=message)]},
        config=config
    )

    # Get the last AI message
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage):
            return msg.content

    return "No response generated."


def stream_chat(agent, message: str, thread_id: str = "default"):
    """
    Stream a chat response from the agent.

    Args:
        agent: The compiled agent
        message: User message
        thread_id: Conversation thread ID

    Yields:
        Chunks of the response as they're generated
    """
    config = {"configurable": {"thread_id": thread_id}}

    for event in agent.stream(
        {"messages": [HumanMessage(content=message)]},
        config=config,
        stream_mode="values"
    ):
        if "messages" in event:
            last_msg = event["messages"][-1]
            if isinstance(last_msg, AIMessage) and last_msg.content:
                yield last_msg.content


def get_conversation_history(agent, thread_id: str = "default") -> List[dict]:
    """
    Get the conversation history for a thread.

    Args:
        agent: The compiled agent
        thread_id: Conversation thread ID

    Returns:
        List of message dictionaries with role and content
    """
    config = {"configurable": {"thread_id": thread_id}}

    try:
        state = agent.get_state(config)
        messages = state.values.get("messages", [])

        history = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})

        return history
    except Exception:
        return []


# ============================================================================
# CLI Interface (for testing)
# ============================================================================

def main():
    """Run the agent in interactive CLI mode."""
    setup_environment()

    print("\n" + "="*60)
    print("CAUSA Agent - Interactive Mode")
    print("="*60)
    print("\nType your messages to interact with the agent.")
    print("Commands:")
    print("  /quit or /exit - Exit the chat")
    print("  /clear - Clear conversation history")
    print("  /help - Show available commands")
    print("="*60 + "\n")

    agent = create_causa_agent()
    thread_id = f"cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["/quit", "/exit"]:
                print("\nGoodbye!")
                break

            if user_input.lower() == "/clear":
                thread_id = f"cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                print("\nConversation cleared.")
                continue

            if user_input.lower() == "/help":
                print("\nAvailable commands:")
                print("  /quit, /exit - Exit the chat")
                print("  /clear - Start a new conversation")
                print("  /help - Show this help message")
                print("\nYou can ask the agent to:")
                print("  - Create posts about specific topics")
                print("  - Search for news or ephemerides")
                print("  - Check past publications")
                print("  - Generate images for approved posts")
                continue

            print("\nAgent: ", end="", flush=True)

            # Stream the response
            full_response = ""
            for chunk in stream_chat(agent, user_input, thread_id):
                # Only print new content
                new_content = chunk[len(full_response):]
                print(new_content, end="", flush=True)
                full_response = chunk

            print()  # New line after response

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            continue


if __name__ == "__main__":
    main()
