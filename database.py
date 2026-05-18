import sqlite3

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    # Table for Client Servers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            guild_id TEXT PRIMARY KEY,
            server_name TEXT,
            custom_onboarding_msg TEXT,
            admin_role_id TEXT
        )
    ''')
    # Table for User States
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            discord_id TEXT PRIMARY KEY,
            guild_id TEXT,
            status TEXT DEFAULT 'active'
        )
    ''')
    # Table for Chat History
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

def register_server(guild_id, name):
    cursor.execute('INSERT OR IGNORE INTO servers (guild_id, server_name) VALUES (?, ?)', (guild_id, name))
    conn.commit()

def save_message(discord_id, role, content):
    cursor.execute('INSERT INTO chat_history (discord_id, role, content) VALUES (?, ?, ?)', (discord_id, role, content))
    conn.commit()

def get_chat_history(discord_id, limit=10):
    cursor.execute('SELECT role, content FROM chat_history WHERE discord_id = ? ORDER BY id DESC LIMIT ?', (discord_id, limit))
    return [{"role": row[0], "content": row[1]} for row in cursor.fetchall()[::-1]]

def update_user_status(discord_id, status):
    cursor.execute('UPDATE users SET status = ? WHERE discord_id = ?', (status, discord_id))
    conn.commit()

def get_user_status(discord_id):
    cursor.execute('SELECT status FROM users WHERE discord_id = ?', (discord_id,))
    res = cursor.fetchone()
    return res[0] if res else "active"

init_db()