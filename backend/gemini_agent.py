import os
import google.generativeai as genai
from typing import Dict, Any
from tools.weather import get_weather
from tools.currency import convert
from tools.wikipedia import search_wikipedia
from dotenv import load_dotenv

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
    # history is a list of {role: "user"|"model", parts: [...]}, optional
    chat = model.start_chat(history=history or [])
    resp = chat.send_message(message)

    tool_traces = []
    # Loop until no more tool calls
    MAX_STEPS = 4
    for _ in range(MAX_STEPS):
        calls = []
        for part in resp.candidates[0].content.parts:
            if fn := getattr(part, "function_call", None):
                calls.append(fn)

        if not calls:
            break

        tool_msgs = []
        for call in calls:
            name = call.name
            args = dict(call.args)

            if name == "weather_tool":
                out = get_weather(
                    args["city"],
                    state=args.get("state"),
                    country=args.get("country")
                )
            elif name == "currency_convert":
                out = convert(args["amount"], args["from"], args["to"])
            elif name == "wikipedia_search":
                out = search_wikipedia(
                    args["query"],
                    sentences=args.get("sentences", 3)
                )
            else:
                out = {"error": f"Unknown tool {name}"}

            tool_traces.append({"name": name, "args": args, "result": out})

            tool_msgs.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=name,
                        response={"content": out}
                    )
                )
            )

        # feed tool responses back
        resp = chat.send_message(tool_msgs)

    final_text = resp.text or "No response."
    return final_text, tool_traces


def run_agent_stream(message: str, history: list[Dict[str, Any]]):
    """Stream version of run_agent that yields chunks of text using real Gemini streaming"""
    try:
        chat = model.start_chat(history=history or [])

        # First, check for tool calls with a non-streaming call
        initial_resp = chat.send_message(message)

        tool_traces = []
        calls = []

        # Check if there are function calls
        for part in initial_resp.candidates[0].content.parts:
            if fn := getattr(part, "function_call", None):
                calls.append(fn)

        # If there are tool calls, process them
        if calls:
            tool_msgs = []
            for call in calls:
                name = call.name
                args = dict(call.args)

                # Notify frontend about tool usage
                yield {"type": "tool_start", "name": name, "args": args}

                if name == "weather_tool":
                    out = get_weather(
                        args["city"],
                        state=args.get("state"),
                        country=args.get("country")
                    )
                elif name == "currency_convert":
                    out = convert(args["amount"], args["from"], args["to"])
                elif name == "wikipedia_search":
                    out = search_wikipedia(
                        args["query"],
                        sentences=args.get("sentences", 3)
                    )
                else:
                    out = {"error": f"Unknown tool {name}"}

                tool_traces.append({"name": name, "args": args, "result": out})
                yield {"type": "tool_complete", "name": name, "result": out}

                tool_msgs.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=name,
                            response={"content": out}
                        )
                    )
                )

            # Stream the final response after tool calls using Gemini's streaming
            stream_response = chat.send_message(tool_msgs, stream=True)
            for chunk in stream_response:
                if chunk.text:
                    yield {"type": "text", "content": chunk.text}
        else:
            # No tool calls, restart chat and stream the response directly
            # We need to restart because we already consumed the response
            chat = model.start_chat(history=history or [])
            stream_response = chat.send_message(message, stream=True)

            for chunk in stream_response:
                if chunk.text:
                    yield {"type": "text", "content": chunk.text}

        # Send final traces if any
        if tool_traces:
            yield {"type": "traces", "traces": tool_traces}

    except Exception as e:
        yield {"type": "error", "content": str(e)}
