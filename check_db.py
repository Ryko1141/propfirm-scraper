import sqlite3

# Check both databases
for db_path in ['propfirm_scraper.db', 'database/propfirm_scraper.db']:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get firm name
        cursor.execute('SELECT name FROM prop_firm LIMIT 1')
        firm = cursor.fetchone()
        
        # Get rule count
        cursor.execute('SELECT COUNT(*) FROM firm_rule')
        rule_count = cursor.fetchone()[0]
        
        print(f"\n{db_path}:")
        print(f"  Firm: {firm[0] if firm else 'None'}")
        print(f"  Rules: {rule_count}")
        
        conn.close()
    except Exception as e:
        print(f"\n{db_path}: Error - {e}")
