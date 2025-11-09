# Website to ICS Event Scraper

This program scrapes events from a website and formats them into ICS (iCalendar) format using OpenRouter and Google Gemini 2.5 Flash Preview.

## Prerequisites

1. **Python 3.7+**
2. **OpenRouter API key** (get one at https://openrouter.ai/keys)

## Installation

1. Create and activate a virtual environment (recommended):
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Setup OpenRouter API Key

Set your OpenRouter API key as an environment variable:
```bash
export OPENROUTER_API_KEY=sk-...yourkey...
```

## Usage

**Make sure your virtual environment is activated** (if using one):
```bash
source venv/bin/activate  # On macOS/Linux
```

Then run the script:
```bash
python website_to_ics.py <website_url> [output_file.ics] [model_name] [api_key]
```
- `model_name` defaults to `google/gemini-2.5-flash-preview-09-2025` if not specified.
- `api_key` can be omitted if `OPENROUTER_API_KEY` is set.

### Examples

```bash
# Scrape events and save to default file (events.ics) with default model
python website_to_ics.py https://example.com/events

# Scrape events and save to custom file
python website_to_ics.py https://example.com/events my_events.ics

# Use a specific model (e.g., google/gemini-2.5-flash-preview-09-2025)
python website_to_ics.py https://example.com/events my_events.ics google/gemini-2.5-flash-preview-09-2025
```

## How it Works

1. **Web Scraping**: Uses `requests` and `BeautifulSoup` to scrape the website content
2. **Event Extraction**: Uses OpenRouter with Google Gemini to intelligently extract event information from the scraped content
3. **ICS Formatting**: Formats the extracted events into standard ICS (iCalendar) format
4. **Output**: Saves the events to an ICS file that can be imported into calendar applications (Google Calendar, Apple Calendar, Outlook, etc.)

## Notes

- The program extracts event titles, dates, times, descriptions, and locations
- If end times are missing, events default to 1 hour duration
- The ICS file uses UTC timezone format
- Make sure your OpenRouter API key is set before executing the script

## Troubleshooting

- **OpenRouter API error**: Make sure your API key is set and valid (`export OPENROUTER_API_KEY=...`)
- **No events found**: The website might not contain events, or the content format might not be recognized
- **Better accuracy needed**: Try using a different or more advanced model via OpenRouter

