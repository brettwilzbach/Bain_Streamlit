@echo off
echo Starting Bloomberg MCP Server...
echo Make sure Bloomberg Terminal is running before starting this server.
echo.
python -m blpapi_mcp --sse --host 127.0.0.1 --port 8000
pause

