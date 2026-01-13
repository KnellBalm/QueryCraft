from backend.services.database import postgres_connection
from datetime import date

def diag():
    target_date = "2026-01-14"
    print(f"Checking data for {target_date}...")
    
    with postgres_connection() as pg:
        # Check problems
        problems_df = pg.fetch_df("SELECT COUNT(*) as count FROM public.problems WHERE problem_date = %s", [target_date])
        print(f"Problems for {target_date}: {problems_df.iloc[0]['count']}")
        
        # Check problem details
        if problems_df.iloc[0]['count'] > 0:
            details = pg.fetch_df("SELECT title FROM public.problems WHERE problem_date = %s", [target_date])
            print("Problem List:")
            print(details)
            
        # Check dataset_versions
        versions = pg.fetch_df("SELECT * FROM public.dataset_versions ORDER BY created_at DESC LIMIT 3")
        print("\nRecent Dataset Versions:")
        print(versions)
        
        # Check scheduler_status
        status = pg.fetch_df("SELECT * FROM public.scheduler_status")
        print("\nScheduler Status:")
        print(status)
        
        # Check date range of data
        data_range = pg.fetch_df("SELECT MIN(signup_at) as min_signup, MAX(signup_at) as max_signup FROM public.pa_users")
        print("\nData Range (pa_users):")
        print(data_range)

if __name__ == "__main__":
    diag()
