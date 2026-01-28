#!/usr/bin/env python3
"""Test script for unified problem generator with AI enrichment"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath('.'))

from backend.generator.scenario_generator import generate_scenario
from backend.generator.unified_problem_generator import generate_daily_problems

def test_problem_generation():
    """Test problem generation with AI enrichment"""
    print("=" * 60)
    print("Testing Unified Problem Generator with AI Enrichment")
    print("=" * 60)

    # Generate scenario
    test_date = "2026-01-28"
    print(f"\n1. Generating scenario for {test_date}...")
    scenario = generate_scenario(test_date)

    print(f"   Company: {scenario.company_name}")
    print(f"   Situation: {scenario.situation}")
    print(f"   Product Type: {scenario.product_type}")
    print(f"   Data Period: {scenario.data_period[0]} ~ {scenario.data_period[1]}")
    print(f"   Tables: {len(scenario.table_configs)}")

    # Generate problems
    print(f"\n2. Generating daily problems...")
    problems = generate_daily_problems(scenario)

    print(f"   Total problems generated: {len(problems)}")

    # Check results
    print(f"\n3. Checking AI enrichment results...")
    with_sql = sum(1 for p in problems if p.get('answer_sql'))
    with_result = sum(1 for p in problems if p.get('expected_result'))

    print(f"   Problems with answer_sql: {with_sql}/{len(problems)}")
    print(f"   Problems with expected_result: {with_result}/{len(problems)}")

    # Show sample
    if problems:
        print(f"\n4. Sample problem (first one):")
        p = problems[0]
        print(f"   ID: {p['problem_id']}")
        print(f"   Type: {p['problem_type']}")
        print(f"   Difficulty: {p['difficulty']}")
        print(f"   Question: {p['question'][:100]}...")
        print(f"   Has answer_sql: {'Yes' if p.get('answer_sql') else 'No'}")
        if p.get('answer_sql'):
            print(f"   SQL preview: {p['answer_sql'][:100]}...")
        print(f"   Has expected_result: {'Yes' if p.get('expected_result') else 'No'}")
        if p.get('expected_result'):
            print(f"   Result rows: {len(p['expected_result'])}")

    print(f"\n{'=' * 60}")
    if with_sql == len(problems):
        print("✅ All problems have answer_sql!")
    else:
        print(f"⚠️  {len(problems) - with_sql} problems missing answer_sql")

    if with_result == len(problems):
        print("✅ All problems have expected_result!")
    else:
        print(f"⚠️  {len(problems) - with_result} problems missing expected_result")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_problem_generation()
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
