# backend/generator/scenario_generator.py
"""
비즈니스 시나리오 생성기
하루치 Daily Challenge의 비즈니스 배경 및 데이터 구조 생성
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime, date, timedelta
import random
import os
import sys

# backend 디렉토리를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator.product_config import (
    PRODUCT_TYPES,
    PRODUCT_KPI_GUIDE,
    select_product_type
)


@dataclass
class ColumnInfo:
    """컬럼 정보"""
    name: str
    data_type: str  # "INTEGER", "VARCHAR(255)", "TIMESTAMP", etc.
    nullable: bool = True
    description: str = ""


@dataclass
class TableConfig:
    """동적으로 생성되는 테이블 메타데이터"""
    schema_name: str  # "warehouse", "analytics", "raw_data"
    table_name: str  # "bf_events_20261117", "user_segments"
    purpose: str  # "블랙프라이데이 기간 유저 행동 이벤트"
    row_count: int = 10000
    columns: List[ColumnInfo] = field(default_factory=list)
    
    @property
    def full_name(self) -> str:
        return f"{self.schema_name}.{self.table_name}"


@dataclass
class BusinessScenario:
    """하루치 챌린지의 비즈니스 배경"""
    date: str  # YYYY-MM-DD
    company_name: str
    company_description: str
    product_type: str  # commerce, content, saas 등
    
    # 스토리 컨텍스트
    situation: str  # "블랙프라이데이 세일 성과 분석"
    stake: str  # "CEO가 다음 분기 마케팅 예산 결정을 위해 요청"
    data_period: Tuple[str, str]  # 분석 대상 기간 (start_date, end_date)
    
    # 동적 테이블 정보
    table_configs: List[TableConfig] = field(default_factory=list)
    
    # 데이터 생성 스토리 (optional, Gemini로 생성)
    data_story: Optional[str] = None
    
    # KPI 정보 (product_config에서 가져옴)
    north_star: Optional[str] = None
    key_metrics: Optional[List[str]] = None


# 시나리오 템플릿 (Product Type별)
SCENARIO_TEMPLATES = {
    "commerce": [
        {
            "situation": "블랙프라이데이 세일 성과 분석",
            "stake": "CEO가 다음 분기 마케팅 예산을 확정하기 위해 이번 세일의 ROI를 검증 요청",
            "period_days": 30,
            "tables": [
                {
                    "schema": "warehouse",
                    "table_pattern": "bf_events_{date}",
                    "purpose": "블랙프라이데이 기간 사용자 행동 이벤트",
                    "row_count": 50000
                },
                {
                    "schema": "analytics",
                    "table_pattern": "user_segments",
                    "purpose": "사용자 세그먼트 (신규/재방문/VIP)",
                    "row_count": 10000
                }
            ]
        },
        {
            "situation": "신규 상품 카테고리 런칭 후 초기 반응 분석",
            "stake": "CMO가 광고 예산 추가 집행 여부를 결정하기 위해 론칭 2주차 데이터 분석 요청",
            "period_days": 14,
            "tables": [
                {
                    "schema": "raw_data",
                    "table_pattern": "product_events_{date}",
                    "purpose": "신규 카테고리 상품 조회/구매 이벤트",
                    "row_count": 30000
                },
                {
                    "schema": "warehouse",
                    "table_pattern": "dim_products",
                    "purpose": "상품 차원 테이블 (카테고리, 가격, 재고)",
                    "row_count": 5000
                }
            ]
        }
    ],
    "saas": [
        {
            "situation": "프리미엄 기능 출시 후 전환율 분석",
            "stake": "제품팀이 프리미엄 티어 가격 조정을 위해 초기 사용자 반응 데이터 요청",
            "period_days": 21,
            "tables": [
                {
                    "schema": "analytics",
                    "table_pattern": "feature_usage_{date}",
                    "purpose": "프리미엄 기능 사용 로그",
                    "row_count": 25000
                },
                {
                    "schema": "warehouse",
                    "table_pattern": "subscriptions",
                    "purpose": "구독 플랜 및 업그레이드 이력",
                    "row_count": 8000
                }
            ]
        },
        {
            "situation": "고객 이탈 예측 모델 학습 데이터 준비",
            "stake": "데이터 과학팀이 이탈 리스크가 높은 고객 조기 발견을 위한 피처 엔지니어링 요청",
            "period_days": 90,
            "tables": [
                {
                    "schema": "ml_features",
                    "table_pattern": "user_activity_summary",
                    "purpose": "사용자별 활동 지표 (로그인, 기능 사용 빈도)",
                    "row_count": 15000
                },
                {
                    "schema": "warehouse",
                    "table_pattern": "churn_events",
                    "purpose": "해지/다운그레이드 이벤트",
                    "row_count": 2000
                }
            ]
        }
    ],
    "content": [
        {
            "situation": "새로운 콘텐츠 포맷 도입 후 Engagement 분석",
            "stake": "콘텐츠팀이 비디오 포맷 확대 여부를 결정하기 위해 기존 텍스트 대비 성과 비교 요청",
            "period_days": 30,
            "tables": [
                {
                    "schema": "raw_data",
                    "table_pattern": "content_engagement_{date}",
                    "purpose": "콘텐츠 조회, 스크롤, 완독 이벤트",
                    "row_count": 80000
                },
                {
                    "schema": "analytics",
                    "table_pattern": "content_metadata",
                    "purpose": "콘텐츠 메타데이터 (포맷, 카테고리, 작성자)",
                    "row_count": 5000
                }
            ]
        }
    ],
    "fintech": [
        {
            "situation": "신규 간편송금 기능 출시 후 안정성 모니터링",
            "stake": "리스크팀이 사기 거래 탐지 모델 업데이트를 위해 초기 트랜잭션 패턴 분석 요청",
            "period_days": 14,
            "tables": [
                {
                    "schema": "warehouse",
                    "table_pattern": "transactions_{date}",
                    "purpose": "송금 트랜잭션 로그 (금액, 송수신자, 시간)",
                    "row_count": 40000
                },
                {
                    "schema": "analytics",
                    "table_pattern": "fraud_alerts",
                    "purpose": "사기 의심 알림 이력",
                    "row_count": 500
                }
            ]
        }
    ]
}


def generate_table_name(pattern: str, scenario_date: str, product_type: str) -> str:
    """
    테이블명 패턴을 실제 테이블명으로 변환
    
    Args:
        pattern: "bf_events_{date}", "user_segments", etc.
        scenario_date: "2026-11-17"
        product_type: "commerce"
    
    Returns:
        실제 테이블명 (예: "bf_events_20261117")
    """
    date_str = scenario_date.replace("-", "")
    
    if "{date}" in pattern:
        return pattern.format(date=date_str)
    else:
        return pattern


def create_table_configs(
    template_tables: List[dict],
    scenario_date: str,
    product_type: str
) -> List[TableConfig]:
    """템플릿에서 TableConfig 목록 생성"""
    configs = []
    
    for tbl in template_tables:
        table_name = generate_table_name(
            tbl["table_pattern"],
            scenario_date,
            product_type
        )
        
        config = TableConfig(
            schema_name=tbl["schema"],
            table_name=table_name,
            purpose=tbl["purpose"],
            row_count=tbl.get("row_count", 10000),
            columns=[]  # 실제 컬럼은 데이터 생성 시 정의
        )
        configs.append(config)
    
    return configs


def generate_scenario(target_date: Optional[str] = None) -> BusinessScenario:
    """
    특정 날짜의 비즈니스 시나리오 생성
    
    Args:
        target_date: YYYY-MM-DD 형식 (없으면 오늘)
    
    Returns:
        BusinessScenario 객체
    """
    if target_date is None:
        target_date = date.today().isoformat()
    
    # 1. Product Type 선택
    product_type = select_product_type()
    
    # 2. 해당 Product Type의 시나리오 템플릿 중 하나 선택
    templates = SCENARIO_TEMPLATES.get(product_type, SCENARIO_TEMPLATES["commerce"])
    template = random.choice(templates)
    
    # 3. KPI 정보 가져오기
    kpi_guide = PRODUCT_KPI_GUIDE.get(product_type, PRODUCT_KPI_GUIDE["commerce"])
    
    # 4. 분석 기간 계산
    target_dt = datetime.fromisoformat(target_date)
    period_days = template["period_days"]
    start_date = (target_dt - timedelta(days=period_days)).isoformat()[:10]
    end_date = target_date
    
    # 5. 테이블 구성 생성
    table_configs = create_table_configs(
        template["tables"],
        target_date,
        product_type
    )
    
    # 6. BusinessScenario 생성
    scenario = BusinessScenario(
        date=target_date,
        company_name=kpi_guide["company_name"],
        company_description=kpi_guide["company_description"],
        product_type=product_type,
        situation=template["situation"],
        stake=template["stake"],
        data_period=(start_date, end_date),
        table_configs=table_configs,
        north_star=kpi_guide.get("north_star"),
        key_metrics=kpi_guide.get("key_metrics", [])
    )
    
    return scenario




if __name__ == "__main__":
    # 테스트
    scenario = generate_scenario("2026-01-17")
    print(f"=== Business Scenario for {scenario.date} ===")
    print(f"Company: {scenario.company_name}")
    print(f"Product Type: {scenario.product_type}")
    print(f"Situation: {scenario.situation}")
    print(f"Stake: {scenario.stake}")
    print(f"Period: {scenario.data_period[0]} ~ {scenario.data_period[1]}")
    print(f"\nTables:")
    for tbl in scenario.table_configs:
        print(f"  - {tbl.full_name}: {tbl.purpose} ({tbl.row_count:,} rows)")
