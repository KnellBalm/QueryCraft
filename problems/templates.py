# problems/templates.py

def build_expected_sql(problem: dict) -> str:
    topic = problem["topic"]

    if topic == "retention":
        return """
        WITH cohort AS (
            SELECT
                user_id,
                date_trunc('day', signup_at) AS cohort_date
            FROM pa_users
        ),
        activity AS (
            SELECT
                c.cohort_date,
                date_part('day', e.event_time - c.cohort_date) AS day_n,
                COUNT(DISTINCT e.user_id)::float
                / COUNT(DISTINCT c.user_id) AS retention_rate
            FROM cohort c
            JOIN pa_events e USING (user_id)
            GROUP BY 1,2
        )
        SELECT cohort_date, day_n, retention_rate
        FROM activity
        WHERE day_n BETWEEN 0 AND 7
        ORDER BY cohort_date, day_n
        """

    if topic == "funnel":
        return """
        WITH v AS (
            SELECT DISTINCT user_id FROM pa_events WHERE event_name = 'view'
        ),
        c AS (
            SELECT DISTINCT user_id FROM pa_events WHERE event_name = 'add_to_cart'
        ),
        p AS (
            SELECT DISTINCT user_id FROM pa_events WHERE event_name = 'purchase'
        )
        SELECT
            COUNT(v.user_id) AS view_users,
            COUNT(c.user_id) AS cart_users,
            COUNT(p.user_id) AS purchase_users
        FROM v
        LEFT JOIN c USING (user_id)
        LEFT JOIN p USING (user_id)
        """

    if topic == "revenue":
        return """
        SELECT
            date_trunc('day', order_time) AS order_date,
            SUM(amount) AS revenue
        FROM pa_orders
        GROUP BY 1
        ORDER BY 1
        """

    raise ValueError(f"Unknown topic: {topic}")
