# problems/stream_summary.py
from __future__ import annotations
from backend.engine.postgres_engine import PostgresEngine

def build_stream_summary(pg: PostgresEngine) -> str:
    """
    Gemini에게 전달할 '오늘의 로그 요약 텍스트' 생성
    """
    q = {}

    q["total_events"] = pg.fetchone(
        "SELECT COUNT(*) AS c FROM stream_events"
    )["c"]

    q["active_users_30d"] = pg.fetchone("""
        SELECT COUNT(DISTINCT user_id) AS c
        FROM stream_events
        WHERE event_time >= current_date - interval '30 days'
    """)["c"]

    q["purchase_rate"] = pg.fetchone("""
        SELECT
          COUNT(DISTINCT CASE WHEN event_name='purchase' THEN user_id END)::float
          / COUNT(DISTINCT user_id)
          AS rate
        FROM stream_events
    """)["rate"]

    q["top_channels"] = pg.fetchall("""
        SELECT channel, COUNT(*) AS c
        FROM stream_events
        GROUP BY channel
        ORDER BY c DESC
        LIMIT 3
    """)

    summary = f"""
[Stream Log Summary]
- Total events: {q['total_events']}
- Active users (30d): {q['active_users_30d']}
- Purchase user ratio: {q['purchase_rate']:.2%}

Top channels:
""" + "\n".join(
        [f"- {r['channel']}: {r['c']}" for r in q["top_channels"]]
    )

    return summary.strip()
