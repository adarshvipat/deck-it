# Website to ICS Event Scraper

This program scrapes events from a website and formats them into ICS (iCalendar) format using Ollama and Gemma 2B.

## Prerequisites

1. **Python 3.7+**
2. **Ollama** installed and running
3. **Gemma model** installed in Ollama (gemma2:2b, gemma2:9b, or other variants)

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

3. Install and start Ollama (if not already installed):
   - Visit https://ollama.ai/ to download Ollama
   - Start the Ollama service

4. Pull a Gemma model (choose one):
```bash
# For Gemma 2B (smaller, faster)
ollama pull gemma2:2b

# For Gemma 9B (larger, more accurate)
ollama pull gemma2:9b

# Or other Gemma variants
```

## Usage

**Make sure your virtual environment is activated** (if using one):
```bash
source venv/bin/activate  # On macOS/Linux
```

Then run the script:
```bash
python website_to_ics.py <website_url> [output_file.ics] [model_name]
```

### Examples

```bash
# Scrape events and save to default file (events.ics) with default model
python website_to_ics.py https://example.com/events

# Scrape events and save to custom file
python website_to_ics.py https://example.com/events my_events.ics

# Use a specific model (e.g., gemma2:9b for better accuracy)
python website_to_ics.py https://example.com/events my_events.ics gemma2:9b
```

## How it Works

1. **Web Scraping**: Uses `requests` and `BeautifulSoup` to scrape the website content
2. **Event Extraction**: Uses Ollama with Gemma 2B to intelligently extract event information from the scraped content
3. **ICS Formatting**: Formats the extracted events into standard ICS (iCalendar) format
4. **Output**: Saves the events to an ICS file that can be imported into calendar applications (Google Calendar, Apple Calendar, Outlook, etc.)

## Notes

- The program extracts event titles, dates, times, descriptions, and locations
- If end times are missing, events default to 1 hour duration
- The ICS file uses UTC timezone format
- Make sure Ollama is running before executing the script

## Troubleshooting

- **Ollama connection error**: Make sure Ollama is running (`ollama serve` or check if it's running as a service)
- **Model not found**: Run `ollama pull <model_name>` to download the model (e.g., `ollama pull gemma2:2b`)
- **No events found**: The website might not contain events, or the content format might not be recognized
- **Better accuracy needed**: Try using a larger model like `gemma2:9b` instead of `gemma2:2b`

