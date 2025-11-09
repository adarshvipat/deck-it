#!/usr/bin/env python3
"""
Scan all .ics files in the current directory, extract all events, and build a list of dictionaries for each event.
Each dictionary contains:
    - title
    - date
    - start time
    - end time
    - location
    - description
    - icstext (raw ICS text for the event)

Usage:
    python file_to_list.py

Dependencies:
    pip install icalendar
"""
import os
from icalendar import Calendar
from typing import List, Dict


def extract_events_from_ics(file_path: str, start_id: int = 1) -> List[Dict]:
    """Extract all VEVENTs from an .ics file as dictionaries, including raw ICS text."""
    events = []
    event_id = start_id
    with open(file_path, 'r', encoding='utf-8') as f:
        cal = Calendar.from_ical(f.read())
        for component in cal.walk():
            if component.name == "VEVENT":
                start_dt = component.get('DTSTART').dt if component.get('DTSTART') else None
                if start_dt and hasattr(start_dt, 'date'):
                    date_str = str(start_dt.date())
                else:
                    date_str = ''
                event_dict = {
                    "id": event_id,
                    "title": str(component.get('SUMMARY', 'Untitled Event')),
                    "date": date_str,
                    "start time": str(start_dt) if start_dt else '',
                    "end time": str(component.get('DTEND').dt) if component.get('DTEND') else '',
                    "location": str(component.get('LOCATION', 'TBD')),
                    "description": str(component.get('DESCRIPTION', '')),
                    "icstext": component.to_ical().decode('utf-8')
                }
                events.append(event_dict)
                event_id += 1
    return events


def main():
    all_events = []
    event_id = 1
    for fname in os.listdir('.'):
        if fname.lower().endswith('.ics') and os.path.isfile(fname):
            events = extract_events_from_ics(fname, start_id=event_id)
            all_events.extend(events)
            event_id += len(events)
    #print(all_events)


if __name__ == '__main__':
    main()
