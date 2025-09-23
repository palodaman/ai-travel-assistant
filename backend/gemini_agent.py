import os
import google.generativeai as genai
from typing import Dict, Any
from dotenv import load_dotenv
from agent_loop import AgentLoop

# Suppress gRPC ALTS warning for local development
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'

# Load environment variables from .env file in parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Get API key and configure genai
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GOOGLE_API_KEY)

FUNCTIONS = [
    {
        "name": "weather_tool",
        "description": "ALWAYS use this tool for ANY weather-related query, regardless of temporal words like 'today', 'now', 'current', 'tomorrow', 'this week'. This tool ALWAYS returns current/today's weather. Use for: 'weather in London', 'weather in London today', 'current weather in Paris', 'how's the weather now in Tokyo', 'what's the temperature today in Rome'. Optionally specify state/province and country for disambiguation.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
                "state": {"type": "string", "description": "Optional state or province name"},
                "country": {"type": "string", "description": "Optional country name"}
            },
            "required": ["city"],
        },
    },
    {
        "name": "currency_convert",
        "description": "ALWAYS use this tool when: user mentions ANY amount of money, asks about costs/prices/budgets in different countries, wonders how much money they need for travel, or mentions spending money abroad. Convert between currencies to show local equivalents. For example: 'How much will $1000 last in France' -> convert USD to EUR. 'What can I buy with 100 euros' -> might convert to user's currency.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "The amount to convert"},
                "from": {"type": "string", "description": "Source currency code (e.g., USD, EUR, GBP)"},
                "to": {"type": "string", "description": "Target currency code (e.g., EUR for France, GBP for UK, JPY for Japan)"},
            },
            "required": ["amount", "from", "to"],
        },
    },
    {
        "name": "wikipedia_search",
        "description": "ALWAYS use this tool when users ask about: tourist attractions, landmarks, cities, countries, historical sites, monuments, museums, cultural information, local customs, famous people, historical events, or ANY factual question about places or travel destinations. Provides up-to-date information with Wikipedia links for further reading. USE THIS for questions like 'tell me about X', 'what is X', 'history of X', 'attractions in X', etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The topic to search for on Wikipedia"},
                "sentences": {"type": "integer", "description": "Number of sentences to return in summary (default 3)"}
            },
            "required": ["query"],
        },
    },
]

model = genai.GenerativeModel(
    model_name=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
    tools=[{"function_declarations": FUNCTIONS}],
    system_instruction="""You are an AI travel assistant specializing in travel information, destinations, and trip planning.

CRITICAL TOOL USAGE RULES:

1. CURRENCY - ALWAYS USE currency_convert when:
   - User mentions ANY specific amount of money (e.g., "$1000", "500 euros", "¥10000")
   - User asks about costs, prices, or budgets in different countries
   - User asks "how much will X last me in [country]" - IMMEDIATELY convert to local currency
   - User mentions travel budgets or spending money abroad
   - ANY discussion of money across different countries/currencies

   Country to Currency Mapping:
   - France, Germany, Italy, Spain, Netherlands, etc. → EUR (Euro)
   - UK → GBP (British Pound)
   - Japan → JPY (Yen)
   - China → CNY (Yuan)
   - India → INR (Rupee)
   - Switzerland → CHF (Swiss Franc)
   - Canada → CAD (Canadian Dollar)
   - Australia → AUD (Australian Dollar)
   - Mexico → MXN (Mexican Peso)
   - Brazil → BRL (Brazilian Real)

2. WEATHER - ALWAYS USE weather_tool when:
   - User asks about weather, temperature, or climate
   - Planning outdoor activities or wondering what to pack
   - IGNORE temporal words like "today", "now", "current", "tomorrow" - the weather_tool ALWAYS returns current weather
   - Treat "What's the weather in London today?" EXACTLY the same as "What's the weather in London?"
   - DO NOT refuse to answer because of words like "today" or "now" - just use the weather_tool

3. WIKIPEDIA - ALWAYS USE wikipedia_search when:
   - User asks about places, attractions, landmarks, history, culture
   - Any factual information about destinations

IMPORTANT: Be PROACTIVE with currency conversion. If someone says "I have $1000 for my trip to France", immediately convert USD to EUR to show them the local equivalent. Don't wait for them to explicitly ask for conversion.

For questions like "How much will $1000 last me in France?":
1. First convert $1000 to EUR using currency_convert
2. Then provide context about costs in France
3. Give practical examples of what that amount can buy

CRITICAL WEATHER HANDLING:
- The weather_tool provides CURRENT weather data
- When users say "today", "now", "current", "at the moment", "right now" - these ALL mean current weather
- NEVER refuse to answer weather questions because of temporal words
- "Weather in Paris today" = "Weather in Paris" = "Current weather in Paris" → ALL use weather_tool
- If asked about future weather (tomorrow, next week), explain you provide current conditions and suggest checking a forecast service

Always aim to be helpful and provide practical, actionable information for travelers."""
)


def run_agent(message: str, history: list[Dict[str, Any]]):
    """
    Main agent function using the agent loop system.
    First gathers context through multiple tool calls, then synthesizes the final answer.
    """
    try:
        # Create a separate model instance for the agent loop
        loop_model = genai.GenerativeModel(
            model_name=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            system_instruction="You are a tool orchestration agent. Analyze queries and decide which tools to call."
        )

        # Step 1: Run the agent loop to gather context
        agent = AgentLoop(loop_model)
        agent_context = agent.run(message)

        # Step 2: Use the main model to synthesize a final answer from the context
        chat = model.start_chat(history=history or [])

        synthesis_prompt = f"""Based on the following context gathered from various tools, provide a comprehensive and helpful answer to the user.

User Query: {message}

Gathered Context:
{agent_context}

Please synthesize this information into a clear, conversational response that directly answers the user's question.
Include relevant details from the tools but present them in a natural, helpful way.
Be concise but informative."""

        final_response = chat.send_message(synthesis_prompt)

        # Extract traces from agent context for display
        traces = []
        if "Weather function was called" in agent_context:
            traces.append({"name": "weather_tool", "args": {}, "result": {}})
        if "Currency function was called" in agent_context:
            traces.append({"name": "currency_convert", "args": {}, "result": {}})
        if "Wikipedia function was called" in agent_context:
            traces.append({"name": "wikipedia_search", "args": {}, "result": {}})

        return final_response.text or "No response.", traces

    except Exception as e:
        return f"Error in agent loop: {str(e)}", []


def run_agent_stream(message: str, history: list[Dict[str, Any]]):
    """Stream version using the agent loop system with real Gemini streaming"""
    try:
        import threading
        import queue

        # Create a separate model instance for the agent loop
        loop_model = genai.GenerativeModel(
            model_name=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            system_instruction="You are a tool orchestration agent. Analyze queries and decide which tools to call."
        )

        # Queue for thinking events
        event_queue = queue.Queue()
        agent_context = None
        tool_traces = []

        def thinking_callback(event):
            """Callback to capture thinking events"""
            event_queue.put(event)

        def run_agent_thread():
            """Run agent in a separate thread"""
            nonlocal agent_context
            agent = AgentLoop(loop_model)
            agent_context = agent.run(message, thinking_callback)
            event_queue.put({"type": "agent_done"})

        # Start agent in background thread
        thread = threading.Thread(target=run_agent_thread)
        thread.start()

        # Stream thinking events as they come in
        while True:
            try:
                event = event_queue.get(timeout=0.1)
                if event.get("type") == "agent_done":
                    break
                yield event

                # Track tool usage for final summary
                if event.get("type") == "thinking" and event.get("tool"):
                    tool_name = event.get("tool")
                    if tool_name == "weather":
                        tool_traces.append({"name": "weather_tool", "args": {}, "result": {}})
                    elif tool_name == "currency":
                        tool_traces.append({"name": "currency_convert", "args": {}, "result": {}})
                    elif tool_name == "wikipedia":
                        tool_traces.append({"name": "wikipedia_search", "args": {}, "result": {}})
            except queue.Empty:
                continue

        # Wait for agent thread to complete
        thread.join(timeout=30)

        # Step 2: Stream the synthesized response
        chat = model.start_chat(history=history or [])

        synthesis_prompt = f"""Based on the following context gathered from various tools, provide a comprehensive and helpful answer to the user.

User Query: {message}

Gathered Context:
{agent_context}

Please synthesize this information into a clear, conversational response that directly answers the user's question.
Include relevant details from the tools but present them in a natural, helpful way.
Be concise but informative."""

        # Stream the final response
        stream_response = chat.send_message(synthesis_prompt, stream=True)
        for chunk in stream_response:
            if chunk.text:
                yield {"type": "text", "content": chunk.text}

        # Send final traces
        if tool_traces:
            yield {"type": "traces", "traces": tool_traces}

    except Exception as e:
        yield {"type": "error", "content": str(e)}
