#!/usr/bin/env python3
"""Route a list of links into a single file-download link and 1-4 website links.

Behavior:
- The script starts with a default list of 4 links (simulate data coming from a DB).
- The first link is treated as the file-download link (handled by `link_to_file.download_file`).
- The remaining 1-4 links are treated as website URLs to be scraped and converted to ICS (handled by functions in `website_to_ics`).

Notes:
- This file does NOT implement any database access. Replace the `STARTING_LINKS` list with data from your DB as needed.
- By default the script performs a dry-run and prints the planned actions. Pass `--execute` to actually call the network functions.
"""

from typing import List, Tuple
import sys
import os
import json

# Import existing utilities in the workspace
import link_to_file
import website_to_ics



# Starting list with 4 links as requested (simulate input from database)
STARTING_LINKS: List[str] = [
    "",           # file to download
    "https://www.eventbrite.com/d/ma--hadley/events/",        # website to convert to ICS
    "",          # website to convert to ICS
    "",          # website to convert to ICS
    ""
    "",    
]


def split_links(links: List[str]) -> Tuple[str, List[str]]:
    """Assume the first link is the file to download and the rest are website links.

    This follows the expected DB contract: 1 link for file download, 1-4 links for web->ICS.
    If fewer than 2 links are provided, raises ValueError.
    """
    if not links or len(links) < 2:
        raise ValueError("Expected at least 2 links: 1 file link and 1 website link")

    file_link = links[0]
    web_links = links[1:5]  # allow up to 4 website links
    return file_link, web_links


def dry_run(file_link: str, web_links: List[str]):
    """Print planned actions without performing network calls."""
    print("DRY RUN: The script will perform the following actions:")
    print(f"- Download file from: {file_link}")
    print(f"- Convert {len(web_links)} website(s) to ICS:")
    for i, url in enumerate(web_links, 1):
        print(f"  {i}. {url}")
    print("\nTo actually perform downloads and scraping, run with the --execute flag.")


def execute(file_link: str, web_links: List[str]):
    """Perform the real actions using the existing modules in the workspace.

    - Calls link_to_file.download_file(file_link)
    - For each website link: scrapes the website, calls extract_events_with_ollama (requires OPENROUTER_API_KEY),
      and then writes ICS using create_ics_file.

    WARNING: extract_events_with_ollama requires an OpenRouter API key in the environment
    variable OPENROUTER_API_KEY or passed in; if not set the call will exit.
    """
    # Download file
    print(f"Downloading file from: {file_link}")
    try:
        downloaded = link_to_file.download_file(file_link)
        print(f"Downloaded file saved as: {downloaded}")
    except SystemExit:
        print("link_to_file raised SystemExit (download failed). Aborting execution.")
        return
    except Exception as e:
        print(f"Unexpected error during download: {e}")
        return

    # Process websites
    for url in web_links:
        print(f"\nProcessing website: {url}")
        try:
            scraped = website_to_ics.scrape_website(url)
            print(f"Scraped {len(scraped)} characters from {url}")

            # Attempt to extract events and create ICS. This function expects an API key
            # to be set in OPENROUTER_API_KEY or passed as parameter. We call it as-is so
            # it uses the environment variable.
            events_ics = website_to_ics.extract_events_with_ollama(scraped)

            # Write events to an ICS file. Name will default to events.ics and auto-increment
            website_to_ics.create_ics_file(events_ics)

        except SystemExit:
            print(f"website_to_ics aborted while processing {url} (likely missing API key or HTTP error). Continuing to next url.")
            continue
        except Exception as e:
            print(f"Error processing {url}: {e}")
            continue


def load_links_from_json(path: str) -> List[str]:
    """Utility to load a JSON array of links to simulate DB input.

    Example JSON file content: ["https://...", "https://...", ...]
    Returns the list from the file or raises on error.
    """
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("JSON must contain a list of links")
    return data


def main(argv: List[str]):
    """Entry point.

    Usage:
      python app2.py            # dry-run using built-in STARTING_LINKS
      python app2.py --execute  # actually perform network actions
      python app2.py links.json --execute  # load links from JSON file and execute
    """
    execute_mode = False
    links_source = None

    args = argv[1:]
    if '--execute' in args:
        execute_mode = True
        args.remove('--execute')

    if args:
        # If a path is provided, load links from it (simulate DB input)
        links_source = args[0]

    if links_source:
        try:
            links = load_links_from_json(links_source)
        except Exception as e:
            print(f"Failed to load links from {links_source}: {e}")
            return
    else:
        links = STARTING_LINKS

    try:
        file_link, web_links = split_links(links)
    except ValueError as e:
        print(f"Invalid links input: {e}")
        return

    if not execute_mode:
        dry_run(file_link, web_links)
    else:
        execute(file_link, web_links)


if __name__ == '__main__':
    main(sys.argv)