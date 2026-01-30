# backend/generator/unified_problem_generator.py
"""
통합 문제 생성기
하나의 시나리오에서 PA와 Stream 문제를 믹스하여 6문제 생성
"""
import sys
import os
from typing import List, Optional
import random
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generator.scenario_generator import BusinessScenario
from backend.common.logging import get_logger

logger = get_logger(__name__)


# 문제 유형과 난이도 정의
DIFFICULTY_LEVELS = ['easy', 'medium', 'hard']
PROBLEM_TYPES = ['pa', 'stream']


def generate_daily_problems(scenario: BusinessScenario) -> List[dict]:
    """
    하나의 시나리오에서 12문제 생성 (2개 세트 x 6문제)
    - Set 0: 6문제 (PA 3, Stream 3 / Easy 2, Medium 2, Hard 2)
    - Set 1: 6문제 (PA 3, Stream 3 / Easy 2, Medium 2, Hard 2)

    Args:
        scenario: BusinessScenario 객체

    Returns:
        12개의 문제 딕셔너리 리스트
    """
    all_problems = []

    for set_idx in range(2):
        set_problems = []
        failed_enrichments = 0

        # 난이도와 유형 조합 생성
        combinations = [
            ('easy', 'pa'),
            ('easy', 'stream'),
            ('medium', 'pa'),
            ('medium', 'stream'),
            ('hard', 'pa'),
            ('hard', 'stream'),
        ]

        # 순서 섞기
        random.shuffle(combinations)

        for idx_in_set, (difficulty, problem_type) in enumerate(combinations, 1):
            # 전역 고유 ID: {date}-{set}-{idx}
            problem_id = f"{scenario.date}-{set_idx}-{idx_in_set}"

            if problem_type == 'pa':
                problem = generate_pa_problem(
                    scenario=scenario,
                    difficulty=difficulty,
                    problem_id=problem_id,
                    problem_number=idx_in_set
                )
            else:
                problem = generate_stream_problem(
                    scenario=scenario,
                    difficulty=difficulty,
                    problem_id=problem_id,
                    problem_number=idx_in_set
                )

            # AI를 사용해 answer_sql과 expected_result 추가
            problem = enrich_problem_with_ai_solution(problem, scenario)

            # Validation gate: answer_sql이 없으면 문제 스킵
            if not problem.get('answer_sql'):
                logger.error(f"Skipping problem {problem['problem_id']} - AI enrichment failed (no answer_sql)")
                failed_enrichments += 1
                continue

            # 세트 정보 주입
            problem['set_index'] = set_idx
            set_problems.append(problem)

        # 실패한 enrichment 요약 로그
        if failed_enrichments > 0:
            logger.warning(f"Set {set_idx}: {failed_enrichments} problems skipped due to AI enrichment failures")

        all_problems.extend(set_problems)

    return all_problems


def enrich_problem_with_ai_solution(problem: dict, scenario: BusinessScenario) -> dict:
    """
    AI를 사용해 문제에 answer_sql과 expected_result를 추가

    Args:
        problem: 기본 문제 딕셔너리
        scenario: 비즈니스 시나리오 정보

    Returns:
        answer_sql과 expected_result가 추가된 문제 딕셔너리
    """
    try:
        # Gemini 클라이언트 가져오기
        from problems.gemini import _call_gemini_with_retry, GeminiModels

        # 테이블 스키마 정보 생성
        table_schema_info = _build_table_schema_text(scenario)

        # AI 프롬프트 생성
        prompt = _build_sql_generation_prompt(problem, scenario, table_schema_info)

        logger.info(f"Generating answer_sql for problem {problem['problem_id']} using Gemini")

        # Gemini 호출
        response = _call_gemini_with_retry(
            model=GeminiModels.PROBLEM,
            contents=prompt,
            purpose="sql_generation"
        )

        # SQL 추출
        answer_sql = _extract_sql_from_response(response.text)

        if not answer_sql:
            logger.warning(f"Failed to extract SQL for {problem['problem_id']}")
            return problem

        problem['answer_sql'] = answer_sql
        logger.info(f"Successfully generated answer_sql for {problem['problem_id']}")

        # SQL 실행하여 expected_result 생성
        expected_result = _execute_and_get_result(answer_sql, problem['problem_id'])

        if expected_result is not None:
            problem['expected_result'] = expected_result
            problem['expected_row_count'] = len(expected_result)
            logger.info(f"Generated expected_result with {len(expected_result)} rows for {problem['problem_id']}")
        else:
            problem['expected_result'] = []
            problem['expected_row_count'] = 0
            logger.warning(f"Failed to execute answer_sql for {problem['problem_id']}")

        return problem

    except Exception as e:
        logger.warning(f"Failed to enrich problem {problem['problem_id']} with AI solution: {e}")
        # 실패해도 원본 문제 반환 (fallback 채점 방식 사용)
        return problem


def _build_table_schema_text(scenario: BusinessScenario) -> str:
    """시나리오의 테이블 스키마 정보를 텍스트로 변환"""
    schema_lines = ["## 사용 가능한 테이블"]

    for table in scenario.table_configs:
        schema_lines.append(f"\n### {table.full_name}")
        schema_lines.append(f"목적: {table.purpose}")
        schema_lines.append(f"행 수: {table.row_count:,}개")
        schema_lines.append("컬럼:")

        for col in table.columns:
            nullable = "NULL 가능" if col.nullable else "NOT NULL"
            desc = f" - {col.description}" if col.description else ""
            schema_lines.append(f"  - {col.name} ({col.data_type}, {nullable}){desc}")

    return "\n".join(schema_lines)


def _build_sql_generation_prompt(problem: dict, scenario: BusinessScenario, table_schema: str) -> str:
    """SQL 생성을 위한 Gemini 프롬프트 작성"""
    return f"""당신은 PostgreSQL 전문 데이터 분석가입니다.
아래 비즈니스 문제에 대한 SQL 쿼리를 작성해주세요.

## 비즈니스 배경
- 회사: {scenario.company_name}
- 상황: {scenario.situation}
- 분석 기간: {scenario.data_period[0]} ~ {scenario.data_period[1]}
- 산업: {scenario.product_type}

## 문제
**제목**: {problem.get('question', 'N/A')}
**난이도**: {problem.get('difficulty', 'medium')}
**주제**: {problem.get('topic', 'aggregation')}
**요청자**: {problem.get('requester', '데이터팀')}

{problem.get('context', '')}

## 기대하는 결과 컬럼
{', '.join(problem.get('expected_columns', []))}

{table_schema}

## 중요 제약사항
1. PostgreSQL 문법만 사용하세요
2. 위에 명시된 테이블과 컬럼만 사용하세요
3. division by zero 방지: NULLIF 또는 CASE 사용
4. 날짜 조건은 반드시 {scenario.data_period[0]} ~ {scenario.data_period[1]} 범위 내에서 사용
5. 기대하는 결과 컬럼명과 정확히 일치하도록 작성
6. 세미콜론(;)을 끝에 추가하지 마세요
7. 주석(--) 사용 금지

## 출력 형식
SQL 쿼리만 출력하세요. 설명이나 마크다운 코드블록 없이 순수 SQL만 작성하세요.

예시:
SELECT
    column1,
    COUNT(*) as count
FROM table_name
WHERE condition
GROUP BY column1
ORDER BY count DESC"""


def _extract_sql_from_response(response_text: str) -> Optional[str]:
    """Gemini 응답에서 SQL 쿼리 추출"""
    # 1. 코드블록 안의 SQL 추출 시도
    code_block_match = re.search(
        r'```(?:sql)?\s*(.*?)\s*```',
        response_text,
        re.DOTALL | re.IGNORECASE
    )

    if code_block_match:
        sql = code_block_match.group(1).strip()
    else:
        # 2. 코드블록이 없으면 전체 텍스트를 SQL로 간주
        sql = response_text.strip()

    # 3. SQL 정리
    # 주석 제거
    sql = re.sub(r'--[^\n]*', '', sql)  # 단일 라인 주석
    sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)  # 멀티 라인 주석

    # 세미콜론 제거
    sql = sql.rstrip(';').strip()

    # 빈 SQL 체크
    if not sql or len(sql) < 10:
        return None

    return sql


def _execute_and_get_result(answer_sql: str, problem_id: str, limit: int = 1000) -> Optional[List[dict]]:
    """
    정답 SQL을 실행하여 expected_result 생성

    Args:
        answer_sql: 실행할 SQL
        problem_id: 문제 ID (로깅용)
        limit: 최대 행 수

    Returns:
        결과 리스트 (실패 시 None)
    """
    try:
        from backend.engine.postgres_engine import PostgresEngine
        from backend.config.db import PostgresEnv

        pg = PostgresEngine(PostgresEnv().dsn())

        try:
            # LIMIT 추가하여 너무 큰 결과 방지
            limited_sql = f"SELECT * FROM ({answer_sql}) AS _result LIMIT {limit}"
            df = pg.fetch_df(limited_sql)

            # DataFrame을 리스트로 변환
            result = []
            for _, row in df.iterrows():
                record = {}
                for col in df.columns:
                    val = row[col]
                    # JSON 직렬화 가능하도록 변환
                    if hasattr(val, 'isoformat'):  # datetime, date
                        record[col] = val.isoformat()
                    elif hasattr(val, 'item'):  # numpy types
                        record[col] = val.item()
                    else:
                        record[col] = val
                result.append(record)

            return result

        finally:
            pg.close()

    except Exception as e:
        logger.error(f"Failed to execute answer_sql for {problem_id}: {e}")
        logger.error(f"SQL was: {answer_sql[:200]}...")
        return None


def generate_pa_problem(
    scenario: BusinessScenario,
    difficulty: str,
    problem_id: str,
    problem_number: int
) -> dict:
    """
    PA 문제 생성 (집계 분석)
    시나리오 컨텍스트를 반영한 문제 생성
    """
    # 테이블 선택
    table = scenario.table_configs[0] if scenario.table_configs else None
    
    # Difficulty별 문제 템플릿
    templates = PA_PROBLEM_TEMPLATES.get(scenario.product_type, PA_PROBLEM_TEMPLATES['commerce'])
    difficulty_templates = [t for t in templates if t['difficulty'] == difficulty]
    
    if not difficulty_templates:
        # Fallback
        template = {
            'difficulty': difficulty,
            'topic': 'aggregation',
            'question_template': f'{scenario.situation}과 관련하여 기본 집계를 수행하세요.'
        }
    else:
        template = random.choice(difficulty_templates)
    
    # 템플릿에 시나리오 정보 주입
    question = template['question_template'].format(
        company=scenario.company_name,
        situation=scenario.situation,
        table=table.full_name if table else 'events',
        period_start=scenario.data_period[0],
        period_end=scenario.data_period[1]
    )
    
    problem = {
        'problem_id': problem_id,
        'problem_type': 'pa',
        'difficulty': difficulty,
        'topic': template.get('topic', 'aggregation'),
        'requester': get_requester_for_scenario(scenario),
        'question': question,
        'context': f"분석 기간: {scenario.data_period[0]} ~ {scenario.data_period[1]}",
        'expected_columns': template.get('expected_columns', ['result']),
        'hint': template.get('hint'),
        'table_names': [tbl.full_name for tbl in scenario.table_configs],
        'scenario_id': scenario.date,
    }
    
    return problem


def generate_stream_problem(
    scenario: BusinessScenario,
    difficulty: str,
    problem_id: str,
    problem_number: int
) -> dict:
    """
    Stream 문제 생성 (시계열 분석)
    시나리오 컨텍스트를 반영한 문제 생성
    """
    table = scenario.table_configs[0] if scenario.table_configs else None
    
    templates = STREAM_PROBLEM_TEMPLATES.get(scenario.product_type, STREAM_PROBLEM_TEMPLATES['commerce'])
    difficulty_templates = [t for t in templates if t['difficulty'] == difficulty]
    
    if not difficulty_templates:
        template = {
            'difficulty': difficulty,
            'topic': 'time_series',
            'question_template': f'{scenario.situation}의 시간대별 트렌드를 분석하세요.'
        }
    else:
        template = random.choice(difficulty_templates)
    
    question = template['question_template'].format(
        company=scenario.company_name,
        situation=scenario.situation,
        table=table.full_name if table else 'events',
        period_start=scenario.data_period[0],
        period_end=scenario.data_period[1]
    )
    
    problem = {
        'problem_id': problem_id,
        'problem_type': 'stream',
        'difficulty': difficulty,
        'topic': template.get('topic', 'time_series'),
        'requester': get_requester_for_scenario(scenario),
        'question': question,
        'context': f"분석 기간: {scenario.data_period[0]} ~ {scenario.data_period[1]}",
        'expected_columns': template.get('expected_columns', ['date', 'value']),
        'hint': template.get('hint'),
        'table_names': [tbl.full_name for tbl in scenario.table_configs],
        'scenario_id': scenario.date,
    }
    
    return problem


def get_requester_for_scenario(scenario: BusinessScenario) -> str:
    """시나리오에 맞는 요청자 선택"""
    requesters = {
        'commerce': ['CMO (마케팅 총괄)', 'CEO', '데이터 분석팀장', '성장팀 리드'],
        'saas': ['제품 매니저', 'VP of Product', '데이터 과학팀', 'Customer Success 팀장'],
        'fintech': ['리스크 매니저', 'CFO', '컴플라이언스 팀', '사기탐지팀 리드'],
        'content': ['콘텐츠 디렉터', '편집장', '성장팀', '알고리즘 팀'],
        'community': ['커뮤니티 매니저', '제품 팀장', 'Trust & Safety 팀', 'Growth팀'],
    }
    
    return random.choice(requesters.get(scenario.product_type, requesters['commerce']))


# ============================================================
# 문제 템플릿 (Product Type별, Difficulty별)
# ============================================================

PA_PROBLEM_TEMPLATES = {
    'commerce': [
        {
            'difficulty': 'easy',
            'topic': 'basic_aggregation',
            'question_template': '{company}의 {situation} 기간({period_start} ~ {period_end}) 동안 총 구매 금액을 계산하세요. 테이블: `{table}`',
            'expected_columns': ['total_amount'],
            'hint': 'SUM 함수를 사용하세요.'
        },
        {
            'difficulty': 'medium',
            'topic': 'conversion_analysis',
            'question_template': '{company}의 {situation} 기간 동안 장바구니 추가(`add_to_cart`) 대비 구매(`purchase`) 전환율을 계산하세요.',
            'expected_columns': ['conversion_rate'],
            'hint': '각 이벤트 수를 카운트하고 나눗셈하세요.'
        },
        {
            'difficulty': 'hard',
            'topic': 'cohort_analysis',
            'question_template': '{company}의 {situation} 관련 데이터에서 가입 월(cohort)별 평균 구매 금액과 구매 고객 수를 구하세요.',
            'expected_columns': ['cohort', 'avg_purchase_amount', 'customer_count'],
            'hint': 'user 테이블과 조인하여 cohort 정보를 가져오세요.'
        },
    ],
    'fintech': [
        {
            'difficulty': 'easy',
            'topic': 'transaction_sum',
            'question_template': '{company}의 {situation} 기간 동안 성공(success) 상태인 송금 건수를 세어보세요. 테이블: `{table}`',
            'expected_columns': ['success_count'],
        },
        {
            'difficulty': 'medium',
            'topic': 'fraud_rate',
            'question_template': '{situation} 기간 동안 전체 트랜잭션 대비 사기 알림(fraud_alerts)이 발생한 비율을 구하세요.',
            'expected_columns': ['fraud_rate'],
            'hint': '두 테이블을 조인하거나 서브쿼리를 사용하세요.'
        },
        {
            'difficulty': 'hard',
            'topic': 'risk_segmentation',
            'question_template': '{situation} 관련 데이터에서 risk_score 구간별(0-50, 50-75, 75-100)로 알림 건수와 false positive 비율을 구하세요.',
            'expected_columns': ['risk_segment', 'alert_count', 'false_positive_rate'],
        },
    ],
    'saas': [
        {
            'difficulty': 'easy',
            'topic': 'active_users',
            'question_template': '{company}의 {situation} 기간 동안 feature_use 이벤트를 발생시킨 순 사용자 수(DAU)를 구하세요.',
            'expected_columns': ['dau'],
        },
        {
            'difficulty': 'medium',
            'topic': 'plan_distribution',
            'question_template': '{situation} 관련 구독 데이터에서 플랜별(plan_type) 활성 구독 수와 총 MRR을 계산하세요.',
            'expected_columns': ['plan_type', 'active_count', 'total_mrr'],
        },
        {
            'difficulty': 'hard',
            'topic': 'activation_funnel',
            'question_template': '{situation} 기간의 신규 가입자 중 온보딩 완료 → feature_use 3회 이상 달성 비율을 구하세요.',
            'expected_columns': ['activation_rate'],
            'hint': 'Window function이나 서브쿼리를 활용해 조건별 필터링을 수행하세요.'
        },
    ],
}

STREAM_PROBLEM_TEMPLATES = {
    'commerce': [
        {
            'difficulty': 'easy',
            'topic': 'daily_trend',
            'question_template': '{company}의 {situation} 기간 동안 일별 총 이벤트 수를 구하세요. 테이블: `{table}`',
            'expected_columns': ['event_date', 'event_count'],
        },
        {
            'difficulty': 'medium',
            'topic': 'hourly_pattern',
            'question_template': '{situation} 기간의 시간대별(event_hour) 평균 페이지뷰 수를 구하고, 피크 시간대를 파악하세요.',
            'expected_columns': ['event_hour', 'avg_pageviews'],
            'hint': 'GROUP BY event_hour, ORDER BY로 정렬하세요.'
        },
        {
            'difficulty': 'hard',
            'topic': 'funnel_dropout',
            'question_template': '{situation} 기간 동안 page_view → add_to_cart → purchase 퍼널에서 각 단계별 이탈률을 시간 순서대로 분석하세요.',
            'expected_columns': ['step', 'user_count', 'dropout_rate'],
        },
    ],
    'fintech': [
        {
            'difficulty': 'easy',
            'topic': 'daily_volume',
            'question_template': '{company}의 {situation} 기간 동안 일별 총 거래 금액을 구하세요.',
            'expected_columns': ['transaction_date', 'total_volume'],
        },
        {
            'difficulty': 'medium',
            'topic': 'failure_trend',
            'question_template': '{situation} 기간의 일별 트랜잭션 실패율(failed/total)을 계산하세요.',
            'expected_columns': ['transaction_date', 'failure_rate'],
        },
        {
            'difficulty': 'hard',
            'topic': 'anomaly_detection',
            'question_template': '{situation} 기간 동안 시간대별 평균 거래 금액과 표준편차를 구하고, 이상 거래(3σ 초과)를 탐지하세요.',
            'expected_columns': ['transaction_hour', 'avg_amount', 'stddev', 'anomaly_count'],
        },
    ],
    'saas': [
        {
            'difficulty': 'easy',
            'topic': 'dau_trend',
            'question_template': '{company}의 {situation} 기간 동안 일별 활성 사용자 수(DAU)를 계산하세요.',
            'expected_columns': ['event_date', 'dau'],
        },
        {
            'difficulty': 'medium',
            'topic': 'retention_curve',
            'question_template': '{situation} 기간 첫 주 가입자의 주차별 리텐션률을 계산하세요.',
            'expected_columns': ['week_number', 'retention_rate'],
            'hint': '가입일 기준으로 코호트를 만들고, 각 주차별 복귀율을 계산하세요.'
        },
        {
            'difficulty': 'hard',
            'topic': 'feature_adoption',
            'question_template': '{situation} 관련 신규 기능의 일별 누적 사용자 수 증가 추이(S-curve)를 분석하세요.',
            'expected_columns': ['event_date', 'cumulative_users', 'new_users'],
        },
    ],
}


if __name__ == "__main__":
    from generator.scenario_generator import generate_scenario
    
    # 테스트
    scenario = generate_scenario("2026-01-17")
    problems = generate_daily_problems(scenario)
    
    print(f"\n=== Daily Challenge for {scenario.date} ===")
    print(f"Company: {scenario.company_name}")
    print(f"Situation: {scenario.situation}\n")
    
    pa_count = sum(1 for p in problems if p['problem_type'] == 'pa')
    stream_count = sum(1 for p in problems if p['problem_type'] == 'stream')
    
    print(f"Generated {len(problems)} problems (PA: {pa_count}, Stream: {stream_count})\n")
    
    for i, problem in enumerate(problems, 1):
        print(f"{i}. [{problem['problem_type'].upper()}] {problem['difficulty'].capitalize()}")
        print(f"   Topic: {problem['topic']}")
        print(f"   Requester: {problem['requester']}")
        print(f"   Question: {problem['question'][:100]}...")
        print()
    
    print("✅ Unified Problem Generator works!")
