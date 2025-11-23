from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import random
import math

app = Flask(__name__)
CORS(app)

DATABASE = 'smartmatch.db'


# database init
#=====================================

def get_db():
    """Create database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise database with tables and sample data (only if not exists)"""
    conn = get_db()
    cursor = conn.cursor()
    
    # check if database already has data
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clubs'")
    if cursor.fetchone():
        print("Database already exists. Skipping initialisation to preserve data.")
        conn.close()
        return
    
    # create tables
    cursor.execute("""
        CREATE TABLE clubs (
            club_id INTEGER PRIMARY KEY,
            club_name TEXT NOT NULL,
            club_color TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE players (
            player_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            club_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (club_id) REFERENCES clubs(club_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE courts (
            court_id INTEGER PRIMARY KEY,
            court_name TEXT NOT NULL,
            court_color TEXT NOT NULL,
            status TEXT DEFAULT 'Active'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE matches (
            match_id TEXT PRIMARY KEY,
            match_code TEXT UNIQUE NOT NULL,
            court_id INTEGER NOT NULL,
            player_a_id TEXT,
            player_b_id TEXT,
            round TEXT NOT NULL,
            scheduled_time TIMESTAMP NOT NULL,
            duration_minutes INTEGER DEFAULT 30,
            status TEXT DEFAULT 'Upcoming',
            score_a INTEGER DEFAULT 0,
            score_b INTEGER DEFAULT 0,
            winner_id TEXT,
            is_bye INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (court_id) REFERENCES courts(court_id),
            FOREIGN KEY (player_a_id) REFERENCES players(player_id),
            FOREIGN KEY (player_b_id) REFERENCES players(player_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE rest_periods (
            rest_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            match_before_id TEXT,
            match_after_id TEXT,
            rest_start_time TIMESTAMP NOT NULL,
            rest_end_time TIMESTAMP NOT NULL,
            rest_duration_min INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(player_id),
            FOREIGN KEY (match_before_id) REFERENCES matches(match_id),
            FOREIGN KEY (match_after_id) REFERENCES matches(match_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE tournament_stats (
            stat_id INTEGER PRIMARY KEY,
            total_players INTEGER DEFAULT 0,
            total_matches INTEGER DEFAULT 0,
            active_courts INTEGER DEFAULT 0,
            matches_completed INTEGER DEFAULT 0,
            matches_live INTEGER DEFAULT 0,
            matches_upcoming INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # insert sample data
    clubs_data = [
        (1, 'Club A', 'blue'),
        (2, 'Club B', 'purple'),
        (3, 'Club C', 'green'),
        (4, 'Club D', 'orange')
    ]
    cursor.executemany("INSERT INTO clubs VALUES (?, ?, ?)", clubs_data)
    
    courts_data = [
        (1, 'Court 1', 'purple', 'Active'),
        (2, 'Court 2', 'blue', 'Active'),
        (3, 'Court 3', 'green', 'Active')
    ]
    cursor.executemany("INSERT INTO courts VALUES (?, ?, ?, ?)", courts_data)
    
    players_data = [
        ('PL-001', 'Rohan Sharma', 1, "Men's Singles", 'Active'),
        ('PL-002', 'Priya Patel', 2, "Women's Singles", 'Active'),
        ('PL-003', 'Arjun Kumar', 1, "Men's Singles", 'Active'),
        ('PL-004', 'Sneha Reddy', 3, "Women's Singles", 'Active'),
        ('PL-005', 'Vikram Singh', 4, "Men's Singles", 'Active'),
        ('PL-006', 'Aditya Verma', 3, "Men's Singles", 'Active'),
        ('PL-007', 'Karthik Iyer', 2, "Men's Singles", 'Active'),
        ('PL-008', 'Rahul Joshi', 4, "Men's Singles", 'Active'),
        ('PL-009', 'Sanjay Mehta', 2, "Men's Singles", 'Active'),
        ('PL-010', 'Anita Kumar', 1, "Women's Singles", 'Active'),
        ('PL-011', 'Kavya Nair', 3, "Women's Singles", 'Active'),
        ('PL-012', 'Deepa Singh', 4, "Women's Singles", 'Active'),
        ('PL-013', 'Riya Gupta', 2, "Women's Singles", 'Active'),
        ('PL-014', 'Nitin Desai', 1, "Men's Singles", 'Active'),
        ('PL-015', 'Varun Reddy', 3, "Men's Singles", 'Active'),
        ('PL-016', 'Manoj Kumar', 4, "Men's Singles", 'Active'),
        ('PL-017', 'Ashok Patel', 2, "Men's Singles", 'Active'),
        ('PL-018', 'Dinesh Rao', 1, "Men's Singles", 'Active')
    ]
    cursor.executemany("INSERT INTO players (player_id, name, club_id, category, status) VALUES (?, ?, ?, ?, ?)", players_data)
    
    # using today's date for matches
    today = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    
    matches_data = [
        ('M-101', '847391', 1, 'PL-001', 'PL-005', 'Round of 16', today, 30, 'Completed', 3, 1, 'PL-001', 0),
        ('M-102', '847392', 1, 'PL-003', 'PL-006', 'Round of 16', today + timedelta(minutes=40), 30, 'Live', 0, 0, None, 0),
        ('M-103', '847393', 1, 'PL-007', 'PL-008', 'Round of 16', today + timedelta(minutes=80), 30, 'Upcoming', 0, 0, None, 0),
        
        ('M-201', '847394', 2, 'PL-002', 'PL-004', 'Round of 16', today + timedelta(minutes=15), 30, 'Completed', 3, 2, 'PL-002', 0),
        ('M-202', '847395', 2, 'PL-010', 'PL-011', 'Round of 16', today + timedelta(minutes=55), 30, 'Upcoming', 0, 0, None, 0),
        ('M-203', '847396', 2, 'PL-012', 'PL-013', 'Round of 16', today + timedelta(minutes=95), 30, 'Upcoming', 0, 0, None, 0),
        
        ('M-301', '847397', 3, 'PL-009', 'PL-014', 'Round of 16', today, 30, 'Completed', 3, 1, 'PL-009', 0),
        ('M-302', '847398', 3, 'PL-015', 'PL-016', 'Round of 16', today + timedelta(minutes=40), 30, 'Completed', 3, 2, 'PL-015', 0),
        ('M-303', '847399', 3, 'PL-017', 'PL-018', 'Round of 16', today + timedelta(minutes=80), 30, 'Upcoming', 0, 0, None, 0),
        
        ('M-401', '847400', 1, 'PL-001', 'PL-006', 'Quarter Finals', today + timedelta(minutes=120), 30, 'Upcoming', 0, 0, None, 0),
        ('M-402', '847401', 2, 'PL-007', None, 'Quarter Finals', today + timedelta(minutes=120), 0, 'Upcoming', 0, 0, 'PL-007', 1)
    ]
    
    cursor.executemany("""
        INSERT INTO matches (match_id, match_code, court_id, player_a_id, player_b_id, round, 
                           scheduled_time, duration_minutes, status, score_a, score_b, winner_id, is_bye)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, matches_data)
    
    rest_data = [
        ('PL-001', 'M-101', 'M-401', today + timedelta(minutes=30), today + timedelta(minutes=40), 10),
        ('PL-006', 'M-102', 'M-401', today + timedelta(minutes=70), today + timedelta(minutes=80), 10),
        ('PL-002', 'M-201', None, today + timedelta(minutes=45), today + timedelta(minutes=55), 10)
    ]
    
    cursor.executemany("""
        INSERT INTO rest_periods (player_id, match_before_id, match_after_id, rest_start_time, rest_end_time, rest_duration_min)
        VALUES (?, ?, ?, ?, ?, ?)
    """, rest_data)
    
    cursor.execute("""
        INSERT INTO tournament_stats (stat_id, total_players, total_matches, active_courts, 
                                     matches_completed, matches_live, matches_upcoming)
        VALUES (1, 18, 11, 5, 3, 2, 10)
    """)
    
    conn.commit()
    conn.close()
    print("Database initialised successfully!")


def add_category_to_matches():
    """Add category column to matches table"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(matches)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'category' not in columns:
            cursor.execute("ALTER TABLE matches ADD COLUMN category TEXT")
            print("Added category column to matches")
            conn.commit()
        else:
            print("Category column already exists")
            
    except Exception as e:
        print(f"Error adding category column: {e}")
    finally:
        conn.close()


# api endpoints
#=================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "SmartMatch API is running"})


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get tournament statistics for admin dashboard"""
    conn = get_db()
    cursor = conn.cursor()
    
    stats = cursor.execute("""
        SELECT total_players, total_matches, active_courts,
               matches_completed, matches_live, matches_upcoming
        FROM tournament_stats WHERE stat_id = 1
    """).fetchone()
    
    conn.close()
    return jsonify(dict(stats))

@app.route('/api/players', methods=['GET'])
def get_players():
    """Get all players with club information (with pagination)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    offset = (page - 1) * per_page
    
    conn = get_db()
    cursor = conn.cursor()
    
    total = cursor.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    
    players = cursor.execute("""
        SELECT p.player_id, p.name, c.club_name, c.club_color, p.category, p.status
        FROM players p
        JOIN clubs c ON p.club_id = c.club_id
        ORDER BY p.player_id DESC
        LIMIT ? OFFSET ?
    """, (per_page, offset)).fetchall()
    
    conn.close()
    return jsonify({
        "players": [dict(row) for row in players],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page
    })

@app.route('/api/players', methods=['POST'])
def add_player():
    """Add a new player with category limit validation"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # check if category already has 16 players
        category = data.get('category', 'Men\'s Singles')
        player_count = cursor.execute("""
            SELECT COUNT(*) as count 
            FROM players 
            WHERE category = ? AND status = 'Active'
        """, (category,)).fetchone()
        
        if player_count['count'] >= 16:
            conn.close()
            return jsonify({
                "success": False,
                "error": f"Maximum 16 players allowed per category. {category} already has 16 active players."
            }), 400
        
        if not data.get('name') or not data.get('club_id') or not category:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Name, club, and category are required"
            }), 400
        
        # generate new player id
        if not data.get('player_id'):
            last_id = cursor.execute("SELECT player_id FROM players ORDER BY player_id DESC LIMIT 1").fetchone()
            if last_id:
                last_num = int(last_id[0].split('-')[1])
                data['player_id'] = f"PL-{str(last_num + 1).zfill(3)}"
            else:
                data['player_id'] = "PL-001"
        
        cursor.execute("""
            INSERT INTO players (player_id, name, club_id, category, status)
            VALUES (?, ?, ?, ?, ?)
        """, (data['player_id'], data['name'], data['club_id'], 
              category, data.get('status', 'Active')))
        
        conn.commit()
        
        cursor.execute("""
            UPDATE tournament_stats 
            SET total_players = total_players + 1, 
                last_updated = CURRENT_TIMESTAMP
            WHERE stat_id = 1
        """)
        
        conn.commit()
        
        player_id = data['player_id']
        
        updated_count = cursor.execute("""
            SELECT COUNT(*) as count 
            FROM players 
            WHERE category = ? AND status = 'Active'
        """, (category,)).fetchone()
        
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": "Player added successfully", 
            "player_id": player_id,
            "category": category,
            "category_count": updated_count['count'],
            "remaining_slots": 16 - updated_count['count']
        })
        
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400
    

@app.route('/api/fixtures', methods=['GET'])
def get_fixtures():
    """Get tournament bracket with all match details"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        fixtures = cursor.execute("""
            SELECT 
                m.match_id,
                m.round,
                m.is_bye,
                m.category,
                pa.player_id as player_a_id,
                COALESCE(pa.name, 'TBD') as player_a_name,
                COALESCE(ca.club_name, '') as player_a_club,
                COALESCE(ca.club_color, 'gray') as player_a_color,
                pb.player_id as player_b_id,
                COALESCE(pb.name, 'TBD') as player_b_name,
                COALESCE(cb.club_name, '') as player_b_club,
                COALESCE(cb.club_color, 'gray') as player_b_color,
                m.score_a,
                m.score_b,
                m.status,
                m.winner_id
            FROM matches m
            LEFT JOIN players pa ON m.player_a_id = pa.player_id
            LEFT JOIN clubs ca ON pa.club_id = ca.club_id
            LEFT JOIN players pb ON m.player_b_id = pb.player_id
            LEFT JOIN clubs cb ON pb.club_id = cb.club_id
            ORDER BY 
                m.category,
                CASE m.round
                    WHEN 'Round of 16' THEN 1
                    WHEN 'Quarter Finals' THEN 2
                    WHEN 'Semi Finals' THEN 3
                    WHEN 'Finals' THEN 4
                    ELSE 5
                END,
                m.match_id
        """).fetchall()
        
        conn.close()
        return jsonify([dict(row) for row in fixtures])
        
    except Exception as e:
        conn.close()
        print(f"Error in get_fixtures: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    


@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    """Get scheduled matches including TBD (Future Matches)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # left joins with coalesce ensure tbd matches appear
        schedule = cursor.execute("""
            SELECT 
                m.match_id, m.match_code, m.scheduled_time, m.duration_minutes, m.status,
                m.round, m.score_a, m.score_b,
                c.court_id, c.court_name,
                m.player_a_id,
                COALESCE(pa.name, 'TBD') as player_a_name, 
                m.category,
                COALESCE(ca.club_name, 'Pending') as player_a_club,
                COALESCE(ca.club_color, 'gray') as player_a_color,
                m.player_b_id,
                COALESCE(pb.name, 'TBD') as player_b_name,
                COALESCE(cb.club_name, 'Pending') as player_b_club,
                COALESCE(cb.club_color, 'gray') as player_b_color
            FROM matches m
            JOIN courts c ON m.court_id = c.court_id
            LEFT JOIN players pa ON m.player_a_id = pa.player_id
            LEFT JOIN clubs ca ON pa.club_id = ca.club_id
            LEFT JOIN players pb ON m.player_b_id = pb.player_id
            LEFT JOIN clubs cb ON pb.club_id = cb.club_id
            WHERE m.status IN ('Upcoming', 'Live', 'Completed') 
                AND m.is_bye = 0
                AND m.scheduled_time IS NOT NULL
            ORDER BY m.scheduled_time, c.court_id
        """).fetchall()

        current_time = datetime.now()
        matches_data = []
        rest_buffer = 10
        
        for row in schedule:
            match = dict(row)
            scheduled_time = datetime.strptime(match['scheduled_time'], '%Y-%m-%d %H:%M:%S')
            
            # simple duration logic (assuming schedule logic handles gaps)
            if match['status'] == 'Live':
                 match['actual_duration'] = max(match['duration_minutes'], int((current_time - scheduled_time).total_seconds() / 60))
            else:
                 match['actual_duration'] = match['duration_minutes']
            
            match['actual_start_time'] = match['scheduled_time']
            matches_data.append(match)
            
        conn.close()
        return jsonify({
            "matches": matches_data,
            "rest_buffer": rest_buffer,
            "current_time": current_time.strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/rest-periods', methods=['GET'])
def get_rest_periods():
    """Get today's rest periods"""
    conn = get_db()
    cursor = conn.cursor()
    
    rest_periods = cursor.execute("""
        SELECT 
            rp.rest_id,
            rp.player_id,
            p.name as player_name,
            rp.rest_start_time,
            rp.rest_end_time,
            rp.rest_duration_min,
            rp.match_before_id,
            rp.match_after_id,
            m1.court_id
        FROM rest_periods rp
        JOIN players p ON rp.player_id = p.player_id
        LEFT JOIN matches m1 ON rp.match_before_id = m1.match_id
        WHERE DATE(rp.rest_start_time) = DATE('now')
        ORDER BY rp.rest_start_time
    """).fetchall()
    
    conn.close()
    return jsonify([dict(row) for row in rest_periods])


@app.route('/api/validate-code', methods=['POST'])
def validate_match_code():
    """Validate umpire match code"""
    data = request.json
    match_code = data.get('match_code')
    
    if not match_code or len(match_code) != 6:
        return jsonify({"success": False, "error": "Invalid match code format"}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    match = cursor.execute("""
        SELECT 
            m.match_id,
            m.match_code,
            m.court_id,
            c.court_name,
            m.round,
            pa.name as player_a_name,
            ca.club_name as player_a_club,
            pb.name as player_b_name,
            cb.club_name as player_b_club,
            m.score_a,
            m.score_b,
            m.status
        FROM matches m
        JOIN courts c ON m.court_id = c.court_id
        LEFT JOIN players pa ON m.player_a_id = pa.player_id
        LEFT JOIN clubs ca ON pa.club_id = ca.club_id
        LEFT JOIN players pb ON m.player_b_id = pb.player_id
        LEFT JOIN clubs cb ON pb.club_id = cb.club_id
        WHERE m.match_code = ? AND m.status != 'Completed'
    """, (match_code,)).fetchone()
    
    conn.close()
    
    if match:
        return jsonify({"success": True, "match": dict(match)})
    else:
        return jsonify({"success": False, "error": "Invalid or expired match code"}), 404


@app.route('/api/admin/sync-bracket', methods=['GET'])
def sync_bracket():
    """
    super sync: 
    1. fixes missing winner_ids based on scores.
    2. pushes winners to next round.
    3. fixes byes.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        matches = cursor.execute("SELECT * FROM matches").fetchall()
        
        updates = 0
        
        for m in matches:
            match_id = m['match_id']
            winner_id = m['winner_id']
            status = m['status']
            
            # fix missing winners - if completed but no winner_id, infer it from scores
            if status == 'Completed' and not winner_id:
                if m['score_a'] > m['score_b']:
                    winner_id = m['player_a_id']
                elif m['score_b'] > m['score_a']:
                    winner_id = m['player_b_id']
                
                if winner_id:
                    print(f"Repaired missing winner for {match_id}: {winner_id}")
                    cursor.execute("UPDATE matches SET winner_id = ? WHERE match_id = ?", (winner_id, match_id))
                    updates += 1

            # handle byes
            if m['is_bye'] == 1 and status != 'Completed':
                winner_id = m['player_a_id']
                print(f"Auto-completing BYE {match_id}")
                cursor.execute("""
                    UPDATE matches 
                    SET status = 'Completed', winner_id = ?, score_a = 0, score_b = 0 
                    WHERE match_id = ?
                """, (winner_id, match_id))
                updates += 1

            # advance to next round - find match where this match is a parent
            if winner_id:
                next_match = cursor.execute("""
                    SELECT match_id, parent_match_a, parent_match_b, player_a_id, player_b_id
                    FROM matches 
                    WHERE parent_match_a = ? OR parent_match_b = ?
                """, (match_id, match_id)).fetchone()
                
                if next_match:
                    next_id = next_match['match_id']
                    
                    if next_match['parent_match_a'] == match_id:
                        if next_match['player_a_id'] != winner_id:
                            print(f"Advancing {winner_id} to {next_id} (A)")
                            cursor.execute("UPDATE matches SET player_a_id = ? WHERE match_id = ?", (winner_id, next_id))
                            updates += 1
                    elif next_match['parent_match_b'] == match_id:
                        if next_match['player_b_id'] != winner_id:
                            print(f"Advancing {winner_id} to {next_id} (B)")
                            cursor.execute("UPDATE matches SET player_b_id = ? WHERE match_id = ?", (winner_id, next_id))
                            updates += 1

        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"Super Sync Complete. {updates} updates performed."
        })
        
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/update-match-statuses', methods=['POST'])
def update_match_statuses():
    """
    aggressive match starter - no rest buffer enforcement
    if the time has come and the court is empty, start it.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        current_time = datetime.now()
        
        # find matches that are ready to start
        candidates = cursor.execute("""
            SELECT m.match_id, m.court_id, m.scheduled_time
            FROM matches m
            WHERE m.status = 'Upcoming' 
              AND m.is_bye = 0
              AND m.scheduled_time IS NOT NULL
              AND datetime(m.scheduled_time) <= datetime(?)
        """, (current_time.strftime('%Y-%m-%d %H:%M:%S'),)).fetchall()
        
        started_count = 0
        started_ids = []

        for match in candidates:
            court_id = match['court_id']
            
            # strict check: is the court physically occupied?
            # only care if there is a match marked 'live' on this court
            # don't check for rest buffers here. if previous match is 'completed', 
            # assume the court is available immediately for the sake of the schedule.
            is_court_busy = cursor.execute("""
                SELECT 1 FROM matches 
                WHERE court_id = ? AND status = 'Live' AND is_bye = 0
            """, (court_id,)).fetchone()
            
            if is_court_busy:
                continue 
            
            # court is free - start the match
            cursor.execute("UPDATE matches SET status = 'Live' WHERE match_id = ?", (match['match_id'],))
            started_count += 1
            started_ids.append(match['match_id'])

        if started_count > 0:
            cursor.execute("""
                UPDATE tournament_stats
                SET matches_live = matches_live + ?,
                    matches_upcoming = matches_upcoming - ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE stat_id = 1
            """, (started_count, started_count))
            
        conn.commit()
        conn.close()
        
        return jsonify({ "success": True, "matches_made_live": started_count, "match_ids": started_ids })
        
    except Exception as e:
        conn.close()
        print(f"Error in update_match_statuses: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/validate-code', methods=['POST'])
def validate_code():
    """Validate match code and check if match is live"""
    data = request.json
    match_code = data.get('match_code')
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        current_time = datetime.now()
        
        # find matches that should transition to live
        # only transition if no other match is live on the same court
        courts_with_live = cursor.execute("""
            SELECT DISTINCT court_id 
            FROM matches 
            WHERE status = 'Live' AND is_bye = 0
        """).fetchall()
        
        occupied_courts = {c['court_id'] for c in courts_with_live}
        
        cursor.execute("""
            UPDATE matches 
            SET status = 'Live'
            WHERE status = 'Upcoming' 
                AND is_bye = 0
                AND scheduled_time IS NOT NULL
                AND datetime(scheduled_time) <= datetime(?)
                AND court_id NOT IN (
                    SELECT court_id FROM matches WHERE status = 'Live' AND is_bye = 0
                )
        """, (current_time.strftime('%Y-%m-%d %H:%M:%S'),))
        
        conn.commit()
        
        # now validate the match code
        match = cursor.execute("""
            SELECT 
                m.match_id, m.match_code, m.status, m.score_a, m.score_b,
                m.round, m.scheduled_time, m.is_bye, m.court_id,
                c.court_name,
                pa.player_id as player_a_id, pa.name as player_a_name,
                ca.club_name as player_a_club,
                pb.player_id as player_b_id, pb.name as player_b_name,
                cb.club_name as player_b_club
            FROM matches m
            LEFT JOIN courts c ON m.court_id = c.court_id
            JOIN players pa ON m.player_a_id = pa.player_id
            LEFT JOIN clubs ca ON pa.club_id = ca.club_id
            LEFT JOIN players pb ON m.player_b_id = pb.player_id
            LEFT JOIN clubs cb ON pb.club_id = cb.club_id
            WHERE m.match_code = ?
        """, (match_code,)).fetchone()
        
        if not match:
            conn.close()
            return jsonify({
                "success": False,
                "error": "Invalid match code"
            }), 404
        
        # check if match is live
        if match['status'] != 'Live':
            scheduled_time_str = match['scheduled_time']
            
            if match['status'] == 'Upcoming' and scheduled_time_str:
                scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%d %H:%M:%S')
                
                # check if time has passed but court is occupied
                if current_time >= scheduled_time:
                    court_occupied = cursor.execute("""
                        SELECT match_id FROM matches 
                        WHERE court_id = ? AND status = 'Live' AND is_bye = 0 AND match_id != ?
                    """, (match['court_id'], match['match_id'])).fetchone()
                    
                    if court_occupied:
                        conn.close()
                        return jsonify({
                            "success": False,
                            "error": f"Court {match['court_id']} is currently occupied. Please wait for the previous match to finish."
                        }), 400
                else:
                    time_until = scheduled_time - current_time
                    minutes_until = int(time_until.total_seconds() / 60)
                    conn.close()
                    return jsonify({
                        "success": False,
                        "error": f"Match is not live yet. Starts in {minutes_until} minutes at {scheduled_time.strftime('%H:%M')}"
                    }), 400
            
            conn.close()
            return jsonify({
                "success": False,
                "error": f"Match is {match['status']}, not Live"
            }), 400
        
        conn.close()
        return jsonify({
            "success": True,
            "match": dict(match)
        })
        
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500
    

@app.route('/api/update-score', methods=['POST'])
def update_score():
    """Update live match score - only works for Live matches"""
    data = request.json
    match_code = data.get('match_code')
    score_a = data.get('score_a')
    score_b = data.get('score_b')
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        match = cursor.execute("""
            SELECT status FROM matches WHERE match_code = ?
        """, (match_code,)).fetchone()
        
        if not match:
            conn.close()
            return jsonify({"success": False, "error": "Invalid match code"}), 404
        
        if match['status'] != 'Live':
            conn.close()
            return jsonify({
                "success": False, 
                "error": "Can only update scores for live matches"
            }), 400
        
        cursor.execute("""
            UPDATE matches 
            SET score_a = ?, score_b = ?
            WHERE match_code = ?
        """, (score_a, score_b, match_code))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
        
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/submit-result', methods=['POST'])
def submit_result():
    data = request.json
    match_code = data.get('match_code')
    score_a = int(data.get('score_a', 0))
    score_b = int(data.get('score_b', 0))
    ui_duration = data.get('actual_duration', 30)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        match = cursor.execute("SELECT * FROM matches WHERE match_code = ?", (match_code,)).fetchone()
        if not match:
            return jsonify({"success": False, "error": "Invalid code"}), 404
            
        match_id = match['match_id']
        winner_id = match['player_a_id'] if score_a > score_b else match['player_b_id']
        final_duration = max(match['duration_minutes'], int(ui_duration), 30)

        cursor.execute("""
            UPDATE matches SET score_a=?, score_b=?, winner_id=?, status='Completed', duration_minutes=? 
            WHERE match_id=?
        """, (score_a, score_b, winner_id, final_duration, match_id))
        
        # recursive advancement logic - loop to handle consecutive byes
        current_winner = winner_id
        current_match_id = match_id
        
        while True:
            next_match = cursor.execute("""
                SELECT match_id, parent_match_a, parent_match_b, is_bye 
                FROM matches WHERE parent_match_a = ? OR parent_match_b = ?
            """, (current_match_id, current_match_id)).fetchone()
            
            if not next_match:
                break
                
            next_id = next_match['match_id']
            
            # place winner in next match
            if next_match['parent_match_a'] == current_match_id:
                cursor.execute("UPDATE matches SET player_a_id = ? WHERE match_id = ?", (current_winner, next_id))
            else:
                cursor.execute("UPDATE matches SET player_b_id = ? WHERE match_id = ?", (current_winner, next_id))
            
            # check if next match is a bye
            if next_match['is_bye'] == 1:
                print(f"Auto-advancing {current_winner} through BYE {next_id}")
                cursor.execute("""
                    UPDATE matches SET status='Completed', winner_id=?, score_a=0, score_b=0 
                    WHERE match_id=?
                """, (current_winner, next_id))
                current_match_id = next_id
            else:
                break

        cursor.execute("UPDATE tournament_stats SET matches_live = matches_live - 1, matches_completed = matches_completed + 1 WHERE stat_id = 1")
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Updated"})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/api/match/<match_code>', methods=['GET'])
def get_match_details(match_code):
    """Get detailed match information"""
    conn = get_db()
    cursor = conn.cursor()
    
    match = cursor.execute("""
        SELECT 
            m.*,
            c.court_name,
            pa.name as player_a_name,
            pb.name as player_b_name,
            ca.club_name as player_a_club,
            cb.club_name as player_b_club
        FROM matches m
        JOIN courts c ON m.court_id = c.court_id
        LEFT JOIN players pa ON m.player_a_id = pa.player_id
        LEFT JOIN players pb ON m.player_b_id = pb.player_id
        LEFT JOIN clubs ca ON pa.club_id = ca.club_id
        LEFT JOIN clubs cb ON pb.club_id = cb.club_id
        WHERE m.match_code = ?
    """, (match_code,)).fetchone()
    
    conn.close()
    
    if match:
        return jsonify(dict(match))
    else:
        return jsonify({"error": "Match not found"}), 404


@app.route('/api/clubs', methods=['GET'])
def get_clubs():
    """Get all clubs"""
    conn = get_db()
    cursor = conn.cursor()
    clubs = cursor.execute("SELECT * FROM clubs").fetchall()
    conn.close()
    return jsonify([dict(row) for row in clubs])

@app.route('/api/courts', methods=['GET'])
def get_courts():
    """Get all courts"""
    conn = get_db()
    cursor = conn.cursor()
    courts = cursor.execute("SELECT * FROM courts WHERE status = 'Active'").fetchall()
    conn.close()
    return jsonify([dict(row) for row in courts])

@app.route('/api/players/<player_id>', methods=['DELETE'])
def delete_player(player_id):
    """Delete a player safely with foreign key checks"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        player = cursor.execute(
            "SELECT * FROM players WHERE player_id = ?", 
            (player_id,)
        ).fetchone()
        
        if not player:
            conn.close()
            return jsonify({
                "success": False, 
                "error": "Player not found"
            }), 404
        
        # check if player in a match
        matches_as_player_a = cursor.execute(
            "SELECT COUNT(*) FROM matches WHERE player_a_id = ?",
            (player_id,)
        ).fetchone()[0]
        
        matches_as_player_b = cursor.execute(
            "SELECT COUNT(*) FROM matches WHERE player_b_id = ?",
            (player_id,)
        ).fetchone()[0]
        
        total_matches = matches_as_player_a + matches_as_player_b
        
        # player is not in any match
        if total_matches == 0:
            cursor.execute(
                "DELETE FROM rest_periods WHERE player_id = ?",
                (player_id,)
            )
            
            cursor.execute(
                "DELETE FROM players WHERE player_id = ?",
                (player_id,)
            )
            
            cursor.execute("""
                UPDATE tournament_stats 
                SET total_players = total_players - 1,
                    last_updated = CURRENT_TIMESTAMP
                WHERE stat_id = 1
            """)
            
            conn.commit()
            conn.close()
            
            return jsonify({
                "success": True,
                "message": f"Player {player_id} deleted successfully",
                "scenario": "no_matches"
            })
        
        # player in match: time to cascade delete
        else:
            matches = cursor.execute("""
                SELECT match_id, round, status, scheduled_time
                FROM matches 
                WHERE player_a_id = ? OR player_b_id = ?
                ORDER BY scheduled_time
            """, (player_id, player_id)).fetchall()
            
            conn.close()
            
            return jsonify({
                "success": False,
                "error": "Player is registered in matches",
                "scenario": "has_matches",
                "match_count": total_matches,
                "matches": [dict(m) for m in matches],
                "message": f"This player is in {total_matches} match(es). Use force delete to remove."
            }), 409
            
    except Exception as e:
        conn.close()
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500


@app.route('/api/players/<player_id>/force', methods=['DELETE'])
def force_delete_player(player_id):
    """Force delete player and cascade remove from all related tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        player = cursor.execute(
            "SELECT name FROM players WHERE player_id = ?", 
            (player_id,)
        ).fetchone()
        
        if not player:
            conn.close()
            return jsonify({
                "success": False, 
                "error": "Player not found"
            }), 404
        
        player_name = player[0]
        
        # find every match player is in
        matches = cursor.execute("""
            SELECT match_id FROM matches 
            WHERE player_a_id = ? OR player_b_id = ?
        """, (player_id, player_id)).fetchall()
        
        match_ids = [m[0] for m in matches]
        match_count = len(match_ids)
        
        cursor.execute(
            "DELETE FROM rest_periods WHERE player_id = ?",
            (player_id,)
        )
        
        if match_count > 0:
            # delete matches entirely
            placeholders = ','.join('?' * len(match_ids))
            cursor.execute(
                f"DELETE FROM rest_periods WHERE match_before_id IN ({placeholders}) OR match_after_id IN ({placeholders})",
                match_ids + match_ids
            )
            cursor.execute(
                f"DELETE FROM matches WHERE match_id IN ({placeholders})",
                match_ids
            )
            
            cursor.execute("""
                UPDATE tournament_stats 
                SET total_matches = total_matches - ?,
                    matches_upcoming = matches_upcoming - ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE stat_id = 1
            """, (match_count, match_count))
        
        cursor.execute(
            "DELETE FROM players WHERE player_id = ?",
            (player_id,)
        )
        
        cursor.execute("""
            UPDATE tournament_stats 
            SET total_players = total_players - 1,
                last_updated = CURRENT_TIMESTAMP
            WHERE stat_id = 1
        """)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Player '{player_name}' and {match_count} associated match(es) deleted successfully",
            "deleted": {
                "player_id": player_id,
                "player_name": player_name,
                "matches_deleted": match_count
            }
        })
        
    except Exception as e:
        conn.close()
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500
    
@app.route('/api/players/force', methods=['DELETE'])
def reset_players():
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        players = cursor.execute("SELECT player_id, name FROM players").fetchall()
        
        if not players:
            conn.close()
            return jsonify({
                "success": True,
                "message": "No players to delete"
            })
        
        deleted_count = 0
        total_matches_deleted = 0
        
        for player_id, player_name in players:
            matches = cursor.execute("""
                SELECT match_id FROM matches 
                WHERE player_a_id = ? OR player_b_id = ?
            """, (player_id, player_id)).fetchall()
            match_ids = [m[0] for m in matches]
            match_count = len(match_ids)
            
            cursor.execute(
                "DELETE FROM rest_periods WHERE player_id = ?",
                (player_id,)
            )
            
            if match_count > 0:
                placeholders = ','.join('?' * len(match_ids))
                cursor.execute(
                    f"DELETE FROM rest_periods WHERE match_before_id IN ({placeholders}) OR match_after_id IN ({placeholders})",
                    match_ids + match_ids
                )
                cursor.execute(
                    f"DELETE FROM matches WHERE match_id IN ({placeholders})",
                    match_ids
                )
                total_matches_deleted += match_count
            
            cursor.execute(
                "DELETE FROM players WHERE player_id = ?",
                (player_id,)
            )
            deleted_count += 1
        
        cursor.execute("""
            UPDATE tournament_stats 
            SET total_players = 0,
                total_matches = 0,
                matches_upcoming = 0,
                last_updated = CURRENT_TIMESTAMP
            WHERE stat_id = 1
        """)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "All players deleted successfully",
            "deleted": {
                "players_deleted": deleted_count,
                "matches_deleted": total_matches_deleted
            }
        })
        
    except Exception as e:
        conn.close()
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500


# fixture generation api
#=============================================

@app.route('/api/generate-fixtures', methods=['POST'])
def generate_fixtures():
    data = request.json
    category = data.get('category', 'Men\'s Singles')
    match_duration = data.get('match_duration', 30)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # delete existing fixtures for this category
        existing_fixtures = cursor.execute("""
            SELECT COUNT(*) as count
            FROM matches m
            JOIN players p ON m.player_a_id = p.player_id
            WHERE p.category = ?
        """, (category,)).fetchone()
        
        if existing_fixtures['count'] > 0:
            print(f"deleting {existing_fixtures['count']} existing fixtures for {category}")
            match_ids_to_delete = cursor.execute("""
                SELECT m.match_id FROM matches m
                JOIN players p ON m.player_a_id = p.player_id
                WHERE p.category = ?
            """, (category,)).fetchall()
            
            match_ids = [m['match_id'] for m in match_ids_to_delete]
            
            if match_ids:
                placeholders = ','.join('?' * len(match_ids))
                cursor.execute(f"DELETE FROM rest_periods WHERE match_before_id IN ({placeholders}) OR match_after_id IN ({placeholders})", match_ids + match_ids)
                cursor.execute(f"DELETE FROM matches WHERE match_id IN ({placeholders})", match_ids)
                cursor.execute("UPDATE tournament_stats SET total_matches = total_matches - ?, matches_upcoming = matches_upcoming - ?, last_updated = CURRENT_TIMESTAMP WHERE stat_id = 1", (len(match_ids), len(match_ids)))
                conn.commit()
        
        # setup counters & players
        existing_match = cursor.execute("SELECT match_id FROM matches ORDER BY match_id DESC LIMIT 1").fetchone()
        last_match_num = int(existing_match['match_id'].split('-')[1]) if existing_match else 0
        match_counter = last_match_num + 1
        
        players = cursor.execute("""
            SELECT p.player_id, p.name, p.club_id, c.club_name
            FROM players p
            JOIN clubs c ON p.club_id = c.club_id
            WHERE p.status = 'Active' AND p.category = ?
            ORDER BY p.player_id
        """, (category,)).fetchall()
        
        if len(players) < 2:
            conn.close()
            return jsonify({"success": False, "error": "Need at least 2 players"}), 400
        
        player_list = [dict(p) for p in players]
        total_players = len(player_list)
        bracket_size = 2 ** math.ceil(math.log2(total_players))
        
        round_names = {
            2: ['Finals'],
            4: ['Semi Finals', 'Finals'],
            8: ['Quarter Finals', 'Semi Finals', 'Finals'],
            16: ['Round of 16', 'Quarter Finals', 'Semi Finals', 'Finals'],
            32: ['Round of 32', 'Round of 16', 'Quarter Finals', 'Semi Finals', 'Finals']
        }
        rounds = round_names.get(bracket_size, ['Round of 16', 'Quarter Finals', 'Semi Finals', 'Finals'])
        first_round = rounds[0]
        
        # pairing logic with club avoidance
        club_groups = {}
        for player in player_list:
            if player['club_id'] not in club_groups: club_groups[player['club_id']] = []
            club_groups[player['club_id']].append(player)
        
        sorted_clubs = sorted(club_groups.items(), key=lambda x: len(x[1]), reverse=True)
        paired_players = []
        club_indices = {cid: 0 for cid, _ in sorted_clubs}
        
        while len(paired_players) < len(player_list):
            for cid, p_list in sorted_clubs:
                if club_indices[cid] < len(p_list):
                    paired_players.append(p_list[club_indices[cid]])
                    club_indices[cid] += 1
        
        # generate bracket structure
        all_matches = []
        current_round_participants = []
        
        if total_players % 2 == 0:
            num_first_round = total_players // 2
            num_byes = 0
        else:
            num_first_round = (total_players - 1) // 2
            num_byes = 1
            
        # first round matches
        for i in range(num_first_round):
            match_id = f'M-{match_counter:03d}'
            all_matches.append({
                'match_id': match_id, 'match_code': f'{random.randint(100000, 999999)}',
                'player_a_id': paired_players[i*2]['player_id'],
                'player_b_id': paired_players[i*2+1]['player_id'],
                'round': first_round, 'is_bye': 0,
                'parent_match_a': None, 'parent_match_b': None
            })
            current_round_participants.append(match_id)
            match_counter += 1
            
        # first round byes
        for i in range(num_byes):
            match_id = f'M-{match_counter:03d}'
            all_matches.append({
                'match_id': match_id, 'match_code': f'{random.randint(100000, 999999)}',
                'player_a_id': paired_players[num_first_round*2+i]['player_id'],
                'player_b_id': None,
                'round': first_round, 'is_bye': 1,
                'parent_match_a': None, 'parent_match_b': None
            })
            current_round_participants.append(match_id)
            match_counter += 1
            
        # subsequent rounds
        for round_idx in range(1, len(rounds)):
            round_name = rounds[round_idx]
            next_round_participants = []
            
            for i in range(0, len(current_round_participants), 2):
                parent_a = current_round_participants[i]
                parent_b = current_round_participants[i+1] if i+1 < len(current_round_participants) else None
                
                # propagate bye flag: if parent_b is missing, this match is strictly a bye
                is_propagated_bye = 1 if parent_b is None else 0
                
                match_id = f'M-{match_counter:03d}'
                all_matches.append({
                    'match_id': match_id, 'match_code': f'{random.randint(100000, 999999)}',
                    'player_a_id': None, 'player_b_id': None,
                    'round': round_name, 
                    'is_bye': is_propagated_bye,
                    'parent_match_a': parent_a,
                    'parent_match_b': parent_b
                })
                next_round_participants.append(match_id)
                match_counter += 1
            
            current_round_participants = next_round_participants

        # insert to db
        for match in all_matches:
            cursor.execute("""
                INSERT INTO matches (
                    match_id, match_code, court_id, player_a_id, player_b_id,
                    round, scheduled_time, duration_minutes, status,
                    score_a, score_b, winner_id, is_bye, category,
                    parent_match_a, parent_match_b
                ) VALUES (?, ?, 1, ?, ?, ?, '2099-01-01 00:00:00', 30, 'Unscheduled', 0, 0, NULL, ?, ?, ?, ?)
            """, (
                match['match_id'], match['match_code'], match['player_a_id'], match['player_b_id'],
                match['round'], match['is_bye'], category,
                match['parent_match_a'], match['parent_match_b']
            ))
            
        cursor.execute("UPDATE tournament_stats SET total_matches = total_matches + ?, last_updated = CURRENT_TIMESTAMP WHERE stat_id = 1", (len(all_matches),))
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"Bracket generated for {category}",
            "summary": {"total_matches": len(all_matches)}
        })

    except Exception as e:
        conn.close()
        print(e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/fixtures', methods=['DELETE'])
def delete_all_fixtures():
    """Delete all fixtures and reset tournament"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        fixture_count = cursor.execute("SELECT COUNT(*) as count FROM matches").fetchone()['count']
        
        if fixture_count == 0:
            conn.close()
            return jsonify({
                "success": True,
                "message": "No fixtures to delete"
            })
        
        cursor.execute("DELETE FROM rest_periods")
        cursor.execute("DELETE FROM matches")
        
        cursor.execute("""
            UPDATE tournament_stats 
            SET total_matches = 0,
                matches_upcoming = 0,
                matches_live = 0,
                matches_completed = 0,
                last_updated = CURRENT_TIMESTAMP
            WHERE stat_id = 1
        """)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "All fixtures deleted successfully",
            "deleted": {
                "fixtures_deleted": fixture_count
            }
        })
        
    except Exception as e:
        conn.close()
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500


@app.route('/api/fixtures/<category>', methods=['DELETE'])
def delete_fixtures_by_category(category):
    """Delete all fixtures for a specific category"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        match_ids_to_delete = cursor.execute("""
            SELECT m.match_id
            FROM matches m
            JOIN players p ON m.player_a_id = p.player_id
            WHERE p.category = ?
        """, (category,)).fetchall()
        
        match_ids = [m['match_id'] for m in match_ids_to_delete]
        
        if not match_ids:
            conn.close()
            return jsonify({
                "success": True,
                "message": f"No fixtures found for {category}"
            })
        
        placeholders = ','.join('?' * len(match_ids))
        
        cursor.execute(
            f"DELETE FROM rest_periods WHERE match_before_id IN ({placeholders}) OR match_after_id IN ({placeholders})",
            match_ids + match_ids
        )
        
        cursor.execute(
            f"DELETE FROM matches WHERE match_id IN ({placeholders})",
            match_ids
        )
        
        cursor.execute("""
            UPDATE tournament_stats 
            SET total_matches = total_matches - ?,
                matches_upcoming = matches_upcoming - ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE stat_id = 1
        """, (len(match_ids), len(match_ids)))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"All fixtures for {category} deleted successfully",
            "deleted": {
                "category": category,
                "fixtures_deleted": len(match_ids)
            }
        })
        
    except Exception as e:
        conn.close()
        return jsonify({
            "success": False, 
            "error": str(e)
        }), 500

# smart scheduling api
#=============================================

@app.route('/api/schedule-matches', methods=['POST'])
def schedule_matches():
    """
    full tournament scheduler
    1. group matches by 'depth' (r16, qf, sf, f).
    2. schedule one depth per day (unless forced to spill over).
    3. shuffle matches within the same depth to mix categories.
    """
    data = request.json
    start_time_str = data.get('start_time', '2024-11-21 09:00:00')
    rest_buffer = data.get('rest_buffer', 10)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        matches = cursor.execute("""
            SELECT m.*
            FROM matches m
            WHERE (m.status = 'Unscheduled' OR m.status = 'Upcoming' OR m.scheduled_time = '2099-01-01 00:00:00')
              AND m.is_bye = 0
            ORDER BY m.category, m.match_id
        """).fetchall()
        
        if not matches:
            conn.close()
            return jsonify({"success": False, "error": "No matches found"}), 400

        courts = cursor.execute("SELECT court_id FROM courts WHERE status = 'Active'").fetchall()
        court_ids = [c['court_id'] for c in courts]
        
        # maps round names to a numeric level
        round_hierarchy = {
            'Round of 128': 1, 'Round of 64': 2, 'Round of 32': 3,
            'Round of 16': 4, 'Quarter Finals': 5, 'Semi Finals': 6, 
            'Finals': 7, 'Champion': 8
        }

        # bucket matches by category first
        category_buckets = {}
        for m in matches:
            cat = m['category'] or 'Uncategorized'
            if cat not in category_buckets: category_buckets[cat] = []
            category_buckets[cat].append(dict(m))
            
        # group into "daily groups" based on relative depth
        daily_groups = {} 
        
        for cat, cat_matches in category_buckets.items():
            cat_matches.sort(key=lambda x: round_hierarchy.get(x['round'], 99))
            
            unique_rounds = sorted(list(set(m['round'] for m in cat_matches)), key=lambda x: round_hierarchy.get(x, 99))
            
            for m in cat_matches:
                # the index determines the day
                day_index = unique_rounds.index(m['round'])
                if day_index not in daily_groups:
                    daily_groups[day_index] = []
                daily_groups[day_index].append(m)

        # schedule loop
        base_start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        current_round_start_cursor = base_start_time
        scheduled_count = 0
        
        sorted_day_indices = sorted(daily_groups.keys())
        
        for day_idx in sorted_day_indices:
            day_matches = daily_groups[day_idx]
            
            # shuffle ensures men's and women's matches are interleaved
            random.shuffle(day_matches)
            
            # reset courts to the exact start time for this round
            # each court tracks its own "next available slot"
            court_cursors = {cid: current_round_start_cursor for cid in court_ids}
            
            round_max_end_time = current_round_start_cursor
            
            for match in day_matches:
                # pick the court available earliest
                chosen_court = min(court_cursors, key=court_cursors.get)
                proposed_start = court_cursors[chosen_court]
                duration = match['duration_minutes']
                
                proposed_end = proposed_start + timedelta(minutes=duration)
                
                # operating hours check (6 am - 10 pm)
                # if this match pushes past 10 pm, move this court to 6 am next day
                if proposed_end.hour >= 22:
                    next_morning = proposed_start.replace(hour=6, minute=0, second=0) + timedelta(days=1)
                    proposed_start = next_morning
                    proposed_end = proposed_start + timedelta(minutes=duration)
                elif proposed_start.hour < 6:
                    proposed_start = proposed_start.replace(hour=6, minute=0, second=0)
                    proposed_end = proposed_start + timedelta(minutes=duration)

                cursor.execute("""
                    UPDATE matches 
                    SET court_id = ?, scheduled_time = ?, status = 'Upcoming'
                    WHERE match_id = ?
                """, (chosen_court, proposed_start.strftime('%Y-%m-%d %H:%M:%S'), match['match_id']))
                
                # update court cursor (end + rest buffer)
                court_cursors[chosen_court] = proposed_end + timedelta(minutes=rest_buffer)
                
                if proposed_end > round_max_end_time:
                    round_max_end_time = proposed_end
                
                scheduled_count += 1
            
            # prepare for next round/day
            # start 1 day after the last match of this round finishes
            next_day_obj = round_max_end_time + timedelta(days=1)
            current_round_start_cursor = next_day_obj.replace(
                hour=base_start_time.hour, 
                minute=base_start_time.minute, 
                second=0
            )

        cursor.execute("UPDATE matches SET status = 'Upcoming' WHERE is_bye = 1 AND status = 'Unscheduled'")
        cursor.execute("""
            UPDATE tournament_stats
            SET matches_upcoming = (SELECT COUNT(*) FROM matches WHERE status='Upcoming'),
                last_updated = CURRENT_TIMESTAMP
            WHERE stat_id = 1
        """)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"Scheduled {scheduled_count} matches across {len(sorted_day_indices)} rounds"
        })
        
    except Exception as e:
        conn.close()
        print(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    

# dynamic rescheduling api
#=============================================

@app.route('/api/reschedule-after-match', methods=['POST'])
def reschedule_after_match():
    """
    dynamic rescheduling: adjust all subsequent matches after a match finishes
    maintains rest buffer and player rest requirements
    """
    data = request.json
    completed_match_id = data.get('match_id')
    actual_end_time_str = data.get('actual_end_time')
    rest_buffer_minutes = data.get('rest_buffer', 10)
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        completed_match = cursor.execute("""
            SELECT court_id, scheduled_time, duration_minutes, player_a_id, player_b_id
            FROM matches
            WHERE match_id = ?
        """, (completed_match_id,)).fetchone()
        
        if not completed_match:
            conn.close()
            return jsonify({"success": False, "error": "Match not found"}), 404
        
        match_dict = dict(completed_match)
        court_id = match_dict['court_id']
        actual_end_time = datetime.strptime(actual_end_time_str, "%Y-%m-%d %H:%M:%S")
        
        # calculate time difference from scheduled end
        scheduled_end = datetime.strptime(str(match_dict['scheduled_time']), "%Y-%m-%d %H:%M:%S") + \
                       timedelta(minutes=match_dict['duration_minutes'])
        time_delta = (actual_end_time - scheduled_end).total_seconds() / 60
        
        print(f"match ended {abs(time_delta):.0f} minutes {'late' if time_delta > 0 else 'early'}")
        
        # only reschedule if significant delay/advance
        if abs(time_delta) < 5:
            conn.close()
            return jsonify({
                "success": True,
                "message": "Time difference too small, no rescheduling needed",
                "time_delta_minutes": time_delta
            })
        
        # get all upcoming matches on this court after the completed match
        upcoming_matches = cursor.execute("""
            SELECT match_id, scheduled_time, duration_minutes, player_a_id, player_b_id
            FROM matches
            WHERE court_id = ? 
              AND status = 'Upcoming'
              AND scheduled_time > ?
            ORDER BY scheduled_time
        """, (court_id, actual_end_time)).fetchall()
        
        # rest buffer enforcement: court available after buffer
        next_available_time = actual_end_time + timedelta(minutes=rest_buffer_minutes)
        
        rescheduled_count = 0
        for match in upcoming_matches:
            match_dict = dict(match)
            match_id = match_dict['match_id']
            old_time = datetime.strptime(str(match_dict['scheduled_time']), "%Y-%m-%d %H:%M:%S")
            
            # new time is the later of: next_available_time or existing scheduled time
            new_time = max(next_available_time, old_time)
            
            if new_time != old_time:
                cursor.execute("""
                    UPDATE matches
                    SET scheduled_time = ?
                    WHERE match_id = ?
                """, (new_time, match_id))
                
                match_end = new_time + timedelta(minutes=match_dict['duration_minutes'])
                cursor.execute("""
                    UPDATE rest_periods
                    SET rest_start_time = ?,
                        rest_end_time = ?
                    WHERE match_before_id = ?
                """, (match_end, match_end + timedelta(minutes=rest_buffer_minutes), match_id))
                
                rescheduled_count += 1
            
            # court continuity: next match's end becomes new available time
            next_available_time = new_time + timedelta(minutes=match_dict['duration_minutes']) + \
                                 timedelta(minutes=rest_buffer_minutes)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Rescheduled {rescheduled_count} subsequent matches",
            "time_delta_minutes": time_delta,
            "matches_affected": rescheduled_count
        })
        
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


# match progression api
#=============================================

@app.route('/api/progress-winner', methods=['POST'])
def progress_winner():
    """
    progression: move winner to next round automatically
    creates next round match if both parent matches are complete
    """
    data = request.json
    completed_match_id = data.get('match_id')
    winner_id = data.get('winner_id')
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        match = cursor.execute("""
            SELECT round, match_id
            FROM matches
            WHERE match_id = ? AND status = 'Completed'
        """, (completed_match_id,)).fetchone()
        
        if not match:
            conn.close()
            return jsonify({"success": False, "error": "Match not found or not completed"}), 404
        
        current_round = dict(match)['round']
        
        round_map = {
            'Round of 32': 'Round of 16',
            'Round of 16': 'Quarter Finals',
            'Quarter Finals': 'Semi Finals',
            'Semi Finals': 'Finals',
            'Finals': 'Champion'
        }
        
        next_round = round_map.get(current_round)
        
        if not next_round:
            conn.close()
            return jsonify({
                "success": True,
                "message": "Tournament complete! Winner is champion.",
                "champion": winner_id
            })
        
        if next_round == 'Champion':
            conn.close()
            return jsonify({
                "success": True,
                "message": f"Tournament winner: {winner_id}",
                "champion": winner_id
            })
        
        # check if next round match already exists for this winner
        existing_next_match = cursor.execute("""
            SELECT match_id FROM matches
            WHERE round = ? 
              AND (player_a_id = ? OR player_b_id = ?)
        """, (next_round, winner_id, winner_id)).fetchone()
        
        if existing_next_match:
            conn.close()
            return jsonify({
                "success": True,
                "message": "Winner already progressed to next round"
            })
        
        # find if there's a partner match
        # for knockout: matches are paired - m-001 & m-002 winners play each other
        match_num = int(completed_match_id.split('-')[1])
        partner_num = match_num + 1 if match_num % 2 == 1 else match_num - 1
        partner_match_id = f"M-{partner_num:03d}"
        
        partner_match = cursor.execute("""
            SELECT match_id, winner_id, status
            FROM matches
            WHERE match_id = ?
        """, (partner_match_id,)).fetchone()
        
        if partner_match:
            partner_dict = dict(partner_match)
            
            # both matches complete? create next round match
            if partner_dict['status'] == 'Completed' and partner_dict['winner_id']:
                opponent_id = partner_dict['winner_id']
                
                last_match = cursor.execute(
                    "SELECT match_id FROM matches ORDER BY match_id DESC LIMIT 1"
                ).fetchone()
                last_num = int(dict(last_match)['match_id'].split('-')[1])
                new_match_id = f"M-{last_num + 1:03d}"
                
                cursor.execute("""
                    INSERT INTO matches (
                        match_id, match_code, court_id, player_a_id, player_b_id,
                        round, scheduled_time, duration_minutes, status,
                        score_a, score_b, winner_id, is_bye
                    ) VALUES (?, ?, ?, ?, ?, ?, NULL, 30, 'Upcoming', 0, 0, NULL, 0)
                """, (new_match_id, f'{random.randint(100000, 999999)}', 
                      1, winner_id, opponent_id, next_round))
                
                cursor.execute("""
                    UPDATE tournament_stats
                    SET total_matches = total_matches + 1,
                        matches_upcoming = matches_upcoming + 1,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE stat_id = 1
                """)
                
                conn.commit()
                conn.close()
                
                return jsonify({
                    "success": True,
                    "message": f"Next round match created: {new_match_id}",
                    "next_match": {
                        "match_id": new_match_id,
                        "round": next_round,
                        "player_a": winner_id,
                        "player_b": opponent_id
                    }
                })
            else:
                conn.close()
                return jsonify({
                    "success": True,
                    "message": "Waiting for partner match to complete",
                    "waiting_for": partner_match_id
                })
        else:
            conn.close()
            return jsonify({
                "success": True,
                "message": "No partner match found (possible bye scenario)"
            })
        
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 500


# main
#===========================================

@app.route('/')
def home():
    return render_template('tournament.html') 

if __name__ == '__main__':
    init_db()
    
    print("\n" + "="*50)
    print("Xthlete Tournament System - Backend")
    print("="*50)
    print("\nAPI Endpoints:")
    print("  • GET  /api/health          - Health check")
    print("  • GET  /api/stats           - Tournament stats")
    print("  • GET  /api/players         - Get all players")
    print("  • POST /api/players         - Add new player")
    print("  • GET  /api/fixtures        - Get tournament bracket")
    print("  • GET  /api/schedule        - Get today's schedule")
    print("  • GET  /api/rest-periods    - Get rest periods")
    print("  • POST /api/validate-code   - Validate match code")
    print("  • POST /api/update-score    - Update match score")
    print("  • POST /api/submit-result   - Submit final result")
    print("  • GET  /api/match/<code>    - Get match details")
    print("  • GET  /api/clubs           - Get all clubs")
    print("  • GET  /api/courts          - Get all courts")
    print("\n Server running on: http://127.0.0.1:8080")
    print("="*50 + "\n")
    
    app.run(debug=True, port=8080)