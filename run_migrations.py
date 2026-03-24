"""One-time migration runner for CleanClaw on Railway.
Run via: railway run -- python3 run_migrations.py
Or deploy and hit: GET /admin/run-migrations?key=<SECRET_KEY>
"""
import os
import sys
import glob
import psycopg2

def run():
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        return False

    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()

    # Check existing tables
    cur.execute("SELECT tablename FROM pg_tables WHERE tablename LIKE 'cleaning_%' ORDER BY 1")
    existing = [r[0] for r in cur.fetchall()]
    print(f"Existing cleaning tables: {len(existing)}")

    # Run migrations in order
    migration_dir = os.path.join(os.path.dirname(__file__), 'database', 'migrations')
    files = sorted(glob.glob(os.path.join(migration_dir, '01[129]*.sql')))
    
    for mig_file in files:
        name = os.path.basename(mig_file)
        print(f"\n--- {name} ---")
        try:
            with open(mig_file, 'r') as f:
                sql = f.read()
            cur.execute(sql)
            print(f"  OK")
        except Exception as e:
            err = str(e).split('\n')[0]
            print(f"  WARN: {err}")
            conn.rollback()
            conn.autocommit = True

    # Verify
    cur.execute("SELECT tablename FROM pg_tables WHERE tablename LIKE 'cleaning_%' ORDER BY 1")
    final = [r[0] for r in cur.fetchall()]
    print(f"\nFinal: {len(final)} cleaning tables")
    for t in final:
        print(f"  ✓ {t}")

    conn.close()
    return True

if __name__ == '__main__':
    run()
