import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.shared._httpx_utils import create_mcp_http_client

LOG_API_URL = "http://192.168.0.130:5001/logs/"

async def fetch_logs(params: dict) -> list[types.ContentBlock]:
    async with create_mcp_http_client() as client:
        response = await client.get(LOG_API_URL, params=params)
        response.raise_for_status()
        logs = response.json()
        return [types.TextContent(type="text", text=str(log)) for log in logs]

@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    app = Server("mcp-financial-logs")

    @app.call_tool()
    async def fetch_logs_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
        if name == "fetch_all_logs":
            return await fetch_logs(arguments)
        elif name == "fetch_logs_by_app":
            if "app_name" not in arguments:
                raise ValueError("Missing required argument 'app_name'")
            return await fetch_logs(arguments)
        elif name == "fetch_logs_by_app_and_level":
            if "app_name" not in arguments or "log_level" not in arguments:
                raise ValueError("Missing required arguments 'app_name' and/or 'log_level'")
            return await fetch_logs(arguments)
        elif name == "fetch_logs_by_app_and_server":
            if "app_name" not in arguments or "server" not in arguments:
                raise ValueError("Missing required arguments 'app_name' and/or 'server'")
            return await fetch_logs(arguments)
        elif name == "fetch_logs_by_app_and_severity":
            if "app_name" not in arguments or "severity" not in arguments:
                raise ValueError("Missing required arguments 'app_name' and/or 'severity'")
            return await fetch_logs(arguments)
        elif name == "fetch_logs_by_all_filters":
            required = {"app_name", "log_level", "server", "severity"}
            if not required.issubset(arguments.keys()):
                raise ValueError(f"Missing required arguments: {required - set(arguments.keys())}")
            return await fetch_logs(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="fetch_all_logs",
                title="Fetch All Logs",
                description="Fetch all logs with optional filters (limit, start_date, end_date, etc).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Limit the number of results"},
                        "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                        "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"},
                        "start_time": {"type": "string", "description": "Start time (HH:MM:SS)"},
                        "end_time": {"type": "string", "description": "End time (HH:MM:SS)"},
                    }
                },
            ),
            types.Tool(
                name="fetch_logs_by_app",
                title="Fetch Logs by App",
                description="Fetch logs for a specific application by name.",
                inputSchema={
                    "type": "object",
                    "required": ["app_name"],
                    "properties": {
                        "app_name": {"type": "string", "description": "Application name"},
                        "limit": {"type": "integer"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                    }
                },
            ),
            types.Tool(
                name="fetch_logs_by_app_and_level",
                title="Fetch Logs by App and Level",
                description="Fetch logs filtered by application name and log level.",
                inputSchema={
                    "type": "object",
                    "required": ["app_name", "log_level"],
                    "properties": {
                        "app_name": {"type": "string", "description": "Application name"},
                        "log_level": {"type": "string", "description": "Log level"},
                        "limit": {"type": "integer"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                    }
                },
            ),
            types.Tool(
                name="fetch_logs_by_app_and_server",
                title="Fetch Logs by App and Server",
                description="Fetch logs filtered by application name and server.",
                inputSchema={
                    "type": "object",
                    "required": ["app_name", "server"],
                    "properties": {
                        "app_name": {"type": "string", "description": "Application name"},
                        "server": {"type": "string", "description": "Server name"},
                        "limit": {"type": "integer"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                    }
                },
            ),
            types.Tool(
                name="fetch_logs_by_app_and_severity",
                title="Fetch Logs by App and Severity",
                description="Fetch logs filtered by application name and severity.",
                inputSchema={
                    "type": "object",
                    "required": ["app_name", "severity"],
                    "properties": {
                        "app_name": {"type": "string", "description": "Application name"},
                        "severity": {"type": "string", "description": "Severity"},
                        "limit": {"type": "integer"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                    }
                },
            ),
            types.Tool(
                name="fetch_logs_by_all_filters",
                title="Fetch Logs by All Filters",
                description="Fetch logs filtered by application name, log level, server, and severity.",
                inputSchema={
                    "type": "object",
                    "required": ["app_name", "log_level", "server", "severity"],
                    "properties": {
                        "app_name": {"type": "string"},
                        "log_level": {"type": "string"},
                        "server": {"type": "string"},
                        "severity": {"type": "string"},
                        "limit": {"type": "integer"},
                        "start_date": {"type": "string"},
                        "end_date": {"type": "string"},
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                    }
                },
            )
        ]

    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
            return Response()

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn

        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    else:
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        anyio.run(arun)

    return 0

if __name__ == "__main__":
    main()