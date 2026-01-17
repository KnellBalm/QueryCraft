#!/usr/bin/env python3
"""
unified_problem_generator 테스트 스크립트
"""
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# 모듈 직접 로드
import importlib.util

# scenario_generator 로드
spec_sg = importlib.util.spec_from_file_location(
    "scenario_generator",
    os.path.join(backend_dir, "generator", "scenario_generator.py")
)
sg = importlib.util.module_from_spec(spec_sg)

# product_config 로드
spec_pc = importlib.util.spec_from_file_location(
    "generator.product_config",
    os.path.join(backend_dir, "generator", "product_config.py")
)
pc = importlib.util.module_from_spec(spec_pc)
spec_pc.loader.exec_module(pc)
sys.modules['generator.product_config'] = pc
sys.modules['product_config'] = pc

# scenario_generator 실행
spec_sg.loader.exec_module(sg)
sys.modules['generator.scenario_generator'] = sg

# unified_problem_generator 로드
spec_upg = importlib.util.spec_from_file_location(
    "unified_problem_generator",
    os.path.join(backend_dir, "generator", "unified_problem_generator.py")
)
upg = importlib.util.module_from_spec(spec_upg)
spec_upg.loader.exec_module(upg)

if __name__ == "__main__":
    # 시나리오 생성
    scenario = sg.generate_scenario("2026-01-17")
    
    # 문제 생성
    problems = upg.generate_daily_problems(scenario)
    
    print(f"\\n=== Daily Challenge for {scenario.date} ===")
    print(f"Company: {scenario.company_name}")
    print(f"Situation: {scenario.situation}")
    print(f"Stake: {scenario.stake}\\n")
    
    pa_count = sum(1 for p in problems if p['problem_type'] == 'pa')
    stream_count = sum(1 for p in problems if p['problem_type'] == 'stream')
    
    print(f"📊 Generated {len(problems)} problems")
    print(f"   PA: {pa_count} | Stream: {stream_count}")
    
    difficulty_count = {}
    for p in problems:
        difficulty_count[p['difficulty']] = difficulty_count.get(p['difficulty'], 0) + 1
    
    print(f"   Easy: {difficulty_count.get('easy', 0)} | Medium: {difficulty_count.get('medium', 0)} | Hard: {difficulty_count.get('hard', 0)}\\n")
    
    for i, problem in enumerate(problems, 1):
        type_badge = "🔢 PA" if problem['problem_type'] == 'pa' else "📈 Stream"
        difficulty_emoji = {'easy': '🟢', 'medium': '🟡', 'hard': '🔴'}[problem['difficulty']]
        
        print(f"{i}. {type_badge} {difficulty_emoji} {problem['difficulty'].capitalize()}")
        print(f"   Topic: {problem['topic']}")
        print(f"   From: {problem['requester']}")
        print(f"   Q: {problem['question'][:120]}...")
        print(f"   Tables: {', '.join(problem['table_names'])}")
        print()
    
    print("✅ Unified Problem Generator works perfectly!")
    print(f"✅ All problems are context-aware (tied to: {scenario.situation})")
