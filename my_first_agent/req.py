from groq import Groq
from tavily import TavilyClient
import os
import json
from dotenv import load_dotenv

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def search_web(query: str) -> str:
    """Search the web for current, real-time information."""
    results = tavily.search(query=query, max_results=3)
    return json.dumps(results)

tools = [{
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Search the web for current, real-time information",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    }
}]

available_functions = {"search_web": search_web}

def run_agent(user_message, max_steps=5):
    messages = [{"role": "user", "content": user_message}]

    for step in range(max_steps):
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",   # switched model
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0   # more deterministic, helps tool-call reliability
        )
        message = response.choices[0].message

        if not message.tool_calls:
            return message.content

        messages.append(message)
        for tool_call in message.tool_calls:
            func = available_functions[tool_call.function.name]
            args = json.loads(tool_call.function.arguments)
            result = func(**args)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })

    return "Max steps reached without a final answer."

# Try it
answer = run_agent("Where is veltech university located give me along with pincode etc.")
print(answer)