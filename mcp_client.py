import asyncio
import os
import sys
from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServerSse
from agents.model_settings import ModelSettings

#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

# Ensure OPENAI_API_KEY is set
if "OPENAI_API_KEY" not in os.environ:
    print("Error: Please set the OPENAI_API_KEY environment variable.")
    sys.exit(1)

# MCP SSE endpoint URL for the financial logs server
FINANCIAL_MCP_SSE_URL = os.getenv("FINANCIAL_MCP_SSE_URL", "http://localhost:8008/sse")

async def run_queries(fin_server):
    # Agent that can call tools from the MCP server
    agent = Agent(
        name="FinancialLogCLI",
        instructions=(
            "You are a financial log assistant. "
            "Use the following tools to fetch logs: "
            "fetch_all_logs, fetch_logs_by_app, fetch_logs_by_app_and_level, fetch_logs_by_app_and_server, "
            "fetch_logs_by_app_and_severity, fetch_logs_by_all_filters."
        ),
        mcp_servers=[fin_server],
        model_settings=ModelSettings(tool_choice="required"),
    )

    queries = [
        # Examples using your tools
        "Fetch all logs for app StockTraderPro with critical severity and limit 3.",
        "Show all logs for app StockTraderPro with log level exception.",
        "Fetch logs for app StockTraderPro on server app-server-1.",
        "Get logs for app StockTraderPro with severity warning and log level info.",
    ]

    for query in queries:
        print(f"\n=== Query: {query}")
        result = await Runner.run(starting_agent=agent, input=query)
        print(result.final_output)

async def main():
    # Connect to the MCP server via SSE
    async with MCPServerSse(name="FinancialServer", params={"url": FINANCIAL_MCP_SSE_URL}) as fin:
        trace_id = gen_trace_id()
        with trace(workflow_name="Financial Log CLI Session", trace_id=trace_id):
            print(f"Trace URL: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            await run_queries(fin)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user, exiting.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)