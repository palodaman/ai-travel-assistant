"""
Agent Loop System with ChooseToolResult Architecture
Implements multi-step reasoning with context accumulation
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any
import google.generativeai as genai
from tools.weather import get_weather
from tools.currency import convert as convert_currency
from tools.wikipedia import search_wikipedia

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentLoop:
    """
    Implements an agent loop that:
    1. Uses ChooseToolResult to decide next tool
    2. Executes tools and accumulates context
    3. Builds comprehensive OUTPUT string
    4. Returns raw context (no synthesis)
    """

    def __init__(self, model: genai.GenerativeModel):
        self.model = model
        self.max_iterations = 10
        self.output_context = ""
        self.iteration_count = 0

    def choose_tool_result(self, user_query: str, current_context: str) -> Dict[str, Any]:
        """
        Decides which tool to call next based on query and context.
        Returns JSON specifying the tool and parameters.
        """

        prompt = f"""You are an intelligent travel assistant that decides which tool to call next.

Available tools:
1. weather - Get weather for a city
   Format: {{"tool": "weather", "city": "string", "state": "optional", "country": "optional", "reason": "your actual thinking about why you need this"}}

2. currency - Convert currency amounts
   Format: {{"tool": "currency", "amount": number, "from": "currency_code", "to": "currency_code", "reason": "your actual thinking about why you need this"}}

3. wikipedia - Search for information about places, people, or topics
   Format: {{"tool": "wikipedia", "query": "search_term", "sentences": 3, "reason": "your actual thinking about why you need this"}}

4. get_context - Return current accumulated context
   Format: {{"tool": "get_context"}}

5. stop - Stop and return accumulated context
   Format: {{"tool": "stop", "stop": true, "reason": "explain what you've gathered and why you're ready to respond"}}

User Query: {user_query}

Current Context Accumulated:
{current_context if current_context else "No context yet - this is the first tool call"}

Based on the user query and what has already been gathered in the context, decide what tool to call next.
If all necessary information has been gathered, call the stop tool.

IMPORTANT: The "reason" field should contain your actual thinking process, like:
- "I need to check the current weather conditions in Paris to help them plan their trip"
- "Converting their budget from USD to EUR will help them understand local costs"
- "Looking up information about the Louvre Museum since they asked about attractions"
- "I now have the weather forecast and currency rates they requested, ready to provide a complete answer"

Be genuine and specific about WHY you're making each tool call based on what the user actually asked.
Don't use generic phrases like "User requested X" - explain your actual reasoning.

Return ONLY valid JSON for the next tool call. No other text."""

        try:
            response = self.model.generate_content(prompt)

            # Extract JSON from response
            response_text = response.text.strip()

            # Try to find JSON in the response
            if '{' in response_text and '}' in response_text:
                start = response_text.index('{')
                end = response_text.rindex('}') + 1
                json_str = response_text[start:end]

                tool_decision = json.loads(json_str)
                logger.info(f"Tool decision: {tool_decision}")
                return tool_decision
            else:
                logger.error(f"No valid JSON in response: {response_text}")
                return {"tool": "stop", "stop": True}

        except Exception as e:
            logger.error(f"Error in choose_tool_result: {e}")
            return {"tool": "stop", "stop": True}

    def execute_tool(self, tool_decision: Dict[str, Any]) -> str:
        """
        Executes the specified tool and returns the result as a string.
        """
        tool_name = tool_decision.get("tool", "").lower()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            if tool_name == "weather":
                city = tool_decision.get("city", "")
                state = tool_decision.get("state")
                country = tool_decision.get("country")
                reason = tool_decision.get("reason", "Checking weather conditions")

                result = get_weather(city, state=state, country=country)

                output = f"\n+ Weather function was called at {timestamp} and generated this output:\n"
                output += f"  City: {result.get('city', city)}\n"
                output += f"  Temperature: {result.get('temperature_c', 'N/A')}°C\n"
                output += f"  Wind Speed: {result.get('windspeed_kmh', 'N/A')} km/h\n"
                output += f"  Conditions: {result.get('conditions_code', 'N/A')}\n"
                if result.get('error'):
                    output += f"  Error: {result['error']}\n"
                output += f"  REASON: {reason}\n"

                return output

            elif tool_name == "currency":
                amount = tool_decision.get("amount", 1)
                from_currency = tool_decision.get("from", "USD")
                to_currency = tool_decision.get("to", "EUR")
                reason = tool_decision.get("reason", "Converting currency")

                result = convert_currency(amount, from_currency, to_currency)

                output = f"\n+ Currency function was called at {timestamp} and generated this output:\n"
                output += f"  Converting: {amount} {from_currency} to {to_currency}\n"
                output += f"  Result: {result.get('result', 'N/A')} {to_currency}\n"
                output += f"  Rate: {result.get('rate', 'N/A')}\n"
                if result.get('error'):
                    output += f"  Error: {result['error']}\n"
                output += f"  REASON: {reason}\n"

                return output

            elif tool_name == "wikipedia":
                query = tool_decision.get("query", "")
                sentences = tool_decision.get("sentences", 3)
                reason = tool_decision.get("reason", "Searching for information")

                result = search_wikipedia(query, sentences=sentences)

                output = f"\n+ Wikipedia function was called at {timestamp} and generated this output:\n"
                output += f"  Query: {query}\n"
                output += f"  Title: {result.get('title', 'N/A')}\n"
                output += f"  Summary: {result.get('summary', 'No summary available')}\n"
                output += f"  URL: {result.get('url', 'N/A')}\n"
                if result.get('error'):
                    output += f"  Error: {result['error']}\n"
                output += f"  REASON: {reason}\n"

                return output

            elif tool_name == "get_context":
                return f"\n[Context requested at {timestamp}]\nCurrent accumulated context:\n{self.output_context}\n"

            elif tool_name == "stop":
                return ""  # No output for stop

            else:
                return f"\n+ Unknown tool '{tool_name}' requested at {timestamp}\n"

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return f"\n+ Error executing {tool_name} at {timestamp}: {str(e)}\n"

    def run(self, user_query: str, thinking_callback=None) -> str:
        """
        Main agent loop that orchestrates tool calls and builds context.
        Returns the accumulated OUTPUT string without synthesis.

        Args:
            user_query: The user's query
            thinking_callback: Optional callback to emit thinking events
        """
        # Initialize OUTPUT with the original query
        self.output_context = f"Original user query was: {user_query}\n"
        self.output_context += "=" * 80 + "\n"

        # Main loop
        for iteration in range(self.max_iterations):
            self.iteration_count = iteration + 1
            logger.info(f"Iteration {self.iteration_count}/{self.max_iterations}")

            # Step 1: Choose which tool to call next
            tool_decision = self.choose_tool_result(user_query, self.output_context)

            # Emit thinking event if callback provided
            if thinking_callback and tool_decision:
                thinking_callback({
                    "type": "thinking",
                    "iteration": self.iteration_count,
                    "tool": tool_decision.get("tool"),
                    "reason": tool_decision.get("reason", "Analyzing query..."),
                    "params": {k: v for k, v in tool_decision.items() if k not in ["tool", "reason", "stop"]}
                })

            # Step 2: Check for stop condition
            if tool_decision.get("tool") == "stop":
                logger.info("Stop tool called, ending loop")
                if thinking_callback:
                    thinking_callback({
                        "type": "thinking_complete",
                        "message": "Finished gathering information"
                    })
                break

            # Step 3: Execute the tool
            tool_output = self.execute_tool(tool_decision)

            # Step 4: Accumulate context
            if tool_output:
                self.output_context += tool_output
                self.output_context += "-" * 40 + "\n"

            # Log current context size
            logger.info(f"Context size: {len(self.output_context)} characters")

        # Add final metadata
        self.output_context += "\n" + "=" * 80 + "\n"
        self.output_context += f"Agent loop completed after {self.iteration_count} iterations\n"
        self.output_context += f"Total context size: {len(self.output_context)} characters\n"
        self.output_context += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        return self.output_context


def create_agent_loop(model: genai.GenerativeModel) -> AgentLoop:
    """Factory function to create an AgentLoop instance"""
    return AgentLoop(model)


# Standalone function for easy integration
def run_agent_loop(user_query: str, model: genai.GenerativeModel, thinking_callback=None) -> str:
    """
    Convenience function to run the agent loop.
    Returns accumulated context string without synthesis.

    Args:
        user_query: The user's query
        model: The Gemini model to use
        thinking_callback: Optional callback to emit thinking events
    """
    agent = AgentLoop(model)
    return agent.run(user_query, thinking_callback)