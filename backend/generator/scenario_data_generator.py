# backend/generator/scenario_data_generator.py
"""
Scenario 기반 통합 데이터 생성
BusinessScenario를 받아 동적 테이블 생성 및 데이터 인서트
"""
import sys
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple
import random

# Path setup
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator.scenario_generator import BusinessScenario, TableConfig, ColumnInfo
from generator.product_config import get_events_for_type, get_probabilities_for_type
import psycopg2


def create_dynamic_tables(scenario: BusinessScenario, pg_conn) -> None:
    """
    시나리오의 TableConfig에 따라 동적으로 테이블 생성
    
    Args:
        scenario: BusinessScenario 객체
        pg_conn: PostgreSQL 연결
    """
    cur = pg_conn.cursor()
    
    for table_config in scenario.table_configs:
        full_name = table_config.full_name
        
        # 스키마가 존재하는지 확인 및 생성
        schema_name = table_config.schema_name
        cur.execute(f"""
            CREATE SCHEMA IF NOT EXISTS {schema_name};
        """)
        
        # 기존 테이블 삭제 (development용)
        cur.execute(f"DROP TABLE IF EXISTS {full_name} CASCADE;")
        
        # 테이블 생성 - product type에 따라 다른 스키마
        if "events" in table_config.table_name or "clickstream" in table_config.table_name:
            # Event stream 테이블
            create_event_table(cur, full_name, scenario.product_type)
        elif "user" in table_config.table_name or "segment" in table_config.table_name:
            # User dimension 테이블
            create_user_dimension_table(cur, full_name)
        elif "product" in table_config.table_name:
            # Product dimension 테이블 (commerce only)
            create_product_dimension_table(cur, full_name)
        elif "transaction" in table_config.table_name:
            # Transaction 테이블 (fintech)
            create_transaction_table(cur, full_name)
        elif "subscription" in table_config.table_name:
            # Subscription 테이블 (saas)
            create_subscription_table(cur, full_name)
        elif "content" in table_config.table_name:
            # Content metadata 테이블
            create_content_metadata_table(cur, full_name)
        elif "fraud" in table_config.table_name or "alert" in table_config.table_name:
            # Fraud alerts 테이블
            create_fraud_alerts_table(cur, full_name)
        else:
            # Generic fact 테이블
            create_generic_fact_table(cur, full_name, scenario.product_type)
        
        print(f"✓ Created table: {full_name}")
    
    pg_conn.commit()


def create_event_table(cur, full_name: str, product_type: str) -> None:
    """이벤트 로그 테이블 생성 (PA + Stream 공통)"""
    cur.execute(f"""
        CREATE TABLE {full_name} (
            event_id BIGSERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            session_id VARCHAR(36),
            event_type VARCHAR(50) NOT NULL,
            event_at TIMESTAMP NOT NULL,
            
            -- Stream 분석용
            event_date DATE NOT NULL,
            event_hour INTEGER,
            
            -- PA 분석용 차원
            device_type VARCHAR(20),
            platform VARCHAR(20),
            country VARCHAR(10),
            
            -- Product type specific 컬럼
            properties JSONB,
            
            -- 실무 패턴: NULL 가능 컬럼
            referrer VARCHAR(255),
            utm_source VARCHAR(100),
            utm_campaign VARCHAR(100),
            
            -- 인덱스
            CONSTRAINT idx_{full_name.replace('.', '_')}_event_date 
                CHECK (event_date = event_at::date)
        );
        
        CREATE INDEX ON {full_name} (user_id);
        CREATE INDEX ON {full_name} (event_type);
        CREATE INDEX ON {full_name} (event_date);
        CREATE INDEX ON {full_name} (event_at);
    """)


def create_user_dimension_table(cur, full_name: str) -> None:
    """사용자 차원 테이블"""
    cur.execute(f"""
        CREATE TABLE {full_name} (
            user_id INTEGER PRIMARY KEY,
            cohort VARCHAR(20),  -- '2026-01-W01', '2026-01', etc.
            signup_date DATE,
            segment VARCHAR(50),  -- 'new', 'returning', 'vip', etc.
            country VARCHAR(10),
            device_type VARCHAR(20),
            
            -- Nullable 컬럼 (실무 패턴)
            email_verified BOOLEAN,
            phone_verified BOOLEAN,
            total_spent DECIMAL(10,2),
            
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)


def create_product_dimension_table(cur, full_name: str) -> None:
    """상품 차원 테이블 (Commerce)"""
    cur.execute(f"""
        CREATE TABLE {full_name} (
            product_id INTEGER PRIMARY KEY,
            product_name VARCHAR(200),
            category VARCHAR(100),
            subcategory VARCHAR(100),
            price DECIMAL(10,2),
            cost DECIMAL(10,2),  -- Nullable
            stock INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)


def create_transaction_table(cur, full_name: str) -> None:
    """트랜잭션 테이블 (Fintech)"""
    cur.execute(f"""
        CREATE TABLE {full_name} (
            transaction_id BIGSERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            transaction_type VARCHAR(50),  -- 'transfer', 'payment', 'deposit'
            amount DECIMAL(15,2) NOT NULL,
            currency VARCHAR(3) DEFAULT 'KRW',
            status VARCHAR(20),  -- 'success', 'failed', 'pending'
            
            -- Sender/Receiver (NULL 가능)
            from_account VARCHAR(50),
            to_account VARCHAR(50),
            
            transaction_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX ON {full_name} (user_id);
        CREATE INDEX ON {full_name} (transaction_at);
        CREATE INDEX ON {full_name} (status);
    """)


def create_subscription_table(cur, full_name: str) -> None:
    """구독 테이블 (SaaS)"""
    cur.execute(f"""
        CREATE TABLE {full_name} (
            subscription_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            plan_type VARCHAR(50),  -- 'free', 'premium', 'enterprise'
            status VARCHAR(20),  -- 'active', 'cancelled', 'expired'
            started_at DATE NOT NULL,
            ended_at DATE,  -- NULL if active
            mrr DECIMAL(10,2),  -- Monthly Recurring Revenue
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX ON {full_name} (user_id);
        CREATE INDEX ON {full_name} (plan_type);
    """)


def create_content_metadata_table(cur, full_name: str) -> None:
    """콘텐츠 메타데이터 테이블 (Content)"""
    cur.execute(f"""
        CREATE TABLE {full_name} (
            content_id INTEGER PRIMARY KEY,
            title VARCHAR(500),
            author_id INTEGER,
            category VARCHAR(100),
            content_type VARCHAR(20),  -- 'article', 'video', 'podcast'
            word_count INTEGER,
            published_at TIMESTAMP,
            view_count INTEGER DEFAULT 0,
            like_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)


def create_fraud_alerts_table(cur, full_name: str) -> None:
    """사기 알림 테이블 (Fintech)"""
    cur.execute(f"""
        CREATE TABLE {full_name} (
            alert_id SERIAL PRIMARY KEY,
            transaction_id BIGINT,
            user_id INTEGER,
            alert_type VARCHAR(50),  -- 'suspicious_amount', 'unusual_pattern', etc.
            risk_score DECIMAL(5,2),  -- 0.00 ~ 100.00
            is_false_positive BOOLEAN,  -- NULL 가능
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)


def create_generic_fact_table(cur, full_name: str, product_type: str) -> None:
    """범용 Fact 테이블"""
    cur.execute(f"""
        CREATE TABLE {full_name} (
            id BIGSERIAL PRIMARY KEY,
            user_id INTEGER,
            event_date DATE NOT NULL,
            metric_value DECIMAL(15,2),
            dimension1 VARCHAR(100),
            dimension2 VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX ON {full_name} (event_date);
    """)


def generate_scenario_data(scenario: BusinessScenario, pg_conn) -> None:
    """
    시나리오 기반 통합 데이터 생성
    PA와 Stream 분석 모두를 지원하는 데이터 생성
    
    Args:
        scenario: BusinessScenario 객체
        pg_conn: PostgreSQL 연결
    """
    cur = pg_conn.cursor()
    
    # 1. 동적 테이블 생성
    create_dynamic_tables(scenario, pg_conn)
    
    # 2. 각 테이블에 데이터 생성
    for table_config in scenario.table_configs:
        full_name = table_config.full_name
        target_rows = table_config.row_count
        
        print(f"Generating {target_rows:,} rows for {full_name}...")
        
        if "events" in table_config.table_name:
            generate_event_data(cur, full_name, scenario, target_rows)
        elif "user" in table_config.table_name or "segment" in table_config.table_name:
            generate_user_data(cur, full_name, scenario, target_rows)
        elif "transaction" in table_config.table_name:
            generate_transaction_data(cur, full_name, scenario, target_rows)
        elif "fraud" in table_config.table_name or "alert" in table_config.table_name:
            generate_fraud_data(cur, full_name, scenario, target_rows)
        else:
            # Generic data
            generate_generic_data(cur, full_name, scenario, target_rows)
        
        pg_conn.commit()
        print(f"✓ Inserted {target_rows:,} rows into {full_name}")


def generate_event_data(cur, full_name: str, scenario: BusinessScenario, target_rows: int) -> None:
    """이벤트 데이터 생성 (PA + Stream 통합)"""
    start_date, end_date = scenario.data_period
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    
    events = get_events_for_type(scenario.product_type)
    probabilities = get_probabilities_for_type(scenario.product_type)
    
    rows = []
    for i in range(target_rows):
        # Random timestamp within period
        random_seconds = random.randint(0, int((end_dt - start_dt).total_seconds()))
        event_at = start_dt + timedelta(seconds=random_seconds)
        
        user_id = random.randint(1, 10000)
        session_id = f"sess_{random.randint(1000000, 9999999)}"
        event_type = random.choices(events, weights=[probabilities.get(e, 0.1) for e in events])[0]
        
        device_type = random.choice(['mobile', 'desktop', 'tablet'])
        platform = random.choice(['ios', 'android', 'web'])
        country = random.choice(['KR', 'US', 'JP', 'CN'])
        
        # 실무 패턴: 일부 NULL
        referrer = random.choice([None, 'google.com', 'facebook.com', 'direct'])
        utm_source = random.choice([None, 'google', 'facebook', 'email']) if referrer else None
        
        rows.append((
            user_id, session_id, event_type, event_at, event_at.date(), event_at.hour,
            device_type, platform, country, '{}',  # properties (JSONB)
            referrer, utm_source,None  # utm_campaign
        ))
    
    # Bulk insert
    cur.executemany(f"""
        INSERT INTO {full_name} 
        (user_id, session_id, event_type, event_at, event_date, event_hour,
         device_type, platform, country, properties, referrer, utm_source, utm_campaign)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, rows)


def generate_user_data(cur, full_name: str, scenario: BusinessScenario, target_rows: int) -> None:
    """사용자 차원 데이터"""
    rows = []
    for user_id in range(1, target_rows + 1):
        signup_date = date.today() - timedelta(days=random.randint(0, 365))
        cohort = signup_date.strftime('%Y-%m')
        segment = random.choice(['new', 'returning', 'vip', 'dormant'])
        country = random.choice(['KR', 'US', 'JP'])
        device_type = random.choice(['mobile', 'desktop'])
        
        # Nullable
        email_verified = random.choice([True, False, None])
        total_spent = random.uniform(0, 10000) if segment in ['returning', 'vip'] else 0
        
        rows.append((
            user_id, cohort, signup_date, segment, country, device_type,
            email_verified, None, total_spent
        ))
    
    cur.executemany(f"""
        INSERT INTO {full_name}
        (user_id, cohort, signup_date, segment, country, device_type,
         email_verified, phone_verified, total_spent)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, rows)


def generate_transaction_data(cur, full_name: str, scenario: BusinessScenario, target_rows: int) -> None:
    """트랜잭션 데이터 (Fintech)"""
    start_date, end_date = scenario.data_period
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    
    rows = []
    for i in range(target_rows):
        user_id = random.randint(1, 5000)
        transaction_type = random.choice(['transfer', 'payment', 'deposit', 'withdrawal'])
        amount = random.uniform(1000, 1000000)
        status = random.choices(['success', 'failed', 'pending'], weights=[0.85, 0.10, 0.05])[0]
        
        from_account = f"ACC{random.randint(10000, 99999)}" if transaction_type in ['transfer', 'withdrawal'] else None
        to_account = f"ACC{random.randint(10000, 99999)}" if transaction_type in ['transfer', 'deposit'] else None
        
        random_seconds = random.randint(0, int((end_dt - start_dt).total_seconds()))
        transaction_at = start_dt + timedelta(seconds=random_seconds)
        
        rows.append((
            user_id, transaction_type, amount, 'KRW', status,
            from_account, to_account, transaction_at
        ))
    
    cur.executemany(f"""
        INSERT INTO {full_name}
        (user_id, transaction_type, amount, currency, status,
         from_account, to_account, transaction_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, rows)


def generate_fraud_data(cur, full_name: str, scenario: BusinessScenario, target_rows: int) -> None:
    """사기 알림 데이터"""
    rows = []
    for i in range(target_rows):
        transaction_id = random.randint(1, 40000)  # 트랜잭션 테이블 참조
        user_id = random.randint(1, 5000)
        alert_type = random.choice(['suspicious_amount', 'unusual_pattern', 'velocity_check', 'geo_mismatch'])
        risk_score = random.uniform(50, 100)  # 50 이상만 알림
        is_false_positive = random.choice([True, False, None])  # 아직 검증 안 된 경우 NULL
        
        rows.append((
            transaction_id, user_id, alert_type, risk_score, is_false_positive
        ))
    
    cur.executemany(f"""
        INSERT INTO {full_name}
        (transaction_id, user_id, alert_type, risk_score, is_false_positive)
        VALUES (%s, %s, %s, %s, %s)
    """, rows)


def generate_generic_data(cur, full_name: str, scenario: BusinessScenario, target_rows: int) -> None:
    """범용 데이터"""
    start_date, end_date = scenario.data_period
    start_dt = datetime.fromisoformat(start_date).date()
    end_dt = datetime.fromisoformat(end_date).date()
    days = (end_dt - start_dt).days
    
    rows = []
    for i in range(target_rows):
        user_id = random.randint(1, 10000)
        event_date = start_dt + timedelta(days=random.randint(0, days))
        metric_value = random.uniform(0, 1000)
        dimension1 = random.choice(['A', 'B', 'C', 'D'])
        dimension2 = random.choice(['X', 'Y', 'Z'])
        
        rows.append((user_id, event_date, metric_value, dimension1, dimension2))
    
    cur.executemany(f"""
        INSERT INTO {full_name}
        (user_id, event_date, metric_value, dimension1, dimension2)
        VALUES (%s, %s, %s, %s, %s)
    """, rows)


if __name__ == "__main__":
    from generator.scenario_generator import generate_scenario
    from config import settings
    
    # 테스트
    scenario = generate_scenario("2026-01-17")
    
    # PostgreSQL 연결
    conn = psycopg2.connect(settings.POSTGRES_DSN)
    
    try:
        generate_scenario_data(scenario, conn)
        print(f"\n✅ Data generation complete for {scenario.date}!")
        print(f"Generated tables:")
        for tbl in scenario.table_configs:
            print(f"  - {tbl.full_name} ({tbl.row_count:,} rows)")
    finally:
        conn.close()
