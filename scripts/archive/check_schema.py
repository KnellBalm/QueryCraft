from backend.services.database import postgres_connection

def check_schema():
    with postgres_connection() as pg:
        print("Listing all tables in 'public' schema:")
        df = pg.fetch_df("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        print(df)
        
        if 'scheduler_status' in df['table_name'].values:
            print("\nColumns in 'scheduler_status':")
            cols = pg.fetch_df("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'scheduler_status'
            """)
            print(cols)
        else:
            print("\n'scheduler_status' table NOT FOUND!")

if __name__ == "__main__":
    check_schema()
