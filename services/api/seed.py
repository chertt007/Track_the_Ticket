"""
Seed script — inserts 3 mock subscriptions into the production database.

Usage:
  cd services/api
  python seed.py

Requirements:
  - DB must be reachable (RDS public access is on for dev)
  - Set env vars or create .env file with DB credentials:
      DB_HOST=tracktheticket-prod.c0v4a4c2krqg.us-east-1.rds.amazonaws.com
      DB_PORT=5432
      DB_NAME=tracktheticket
      DB_USERNAME=tracktheticket_admin
      DB_PASSWORD=your_password

  The script will:
  1. Connect to the database
  2. Find the first existing user (created automatically on first login)
  3. Insert 3 mock subscriptions for that user
  4. Skip if subscriptions already exist
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv(".env")

# ── DB connection ─────────────────────────────────────────────────────────────

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "tracktheticket")
DB_USER = os.getenv("DB_USERNAME", "postgres")
DB_PASS = os.getenv("DB_PASSWORD", "")

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        connect_timeout=10,
    )
    print(f"✅ Connected to {DB_HOST}/{DB_NAME}")
except Exception as e:
    print(f"❌ Cannot connect to database: {e}")
    sys.exit(1)

cur = conn.cursor()

# ── Find user ─────────────────────────────────────────────────────────────────

cur.execute("SELECT id, email FROM users LIMIT 1;")
user = cur.fetchone()

if not user:
    print("❌ No users found in database.")
    print("   Please log in to the frontend first — this creates your user record.")
    print("   Then run this script again.")
    conn.close()
    sys.exit(1)

user_id, user_email = user
print(f"👤 Found user: {user_email} (id={user_id})")

# ── Mock subscriptions ────────────────────────────────────────────────────────

mock_subscriptions = [
    {
        "source_url":       "https://www.aviasales.ru/search/SVO1505DXB1",
        "flight_number":    "SU 1234",
        "airline":          "Aeroflot",
        "origin_iata":      "SVO",
        "destination_iata": "DXB",
        "departure_date":   "2026-05-15",
        "departure_time":   "08:30:00",
        "baggage_info":     "1 × 23 kg",
        "status":           "active",
        "is_active":        True,
        "check_frequency":  3,
    },
    {
        "source_url":       "https://www.aviasales.ru/search/LED0204IST1",
        "flight_number":    "TK 789",
        "airline":          "Turkish Airlines",
        "origin_iata":      "LED",
        "destination_iata": "IST",
        "departure_date":   "2026-06-02",
        "departure_time":   "14:15:00",
        "baggage_info":     "1 × 20 kg",
        "status":           "active",
        "is_active":        True,
        "check_frequency":  3,
    },
    {
        "source_url":       "https://www.aviasales.ru/search/SVO1005BCN1",
        "flight_number":    "VY 456",
        "airline":          "Vueling",
        "origin_iata":      "SVO",
        "destination_iata": "BCN",
        "departure_date":   "2026-05-10",
        "departure_time":   "11:45:00",
        "baggage_info":     "Hand luggage only",
        "status":           "active",
        "is_active":        True,
        "check_frequency":  6,
    },
]

# ── Insert ────────────────────────────────────────────────────────────────────

inserted = 0
skipped = 0

for sub in mock_subscriptions:
    # Skip if subscription with same source_url already exists for this user
    cur.execute(
        "SELECT id FROM subscriptions WHERE user_id = %s AND source_url = %s",
        (user_id, sub["source_url"]),
    )
    if cur.fetchone():
        print(f"⏭️  Skipping {sub['flight_number']} — already exists")
        skipped += 1
        continue

    cur.execute(
        """
        INSERT INTO subscriptions (
            user_id, source_url, flight_number, airline,
            origin_iata, destination_iata, departure_date, departure_time,
            baggage_info, status, is_active, check_frequency
        ) VALUES (
            %(user_id)s, %(source_url)s, %(flight_number)s, %(airline)s,
            %(origin_iata)s, %(destination_iata)s, %(departure_date)s, %(departure_time)s,
            %(baggage_info)s, %(status)s, %(is_active)s, %(check_frequency)s
        )
        """,
        {**sub, "user_id": user_id},
    )
    print(f"✅ Inserted: {sub['flight_number']} ({sub['origin_iata']} → {sub['destination_iata']})")
    inserted += 1

conn.commit()
conn.close()

print(f"\n🎉 Done: {inserted} inserted, {skipped} skipped.")
