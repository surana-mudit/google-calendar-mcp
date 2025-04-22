#!/usr/bin/env python
"""
Google Calendar MCP Server
--------------------------
Provides access to Google Calendar events through MCP resources and tools.
"""

import os
import json
import datetime
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP, Context
from dateutil.parser import parse as parse_date
import dateparser
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Configure logging
log_dir = os.path.expanduser("~/Practice-Projects/mcp")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "calendar_mcp_server.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger('calendar_mcp')

# Constants
SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_DIR = os.path.expanduser("~/Practice-Projects/mcp")
os.makedirs(TOKEN_DIR, exist_ok=True)
TOKEN_FILE = os.path.join(TOKEN_DIR, 'token.json')
CREDENTIALS_FILE = os.path.join(TOKEN_DIR, 'credentials.json')

# Create the MCP server
mcp = FastMCP("Google Calendar")


def get_credentials():
    """Get or refresh Google API credentials."""
    logger.info("Attempting to get or refresh credentials")
    creds = None
    token_path = Path(TOKEN_FILE)
    
    # Check if token.json exists with stored credentials
    if token_path.exists():
        logger.info(f"Found existing token file at {token_path}")
        creds = Credentials.from_authorized_user_info(
            json.loads(token_path.read_text()), SCOPES)
    else:
        logger.info("No token file found, will need to authenticate")
    
    # If credentials don't exist or are invalid, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired token")
            creds.refresh(Request())
        else:
            credential_path = Path(CREDENTIALS_FILE)
            if not credential_path.exists():
                error_msg = f"Missing {CREDENTIALS_FILE}. Download it from Google Cloud Console."
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            logger.info(f"Starting OAuth flow using {CREDENTIALS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            logger.info("OAuth flow completed successfully")
        
        # Save credentials for next run
        token_content = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        token_path.write_text(json.dumps(token_content))
        logger.info(f"Credentials saved to {token_path}")
    
    return creds


def get_calendar_service():
    """Create a Google Calendar API service object."""
    logger.info("Building Google Calendar service")
    try:
        creds = get_credentials()
        service = build('calendar', 'v3', credentials=creds)
        logger.info("Calendar service built successfully")
        return service
    except Exception as e:
        logger.error(f"Failed to build calendar service: {str(e)}", exc_info=True)
        raise


@dataclass
class CalendarEvent:
    """Structured representation of a calendar event."""
    id: str
    summary: str
    start_time: str
    end_time: str
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: Optional[List[str]] = None


def format_events(events) -> str:
    """Format events into a human-readable string."""
    event_count = len(events) if events else 0
    logger.info(f"Formatting {event_count} events")
    
    if not events:
        return "No events found."
    
    formatted = []
    for event in events:
        start_time = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', 'Unknown'))
        end_time = event.get('end', {}).get('dateTime', event.get('end', {}).get('date', 'Unknown'))
        
        # Convert to more human-readable format if datetime (not just date)
        if 'T' in start_time:
            start_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            start_time = start_dt.strftime('%I:%M %p')
        
        if 'T' in end_time:
            end_dt = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            end_time = end_dt.strftime('%I:%M %p')
        
        attendees = []
        if 'attendees' in event:
            attendees = [attendee.get('email', '') for attendee in event['attendees']]
        
        formatted.append(
            f"Event: {event.get('summary', 'Untitled')}\n"
            f"Time: {start_time} - {end_time}\n"
            f"Location: {event.get('location', 'N/A')}\n"
            f"Description: {event.get('description', 'N/A')}\n"
            f"Attendees: {', '.join(attendees) if attendees else 'None'}\n"
        )
    
    return "\n".join(formatted)


def parse_natural_language_date(date_str: str) -> datetime.date:
    """
    Parse natural language date expressions into datetime objects.
    
    Args:
        date_str: Date string in natural language (e.g., 'yesterday', 'last week', 'next monday')
                 or in standard format (YYYY-MM-DD)
    
    Returns:
        datetime.date object representing the date
    
    Raises:
        ValueError: If the date string cannot be parsed
    """
    logger.info(f"Parsing natural language date: '{date_str}'")
    
    # First try with dateparser which handles natural language well
    parsed_date = dateparser.parse(date_str)
    
    if parsed_date:
        logger.info(f"Successfully parsed '{date_str}' to {parsed_date.date().isoformat()}")
        return parsed_date.date()
    
    # Fall back to dateutil.parser for standard formats
    try:
        return parse_date(date_str).date()
    except Exception as e:
        error_msg = f"Unknown string format: {date_str}"
        logger.error(error_msg)
        raise ValueError(error_msg)


def get_date_range(date_str: str) -> tuple:
    """Convert a date string to start and end datetime objects."""
    logger.info(f"Converting date string: {date_str}")
    try:
        # Parse the date string using enhanced natural language parsing
        date = parse_natural_language_date(date_str)
        
        # Create start and end timestamps for the entire day
        start_datetime = datetime.datetime.combine(date, datetime.time.min)
        end_datetime = datetime.datetime.combine(date, datetime.time.max)
        
        logger.info(f"Date range: {start_datetime.isoformat()} to {end_datetime.isoformat()}")
        return start_datetime.isoformat() + 'Z', end_datetime.isoformat() + 'Z'
    except Exception as e:
        error_msg = f"Invalid date format: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)


# Resources
@mcp.resource("calendar://events/{date}")
def get_events_resource(date: str) -> str:
    """
    Get calendar events for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format or natural language like 'today', 'tomorrow'
    
    Returns:
        Formatted string with event details
    """
    logger.info(f"Resource request: Getting events for date '{date}'")
    try:
        service = get_calendar_service()
        
        # Parse date using enhanced natural language parser
        start_time, end_time = get_date_range(date)
        
        logger.info(f"Fetching events between {start_time} and {end_time}")
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        logger.info(f"Found {len(events)} events")
        return format_events(events)
    
    except Exception as e:
        error_msg = f"Error retrieving calendar events: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


# Tools
@mcp.tool()
def list_events(date_start: str, date_end=None) -> str:
    """
    List calendar events within a date range.
    
    Args:
        date_start: Start date (YYYY-MM-DD or natural language like 'today')
        date_end: Optional end date; if not provided, will use only the start date
    
    Returns:
        Formatted string with events in the date range
    """
    logger.info(f"Tool call: list_events(date_start='{date_start}', date_end='{date_end}')")
    try:
        service = get_calendar_service()
        
        # Parse the start date using enhanced natural language parsing
        try:
            start_date = parse_natural_language_date(date_start)
            start_time = datetime.datetime.combine(start_date, datetime.time.min).isoformat() + 'Z'
        except ValueError as e:
            return f"Error listing calendar events: {str(e)}"
        
        # If end date is provided, parse it; otherwise, use the start date
        if date_end:
            try:
                end_date = parse_natural_language_date(date_end)
                end_time = datetime.datetime.combine(end_date, datetime.time.max).isoformat() + 'Z'
            except ValueError as e:
                return f"Error parsing end date: {str(e)}"
        else:
            end_time = datetime.datetime.combine(start_date, datetime.time.max).isoformat() + 'Z'
        
        logger.info(f"Fetching events between {start_time} and {end_time}")
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time,
            timeMax=end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        logger.info(f"Found {len(events)} events")
        return format_events(events)
    
    except Exception as e:
        error_msg = f"Error listing calendar events: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@mcp.tool()
def create_event(summary: str, start_datetime: str, end_datetime: str, 
                 description: Optional[str] = None, 
                 location: Optional[str] = None, 
                 attendees: Optional[str] = None) -> str:
    """
    Create a new calendar event.
    
    Args:
        summary: Event title
        start_datetime: Start time (in ISO format or natural language)
        end_datetime: End time (in ISO format or natural language)
        description: Optional event description
        location: Optional event location
        attendees: Optional comma-separated list of attendee emails
    
    Returns:
        Confirmation message with the event details
    """
    logger.info(f"Tool call: create_event(summary='{summary}', start='{start_datetime}', end='{end_datetime}')")
    try:
        service = get_calendar_service()
        
        # Parse and format date times using enhanced natural language parsing
        try:
            # For event creation, we need full datetime, not just date
            start_dt = dateparser.parse(start_datetime)
            if not start_dt:
                start_dt = parse_date(start_datetime)
                
            end_dt = dateparser.parse(end_datetime)
            if not end_dt:
                end_dt = parse_date(end_datetime)
                
            logger.info(f"Parsed start time: {start_dt.isoformat()}, end time: {end_dt.isoformat()}")
        except Exception as e:
            return f"Error parsing event dates: {str(e)}"
        
        event_body = {
            'summary': summary,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'UTC',
            },
        }
        
        if description:
            event_body['description'] = description
            logger.info(f"Added description: {description}")
        
        if location:
            event_body['location'] = location
            logger.info(f"Added location: {location}")
        
        # Add attendees if provided
        if attendees:
            attendee_emails = [email.strip() for email in attendees.split(',')]
            logger.info(f"Adding attendees: {attendee_emails}")
            attendee_list = [{'email': email} for email in attendee_emails]
            event_body['attendees'] = attendee_list
        
        logger.info("Creating event in Google Calendar")
        event = service.events().insert(calendarId='primary', body=event_body).execute()
        logger.info(f"Event created successfully with ID: {event['id']}")
        
        return f"Event created successfully!\nEvent ID: {event['id']}\nLink: {event.get('htmlLink', 'No link available')}"
    
    except Exception as e:
        error_msg = f"Error creating event: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


@mcp.tool()
def update_event(event_id: str, summary: Optional[str] = None, 
                 start_datetime: Optional[str] = None, 
                 end_datetime: Optional[str] = None,
                 description: Optional[str] = None, 
                 location: Optional[str] = None) -> str:
    """
    Update an existing calendar event.
    
    Args:
        event_id: The ID of the event to update
        summary: New event title (optional)
        start_datetime: New start time (optional)
        end_datetime: New end time (optional)
        description: New event description (optional)
        location: New event location (optional)
    
    Returns:
        Confirmation message with the updated event details
    """
    logger.info(f"Tool call: update_event(event_id='{event_id}')")
    try:
        service = get_calendar_service()
        
        # First get the existing event
        logger.info(f"Fetching existing event with ID: {event_id}")
        event = service.events().get(calendarId='primary', eventId=event_id).execute()
        
        # Update the fields that were provided
        if summary:
            event['summary'] = summary
            logger.info(f"Updating summary to: {summary}")
        
        if start_datetime:
            try:
                start_dt = dateparser.parse(start_datetime)
                if not start_dt:
                    start_dt = parse_date(start_datetime)
                    
                event['start'] = {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'UTC',
                }
                logger.info(f"Updating start time to: {start_dt.isoformat()}")
            except Exception as e:
                return f"Error parsing start date: {str(e)}"
        
        if end_datetime:
            try:
                end_dt = dateparser.parse(end_datetime)
                if not end_dt:
                    end_dt = parse_date(end_datetime)
                    
                event['end'] = {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'UTC',
                }
                logger.info(f"Updating end time to: {end_dt.isoformat()}")
            except Exception as e:
                return f"Error parsing end date: {str(e)}"
        
        if description:
            event['description'] = description
            logger.info(f"Updating description to: {description}")
        
        if location:
            event['location'] = location
            logger.info(f"Updating location to: {location}")
        
        logger.info("Updating event in Google Calendar")
        updated_event = service.events().update(
            calendarId='primary', eventId=event_id, body=event).execute()
        logger.info(f"Event updated successfully with ID: {updated_event['id']}")
        
        return f"Event updated successfully!\nEvent ID: {updated_event['id']}\nLink: {updated_event.get('htmlLink', 'No link available')}"
    
    except Exception as e:
        error_msg = f"Error updating event: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg


# Prompts
@mcp.prompt()
def today_events() -> str:
    """Get a list of today's calendar events."""
    logger.info("Using prompt: today_events()")
    return "Please show me all of my calendar events for today."


@mcp.prompt()
def schedule_meeting() -> str:
    """Create a new meeting on my calendar."""
    logger.info("Using prompt: schedule_meeting()")
    return """
    I'd like to schedule a new meeting. Please help me create a calendar event with the following information:
    
    Title: [Meeting title]
    Date and time: [Date and time, e.g., "tomorrow at 2pm for 1 hour"]
    Description: [Optional description]
    Location: [Optional location]
    Attendees: [Optional list of emails]
    
    Please create this event in my calendar.
    """


if __name__ == "__main__":
    logger.info("=== Starting Google Calendar MCP Server ===")
    try:
        logger.info("Server initialized and ready to handle connections")
        mcp.run()
    except Exception as e:
        logger.critical(f"Server crashed: {str(e)}", exc_info=True)
        raise
    finally:
        logger.info("=== Google Calendar MCP Server shutting down ===") 