#!/usr/bin/env python3
"""
daily_challenge_writer 테스트 스크립트
"""
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# 모듈 로드
import importlib.util

# product_config
spec_pc = importlib.util.spec_from_file_location(
    "generator.product_config",
    os.path.join(backend_dir, "generator", "product_config.py")
)
pc = importlib.util.module_from_spec(spec_pc)
spec_pc.loader.exec_module(pc)
sys.modules['generator.product_config'] = pc

# scenario_generator
spec_sg = importlib.util.spec_from_file_location(
    "generator.scenario_generator",
    os.path.join(backend_dir, "generator", "scenario_generator.py")
)
sg = importlib.util.module_from_spec(spec_sg)
spec_sg.loader.exec_module(sg)
sys.modules['generator.scenario_generator'] = sg

# unified_problem_generator
spec_upg = importlib.util.spec_from_file_location(
    "generator.unified_problem_generator",
    os.path.join(backend_dir, "generator", "unified_problem_generator.py")
)
upg = importlib.util.module_from_spec(spec_upg)
spec_upg.loader.exec_module(upg)
sys.modules['generator.unified_problem_generator'] = upg

# daily_challenge_writer
spec_dcw = importlib.util.spec_from_file_location(
    "generator.daily_challenge_writer",
    os.path.join(backend_dir, "generator", "daily_challenge_writer.py")
)
dcw = importlib.util.module_from_spec(spec_dcw)
spec_dcw.loader.exec_module(dcw)

if __name__ == "__main__":
    # 테스트 날짜
    test_date = "2026-01-18"
    
    print(f"Testing Daily Challenge Writer for {test_date}\n")
    
    # 1. 전체 파이프라인 실행
    filepath = dcw.generate_and_save_daily_challenge(test_date)
    
    # 2. 파일 로드 검증
    print("\n" + "="*60)
    print("📖 Loading saved file...")
    loaded = dcw.load_daily_challenge(test_date)
    
    if loaded:
        print(f"\n✅ File loaded successfully!")
        print(f"\n📊 Challenge Summary:")
        print(f"   Version: {loaded.get('version', 'N/A')}")
        print(f"   Date: {loaded['scenario']['date']}")
        print(f"   Company: {loaded['scenario']['company_name']}")
        print(f"   Product Type: {loaded['scenario']['product_type']}")
        print(f"   Situation: {loaded['scenario']['situation']}")
        
        print(f"\n📋 Problems:")
        print(f"   Total: {loaded['metadata']['total_problems']}")
        print(f"   PA: {loaded['metadata']['pa_count']}")
        print(f"   Stream: {loaded['metadata']['stream_count']}")
        print(f"   Difficulty: Easy {loaded['metadata']['difficulty_distribution']['easy']}, "
              f"Medium {loaded['metadata']['difficulty_distribution']['medium']}, "
              f"Hard {loaded['metadata']['difficulty_distribution']['hard']}")
        
        print(f"\n📁 Tables:")
        for tbl in loaded['scenario']['table_configs']:
            print(f"   - {tbl['full_name']} ({tbl['row_count']:,} rows)")
        
        print(f"\n🎯 Sample Problems:")
        for i, prob in enumerate(loaded['problems'][:3], 1):
            type_badge = "PA" if prob['problem_type'] == 'pa' else "Stream"
            print(f"   {i}. [{type_badge}] {prob['difficulty'].capitalize()}: {prob['question'][:80]}...")
        
        print(f"\n✅ All systems working!")
    else:
        print("❌ Failed to load file")
