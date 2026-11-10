import sqlite3

DB_NAME = "hushhush.db"

def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            profile_url TEXT,
            followers INTEGER,
            public_repos INTEGER,
            total_stars INTEGER,
            total_forks INTEGER,
            commit_count INTEGER,
            top_language TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
    """)
    
    cursor.execute("""      
        CREATE TABLE IF NOT EXISTS scores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            github_score REAL,
            is_selected INTEGER,
            scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(candidate_id) REFERENCES candidates(id)
                ON DELETE CASCADE
            
            )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidate_queries(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            query TEXT NOT NULL,
            found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
            UNIQUE(candidate_id, role)
            )
    """)
    
    conn.commit()
    conn.close()

def save_candidate(candidate):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO candidates(username, profile_url, followers, public_repos,
        total_stars, total_forks, commit_count, top_language)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET
        public_repos = excluded.public_repos,
        followers = excluded.followers,
        total_stars = excluded.total_stars,
        total_forks = excluded.total_forks,
        commit_count = excluded.commit_count,
        top_language = excluded.top_language
    """, (
        candidate.username,
        candidate.profile_url,
        candidate.followers,
        candidate.public_repos,
        candidate.total_stars,
        candidate.total_forks,
        candidate.commit_count,
        candidate.top_language
    ))

    conn.commit()
    conn.close()
    
def get_candidate_id(username):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM candidates WHERE username = ?", (username,))

    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def save_score(candidate_id, github_score, is_selected):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO scores(candidate_id, github_score, is_selected)
        VALUES(?, ?, ?)
    """, (
        candidate_id,
        github_score,
        is_selected
    ))

    conn.commit()
    conn.close()

def save_candidate_query(candidate_id, role, query):
    if candidate_id is None:
        return
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT or IGNORE INTO candidate_queries(candidate_id, role, query)
        VALUES(?, ?, ?)
    """, (
        candidate_id,
        role,
        query
    ))
    conn.commit()
    conn.close()

def candidate_by_role(role):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT c.username, c.followers, c.commit_count, c.public_repos, c.total_stars, c.total_forks, c.top_language, s.github_score, s.is_selected
        FROM candidates c
        JOIN candidate_queries cq ON c.id = cq.candidate_id
        WHERE cq.role = ?
        AND s.id IN (SELECT MAX(id) FROM scores GROUP BY candidate_id)
        ORDER BY c.commit_count DESC
""", (role,))

    rows = cursor.fetchall()
    conn.close()
    return rows
