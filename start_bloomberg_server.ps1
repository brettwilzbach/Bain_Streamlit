# PowerShell script to start Bloomberg MCP Server
Write-Host "Starting Bloomberg MCP Server..." -ForegroundColor Green
Write-Host "Make sure Bloomberg Terminal is running before starting this server." -ForegroundColor Yellow
Write-Host ""
python -m blpapi_mcp --sse --host 127.0.0.1 --port 8000

