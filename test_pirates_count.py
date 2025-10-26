import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Count pirates
cur.execute('SELECT COUNT(*) FROM expedition_pirates')
count = cur.fetchone()[0]
print(f'Total pirates in expedition_pirates: {count}')

# Show some sample data
cur.execute('SELECT id, pirate_name, expedition_id FROM expedition_pirates LIMIT 5')
rows = cur.fetchall()
print(f'\nSample pirates:')
for row in rows:
    print(f'  ID: {row[0]}, Name: {row[1]}, Expedition: {row[2]}')

conn.close()
