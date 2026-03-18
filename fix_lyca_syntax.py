import sqlite3

def fix_lyca_syntax():
    conn = sqlite3.connect('telecom_outage.db')
    cur = conn.cursor()
    
    cur.execute("""
        SELECT o.id, o.location 
        FROM outages o
        JOIN operators op ON o.operator_id = op.id
        WHERE op.name = 'lycamobile'
    """)
    
    rows = cur.fetchall()
    fixed = 0
    
    for oid, loc in rows:
        if not loc: continue
        original = loc
        
        # E.g. "Stockholms län (Stockholm County)" -> "Stockholms län"
        if '(' in loc and 'County' in loc:
            loc = loc.split('(')[0].strip()
            
        # E.g. "Stockholms County" -> "Stockholms län"
        elif 'County' in loc:
            loc = loc.replace('County', 'län')
            
        if loc != original:
            cur.execute("UPDATE outages SET location = ? WHERE id = ?", (loc, oid))
            fixed += 1
            
    conn.commit()
    conn.close()
    print(f"Fixed formatting for {fixed} Lycamobile locations.")

if __name__ == '__main__':
    fix_lyca_syntax()
