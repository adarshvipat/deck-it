#!/usr/bin/env python3
"""
Scrape events from a website and format them into ICS format using OpenRouter with Google Gemini 2.5 Flash Preview.
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import sys
import os
from typing import List, Dict, Optional

# Set your OpenRouter API key here
OPENROUTER_API_KEY = ""  # <-- Replace with your actual API key


def scrape_website(url: str) -> str:
    """
    Scrape the website and return the text content.
    
    Args:
        url: The website URL to scrape
        
    Returns:
        The text content of the website
    """
    try:
        # More realistic headers to avoid 403 errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        # Use a session to maintain cookies
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        # Check for specific HTTP status codes
        if response.status_code == 403:
            print(f"\n❌ 403 Forbidden Error: The website blocked the request.")
            print(f"   This usually means:")
            print(f"   • The website has anti-bot protection (Cloudflare, etc.)")
            print(f"   • The website requires authentication or cookies")
            print(f"   • The website blocks automated requests")
            print(f"\n   Possible solutions:")
            print(f"   • Try accessing the URL directly in a browser first")
            print(f"   • The website may require login or specific permissions")
            print(f"   • Some websites don't allow scraping - check their robots.txt")
            print(f"   • Try a different URL or use the website's API if available")
            sys.exit(1)
        elif response.status_code == 401:
            print(f"\n❌ 401 Unauthorized: The website requires authentication.")
            sys.exit(1)
        elif response.status_code == 404:
            print(f"\n❌ 404 Not Found: The URL doesn't exist.")
            sys.exit(1)
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        return text
    except requests.RequestException as e:
        print(f"\n❌ Error scraping website: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   HTTP Status Code: {e.response.status_code}")
            print(f"   Response Headers: {dict(e.response.headers)}")
        sys.exit(1)


def extract_events_with_openrouter(website_content: str, model: str = 'google/gemini-2.5-flash-preview-09-2025', api_key: Optional[str] = None) -> str:
    """
    Use OpenRouter with Google Gemini 2.5 Flash Preview to extract event information from website content.
    
    Args:
        website_content: The scraped website content
        model: The OpenRouter model to use (default: google/gemini-2.5-flash-preview-09-2025)
        api_key: OpenRouter API key (if None, will try to get from OPENROUTER_API_KEY environment variable)
        
    Returns:
        Formatted event information in ICS format
    """
    # Get API key from parameter, variable, or environment variable
    if api_key is None:
        api_key = OPENROUTER_API_KEY or os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            print("Error: OpenRouter API key is required.")
            print("Please set the OPENROUTER_API_KEY variable, environment variable, or pass it as a parameter.")
            print("You can get an API key from: https://openrouter.ai/keys")
            sys.exit(1)
    
    # Truncate content if too long (models have context limits)
    max_chars = 12000
    if len(website_content) > max_chars:
        website_content = website_content[:max_chars] + "..."
    
    prompt = f"""Extract all events from the following website content and format them as ICS (iCalendar) format.

Website content:
{website_content}

Please extract:
- Event title
- Start date and time
- End date and time (if available)
- Description (if available)
- Location (if available)

Format the output as valid ICS format. Each event should start with BEGIN:VEVENT and end with END:VEVENT.
Use UTC timezone format (YYYYMMDDTHHMMSSZ) for dates.
If a date is missing, use today's date.
If an end time is missing, assume the event is 1 hour long.

Example format:
BEGIN:VEVENT
DTSTART:20240101T120000Z
DTEND:20240101T130000Z
SUMMARY:Event Title
DESCRIPTION:Event description
LOCATION:Event location
END:VEVENT

Now extract and format all events from the website content:"""

    try:
        print(f"Calling OpenRouter with {model} to extract events...")
        
        # OpenRouter API endpoint
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/deck-it",  # Optional: for tracking
            "X-Title": "Deck-it Event Scraper"  # Optional: for tracking
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # Lower temperature for more consistent output
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        
        # Extract the content from the response
        if 'choices' in result and len(result['choices']) > 0:
            ics_content = result['choices'][0]['message']['content']
            return ics_content
        else:
            print(f"Error: Unexpected response format from OpenRouter: {result}")
            sys.exit(1)
            
    except requests.exceptions.RequestException as e:
        print(f"Error calling OpenRouter API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"HTTP Status Code: {e.response.status_code}")
                print(f"Response: {e.response.text}")
        print(f"Make sure your OpenRouter API key is valid and you have credits.")
        print(f"You can get an API key from: https://openrouter.ai/keys")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def get_next_available_filename(output_file: str) -> str:
    """
    Get the next available filename by incrementing the number if the file exists.
    
    Args:
        output_file: The desired output file name (e.g., "events.ics")
        
    Returns:
        A filename that doesn't exist yet (e.g., "events.ics", "events2.ics", "events3.ics")
    """
    # If the file doesn't exist, return it as-is
    if not os.path.exists(output_file):
        return output_file
    
    # Split filename into name and extension
    base_name, ext = os.path.splitext(output_file)
    
    # Check if the base name ends with a number (e.g., "events2")
    match = re.match(r'^(.+?)(\d+)$', base_name)
    
    if match:
        # File already has a number (e.g., "events2.ics")
        name_prefix = match.group(1)
        current_num = int(match.group(2))
        next_num = current_num + 1
    else:
        # File doesn't have a number yet (e.g., "events.ics")
        name_prefix = base_name
        next_num = 2
    
    # Keep incrementing until we find an available filename
    while True:
        new_filename = f"{name_prefix}{next_num}{ext}"
        if not os.path.exists(new_filename):
            return new_filename
        next_num += 1


def create_ics_file(events_ics: str, output_file: str = "events.ics"):
    """
    Create a complete ICS file with proper header and footer.
    If the file already exists, creates a new file with an incremented number.
    
    Args:
        events_ics: The events in ICS format (may include multiple VEVENT blocks)
        output_file: The output file name
    """
    # Extract VEVENT blocks from the response
    vevent_pattern = r'BEGIN:VEVENT.*?END:VEVENT'
    events = re.findall(vevent_pattern, events_ics, re.DOTALL)
    
    if not events:
        print("No events found in the extracted content.")
        print("Raw OpenRouter response:")
        print(events_ics)
        return
    
    # Get the next available filename
    final_filename = get_next_available_filename(output_file)
    
    if final_filename != output_file:
        print(f"File {output_file} already exists. Creating {final_filename} instead.")
    
    # Create complete ICS file
    ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Website Event Scraper//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
"""

    for event in events:
        ics_content += event + "\n"
    
    ics_content += "END:VCALENDAR"
    
    # Write to file
    with open(final_filename, 'w', encoding='utf-8') as f:
        f.write(ics_content)
    
    print(f"Successfully created ICS file: {final_filename}")
    print(f"Found {len(events)} event(s)")


def main():
    """
    Main function to scrape website and generate ICS file.
    """
    if len(sys.argv) < 2:
        print("Usage: python website_to_ics.py <website_url> [output_file.ics] [model_name] [api_key]")
        print("Example: python website_to_ics.py https://example.com/events events.ics")
        print("Example: python website_to_ics.py https://example.com/events events.ics google/gemini-2.5-flash-preview-09-2025")
        print("Note: Set OPENROUTER_API_KEY environment variable or pass API key as 4th argument")
        sys.exit(1)
    
    website_url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "events.ics"
    model = sys.argv[3] if len(sys.argv) > 3 else 'google/gemini-2.5-flash-preview-09-2025'
    api_key = sys.argv[4] if len(sys.argv) > 4 else None
    
    print(f"Scraping website: {website_url}")
    website_content = scrape_website(website_url)
    
    print(f"Website content scraped ({len(website_content)} characters)")
    print("\n" + "="*80)
    print("EXTRACTED WEBSITE TEXT:")
    print("="*80)
    print(website_content)
    print("="*80 + "\n")
    
    events_ics = extract_events_with_openrouter(website_content, model, api_key)
    
    create_ics_file(events_ics, output_file)


if __name__ == "__main__":
    main()

