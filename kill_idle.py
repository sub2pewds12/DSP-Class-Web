import psycopg2
conn = psycopg2.connect('postgresql://postgres.zidhrjftuoyrvoxfnyev:pex9IeFcBAeSSmcx@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?sslmode=require')
conn.autocommit = True
cur = conn.cursor()
cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename='postgres' AND application_name='Supavisor' AND state='idle';")
print(f"Terminated {cur.rowcount} idle Supavisor connections.")
