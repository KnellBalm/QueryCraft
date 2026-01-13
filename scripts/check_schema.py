from backend.services.database import postgres_connection

def check_schema():
    with postgres_connection() as pg:
        for table in ['pa_users', 'pa_sessions', 'pa_events', 'pa_orders', 'stream_events']:
            print(f"\n--- {table} ---")
            df = pg.fetch_df(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'")
            print(df)

if __name__ == "__main__":
    check_schema()
