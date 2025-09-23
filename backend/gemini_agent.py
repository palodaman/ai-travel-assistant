import os
import google.generativeai as genai
from typing import Dict, Any
from tools.weather import get_weather
from tools.currency import convert
from dotenv import load_dotenv

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
        "description": "Get current weather for a city. Optionally specify state/province and country for disambiguation (e.g., Victoria, BC, Canada vs Victoria, Australia)",
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
        "description": "Convert currency via exchangerate.host",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "from": {"type": "string"},
                "to": {"type": "string"},
            },
            "required": ["amount", "from", "to"],
        },
    },
]

model = genai.GenerativeModel(
    model_name=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
    tools=[{"function_declarations": FUNCTIONS}],
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
