import sqlite3
from pathlib import Path
from backend.core.config import settings

def get_db_connection() -> sqlite3.Connection:
    """
    Creates and returns a connection to the local SQLite database.
    Row factory is configured to return dict-like sqlite3.Row objects.
    """
    db_path = Path(settings.DATABASE_URL.replace("sqlite:///", ""))
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Initializes required database tables if they do not already exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Route search history table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS route_queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origin_name TEXT NOT NULL,
        destination_name TEXT NOT NULL,
        vehicle_type TEXT NOT NULL,
        recommended_route_id TEXT,
        eco_saving_percent REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Cached route emissions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS route_emissions_cache (
        route_hash TEXT PRIMARY KEY,
        distance_km REAL NOT NULL,
        duration_min REAL NOT NULL,
        vehicle_type TEXT NOT NULL,
        co2_grams REAL NOT NULL,
        model_version TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
