# Google Calendar MCP Server

This MCP server provides access to your Google Calendar events and allows you to manage them through an MCP interface. It can be used with Claude Desktop or any other MCP-compatible client.

## Requirements

- **Python 3.10 or higher** - MCP requires Python 3.10+
- Google Cloud project with Calendar API enabled
- OAuth credentials for authentication

## Features

- **View calendar events** for any date or date range
- **Create new events** with title, time, description, location, and attendees
- **Update existing events** with new details
- **Pre-built prompts** for common calendar actions

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd google-calendar-mcp
   ```

2. Create a virtual environment with Python 3.10 or higher:
   ```bash
   # Check your Python version
   python --version
   
   # Create a virtual environment with the correct Python version
   # For Python 3.10
   python3.10 -m venv venv
   # OR for Python 3.11
   python3.11 -m venv venv
   # OR for Python 3.12
   python3.12 -m venv venv
   
   # Activate the virtual environment
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies using pip:
   ```bash
   pip install -r requirements.txt
   ```

   Alternatively, you can use `uv` for faster installation (recommended):
   ```bash
   # Install uv if you don't have it
   curl -fsSL https://astral.sh/uv/install.sh | sh
   # On Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Install dependencies with uv
   uv pip install -r requirements.txt
   ```

4. Set up Google Calendar API credentials:
   
   a. Go to the [Google Cloud Console](https://console.cloud.google.com/)
   b. Create a new project or select an existing one
   c. Enable the Google Calendar API
   d. Create OAuth credentials (Desktop client OAuth ID)
   e. Download the credentials JSON file and save it as `credentials.json` in the project directory

## Usage


### Using with Claude Desktop

1. Install Claude Desktop from the [official website](https://claude.ai/downloads)

2. Install the MCP server in Claude Desktop:
   ```bash
   # Make sure you're in the project directory with the virtual environment activated
   mcp install calendar_mcp_server.py
   ```

3. Configure Claude Desktop to use the MCP server by editing the Claude Desktop configuration file:
   - Locate the Claude configuration file at `/path/to/your/claude_desktop_config.json` (Mac) or appropriate location for your OS
   - Add or modify the configuration to include the Google Calendar MCP:
   ```json
   {
     "Google Calendar": {
       "command": "/path/to/your/venv/bin/mcp",
       "args": [
         "run",
         "/path/to/your/project/calendar_mcp_server.py"
       ]
     }
   }
   ```
   - Replace `/path/to/your/venv/` with the actual path to your virtual environment
   - Replace `/path/to/your/project/` with the actual path to your project directory

4. Verify that the MCP server is running properly:
   - Open Claude Desktop
   - Click on the settings icon (gear) in the bottom left corner
   - Select "Developer" from the settings menu
   - Under "Active MCP Servers", you should see "Google Calendar" listed
   - If the MCP server is running correctly, you'll see a green status indicator
   - If you don't see it listed or it shows an error, ensure that your server is running

4. You can now use prompts like:
   ```
   Show me my events for today
   Create a meeting with John tomorrow at 2pm
   ```

### Using with Cursor

1.  **Configure Cursor:**
    *   Open Cursor.
    *   Go to `Settings` (usually a gear icon or via the Command Palette).
    *   Navigate to `Cursor Settings` > `MCP`.
    *   Click on `Add New Global MCP Server`.
         - Add or modify the configuration to include the Google Calendar MCP:
         ```json
         {
         "Google Calendar": {
            "command": "/path/to/your/venv/bin/mcp",
            "args": [
               "run",
               "/path/to/your/project/calendar_mcp_server.py"
            ]
         }
         }
         ```
         - Replace `/path/to/your/venv/` with the actual path to your virtual environment
         - Replace `/path/to/your/project/` with the actual path to your project directory

3.  **Using in Cursor:**
    *   Now, when you chat with the AI in Cursor (e.g., using "Agent" mode or similar features that leverage MCP), it should be able to connect to your running Google Calendar MCP server.
    *   You can use calendar-related prompts like:
        ```
        Show me my events for today
        Create a meeting with John tomorrow at 2pm
        ```
    *   Cursor should route these requests to your local server if the configuration is correct and the server is running.

### Run in development mode with the MCP Inspector:

If you're developing or debugging the MCP server, use:

```bash
mcp dev calendar_mcp_server.py
```

This will provide additional debugging information and a web interface for inspecting requests and responses.

## Resources

The server exposes the following MCP resources:

- `calendar://events/{date}` - Returns events for a specific date

Example usage:
```
calendar://events/today
calendar://events/tomorrow
calendar://events/2023-07-15
```

## Tools

The server provides the following tools:

1. `list_events(date_start, date_end=None)` - List events in a date range
2. `create_event(summary, start_datetime, end_datetime, ...)` - Create a new calendar event
3. `update_event(event_id, ...)` - Update an existing event

## Prompts

Pre-built prompts to simplify common actions:

1. `today_events` - Quick access to today's calendar
2. `schedule_meeting` - Guided prompt to create a new meeting

## Authentication

On first use, the server will open a browser window for Google OAuth authentication. After authorizing the application, your credentials will be stored in `token.json` for future use.

## Troubleshooting

- **Python version issues**: This project requires Python 3.10 or higher. If you see errors like `No matching distribution found for mcp[cli]`, check your Python version.
- **Authentication errors**: Ensure your `credentials.json` file is correctly placed and has the right permissions.
- **MCP installation problems**: Try using `uv` instead of `pip` for a more reliable installation experience.

## Notes

- The server uses UTC for timestamps. Event times are displayed in the local timezone.
- You need a valid `credentials.json` file from Google Cloud Console to use this server.
- Your authentication token is stored in `token.json` after first login. 
