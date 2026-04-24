import psycopg2
conn = psycopg2.connect('postgresql://postgres.zidhrjftuoyrvoxfnyev:pex9IeFcBAeSSmcx@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres?sslmode=require')
cur = conn.cursor()
cur.execute("SELECT count(*), application_name, client_addr FROM pg_stat_activity WHERE usename='postgres' GROUP BY application_name, client_addr;")
for row in cur.fetchall(): print(row)
