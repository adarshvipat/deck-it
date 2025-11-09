from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from ics import Calendar, Event
import urllib.parse as urlparse
import psycopg2
import json
import os

# ---- Backend imports ----
import link_to_file
import website_to_ics
import file_to_list

app = Flask(__name__)
app.secret_key = "deckit_secret"

# ---- Database setup ----
db_url = ''
url = urlparse.urlparse(db_url)
dbusername = url.username
dbpassword = url.password
hostname = url.hostname
port = url.port if url.port else 5432
dbname = url.path[1:]
conn = psycopg2.connect(
    host=hostname,
    port=port,
    dbname=dbname,
    user=dbusername,
    password=dbpassword,
    sslmode='require'
)
cursor = conn.cursor()
print("Connection successful!")

# ---- Globals ----
stored_links = []
stored_yes = []
EVENTS = []

# ---- UMass links ----
PULSE_LINK = "https://umassamherst.campuslabs.com/engage/events.rss"
EVENTS_LINK = "https://events.umass.edu/calendar/1.xml"

# ============================================================
# Utility: backend link pipeline (from second app.py)
# ============================================================
def process_links(user_data):
    """
    Takes user_data tuple from DB and runs:
    - download Canvas .ics file
    - scrape optional websites and convert to .ics
    - extract all events into a unified list
    """
    canvas_link, cust1, cust2, cust3, cppref, umevpref = user_data
    STARTING_LINKS = [canvas_link, cust1, cust2, cust3, "", ""]

    # Add Pulse / UMass events based on preferences
    if cppref:
        STARTING_LINKS[4] = PULSE_LINK
    if umevpref:
        STARTING_LINKS[5] = EVENTS_LINK

    file_link = STARTING_LINKS[0]
    web_links = [x for x in STARTING_LINKS[1:6] if x.strip()]

    

    # --- Step 2: Scrape each website and generate ICS files
    for url in web_links:
        try:
            print(f"Scraping: {url}")
            scraped = website_to_ics.scrape_website(url)
            events_ics = website_to_ics.extract_events_with_openrouter(scraped)
            website_to_ics.create_ics_file(events_ics)
        except Exception as e:
            print(f"Error processing {url}: {e}")

    # --- Step 3: Combine all ICS events into list
    all_events = []
    for fname in os.listdir('.'):
        if fname.lower().endswith('.ics') and os.path.isfile(fname):
            try:
                all_events.extend(file_to_list.extract_events_from_ics(fname))
            except Exception as e:
                print(f"Failed reading {fname}: {e}")
    # --- Step 1: Download Canvas file (.ics)
    try:
        downloaded_file = link_to_file.download_file(file_link)
        print(f"Downloaded Canvas ICS: {downloaded_file}")
    except Exception as e:
        print(f"Canvas download failed: {e}")

    print(f"Extracted {len(all_events)} total events.")
    return all_events


# ============================================================
# Flask routes
# ============================================================

@app.route('/', methods=['GET', 'POST'])
def index():
    global stored_links
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        pwd = request.form.get('pwd', '').strip()
        canvas = request.form.get('canvas_link', '').strip()

        selected_options = request.form.getlist('options')
        cppref = "TRUE" if "TRUE" in selected_options else "FALSE"
        umeventspref = "TRUE" if len(selected_options) > 1 and selected_options[1] == 'TRUE' else "FALSE"

        cust1 = request.form.get('custom1', '').strip()
        cust2 = request.form.get('custom2', '').strip()
        cust3 = request.form.get('custom3', '').strip()

        q1 = f"INSERT INTO login VALUES('{email}','{pwd}','{canvas}','{cust1}','{cust2}','{cust3}',{cppref},{umeventspref});"
        cursor.execute(q1)
        conn.commit()

        cursor.execute("SELECT cust1,cust2,cust3,canvaslink FROM login;")
        stored_links = cursor.fetchall()
        return render_template('form.html', links=stored_links, submitted=True)
    return render_template('form.html', links=stored_links, submitted=False)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        pwd = request.form.get('pwd', '').strip()
        cursor.execute("SELECT * FROM login WHERE email=%s AND password=%s;", (email, pwd))
        user = cursor.fetchone()
        if user:
            session['user'] = email
            return redirect(url_for('deck'))
        else:
            return render_template('login.html', error="Invalid email or password.")
    return render_template('login.html', error=None)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/deck')
def deck():
    """Deck route: fetch user prefs, run backend pipeline, render event cards."""
    if 'user' not in session:
        return redirect(url_for('login'))

    email = session['user']
    cursor.execute(f"SELECT canvaslink, cust1, cust2, cust3, cppref, umevpref FROM login WHERE email='{email}';")
    user_data = cursor.fetchone()
    if not user_data:
        return "User data not found in DB.", 400

    # Run backend logic to gather events
    global EVENTS
    EVENTS = process_links(user_data)

    if not EVENTS:
        EVENTS = [{'id': 1, 'title': 'No events found', 'date': 'N/A', 'start_time': '', 'end_time': '', 'location': '', 'desc': ''}]
    else:
        # Ensure each has ID field for deck voting
        for i, e in enumerate(EVENTS, start=1):
            e['id'] = i

    # Check if user already saved events
    cursor.execute(f"SELECT * FROM selected WHERE email='{email}';")
    check = cursor.fetchall()
    if check:
        return redirect(url_for('dashboard'))
    return render_template('deck.html', events=EVENTS)


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    cursor.execute(f"SELECT file_data FROM selected WHERE email='{session['user']}';")
    row = cursor.fetchone()
    ics_string = row[0] if row and row[0] else ''
    parsed = []

    def parse_ics_string(ics_string):
        events = []
        if not ics_string:
            return events
        try:
            cal = Calendar(ics_string)
        except Exception:
            return events
        for e in cal.events:
            try:
                start_date = e.begin.format('YYYY-MM-DD')
                start_time = e.begin.format('HH:mm')
                end_time = e.end.format('HH:mm')
            except Exception:
                start_date, start_time, end_time = 'N/A', '', ''
            events.append({
                'title': e.name or 'Event',
                'description': e.description or '',
                'date': start_date,
                'startTime': start_time,
                'endTime': end_time
            })
        return events

    parsed = parse_ics_string(ics_string) if ics_string else globals().get('EVENTS', [])
    return render_template('dashboard.html', events=parsed)

@app.route('/vote', methods=['POST'])
def vote():
    
    global stored_yes
    data = request.get_json() or {}
    event_id = data.get('id')
    vote = data.get('vote')  # expected 'yes' or 'no'
    if event_id is None or vote not in ('yes', 'no'):
        return jsonify({'status': 'error', 'message': 'invalid payload'}), 400

    # find event
    event = next((e for e in EVENTS if e['id'] == event_id), None)
    if not event:
        return jsonify({'status': 'error', 'message': 'event not found'}), 404

    if vote == 'yes':
        # avoid duplicates
        if not any(e['id'] == event_id for e in stored_yes):
            stored_yes.append(event)
        
        save_selected_events()
        return jsonify({'status': 'ok'})


def save_selected_events():
    databytes = "\n".join(e.get('title', 'unknown') for e in stored_yes)
    q3 = f"INSERT INTO selected VALUES('{session['user']}','{databytes}');"
    cursor.execute(q3)
    conn.commit()


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5002)