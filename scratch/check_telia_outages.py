import sqlite3

conn = sqlite3.connect('telecom_outage.db')
c = conn.cursor()

# Get telia operator id
c.execute("SELECT id FROM operators WHERE name='telia'")
telia_id = c.fetchone()[0]
print('Telia operator id:', telia_id)

# Outages per operator - latest update
c.execute("""
    SELECT o.name, COUNT(*), MIN(out.created_at), MAX(out.created_at),
           MIN(out.updated_at), MAX(out.updated_at)
    FROM outages out
    JOIN operators o ON o.id = out.operator_id
    GROUP BY o.name
""")
print('\n=== outages table per operator ===')
for row in c.fetchall():
    print(f"  {row[0]}: count={row[1]}")
    print(f"    created: {row[2]} -> {row[3]}")
    print(f"    updated: {row[4]} -> {row[5]}")

# Telia outages updated today
c.execute("""
    SELECT incident_id, status, start_time, updated_at, location
    FROM outages
    WHERE operator_id = ?
    ORDER BY updated_at DESC
    LIMIT 10
""", (telia_id,))
print('\n=== Telia 10 most recently updated outages ===')
for row in c.fetchall():
    print(' ', row)

conn.close()