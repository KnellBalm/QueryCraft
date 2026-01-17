#!/usr/bin/env python3
"""
scenario_generator 테스트 스크립트
"""
import sys
import os

# backend 디렉토리를 path에 추가
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# scenario_generator 직접 import
import importlib.util
spec = importlib.util.spec_from_file_location(
    "scenario_generator",
    os.path.join(backend_dir, "generator", "scenario_generator.py")
)
sg = importlib.util.module_from_spec(spec)

# product_config도 먼저 로드
spec2 = importlib.util.spec_from_file_location(
    "generator.product_config",
    os.path.join(backend_dir, "generator", "product_config.py")
)
pc = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(pc)
sys.modules['generator.product_config'] = pc

# scenario_generator 실행
spec.loader.exec_module(sg)

# 테스트 실행
if __name__ == "__main__":
    scenario = sg.generate_scenario("2026-01-17")
    print(f"\\n=== Business Scenario for {scenario.date} ===")
    print(f"Company: {scenario.company_name}")
    print(f"Product Type: {scenario.product_type}")
    print(f"Situation: {scenario.situation}")
    print(f"Stake: {scenario.stake}")
    print(f"Period: {scenario.data_period[0]} ~ {scenario.data_period[1]}")
    print(f"\\nTables:")
    for tbl in scenario.table_configs:
        print(f"  - {tbl.full_name}: {tbl.purpose} ({tbl.row_count:,} rows)")
    print(f"\\n✅ Scenario Generator works!")
