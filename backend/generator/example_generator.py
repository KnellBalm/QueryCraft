# backend/generator/example_generator.py
"""
BaseGenerator 사용 예시

이 파일은 BaseGenerator를 상속받아 새로운 Generator를 구현하는 방법을 보여줍니다.
실제 프로덕션에서는 이 파일을 참고하여 PAGenerator, RCAGenerator 등을 구현할 수 있습니다.
"""
from datetime import date
from backend.generator.base import BaseGenerator, GenerationResult
from backend.generator.validator import DataValidator
from backend.common.logging import get_logger

logger = get_logger(__name__)


class ExampleGenerator(BaseGenerator):
    """
    예시 Generator 구현

    BaseGenerator를 상속받아 다음 메서드를 구현합니다:
    1. generate() - 실제 데이터/문제 생성 로직
    2. validate() - 생성된 데이터 검증 로직
    """

    def __init__(self, name: str = "ExampleGenerator"):
        """
        초기화

        Args:
            name: Generator 이름 (로깅용)
        """
        super().__init__(name)
        self.validator = DataValidator()
        self.generated_data = None

    def generate(self, target_date: str) -> GenerationResult:
        """
        데이터 생성 로직 구현

        Args:
            target_date: 생성 대상 날짜 (YYYY-MM-DD 형식)

        Returns:
            GenerationResult: 생성 결과

        Example:
            generator = ExampleGenerator()
            result = generator.generate("2026-01-16")
            if result.success:
                print(f"생성 성공: {result.data}")
        """
        try:
            logger.info(f"[{self.name}] Generating data for {target_date}")

            # 1. 데이터 생성 예시
            self.generated_data = {
                "date": target_date,
                "total_events": 10000,
                "unique_users": 5000,
                "page_views": 15000,
                "downloads": 3000,
                "signups": 1500
            }

            # 2. 검증 수행
            if not self.validate():
                return GenerationResult(
                    success=False,
                    error="Data validation failed",
                    metadata={"date": target_date}
                )

            # 3. 성공 결과 반환
            return GenerationResult(
                success=True,
                data=self.generated_data,
                metadata={
                    "date": target_date,
                    "records_generated": len(self.generated_data)
                }
            )

        except Exception as e:
            logger.exception(f"[{self.name}] Generation failed: {e}")
            return GenerationResult(
                success=False,
                error=str(e),
                metadata={"date": target_date}
            )

    def validate(self) -> bool:
        """
        생성된 데이터 검증

        DataValidator를 사용하여 논리적 일관성을 검증합니다.

        Returns:
            bool: 검증 성공 여부

        Example:
            if generator.validate():
                print("✓ 검증 통과")
            else:
                print("✗ 검증 실패")
        """
        if not self.generated_data:
            logger.warning(f"[{self.name}] No data to validate")
            return False

        # 1. 퍼널 규칙 검증
        funnel_result = self.validator.validate_funnel(
            self.generated_data,
            rules=[
                ("page_views", "downloads"),
                ("downloads", "signups")
            ]
        )

        if not funnel_result.is_valid:
            logger.error(f"[{self.name}] Funnel validation failed: {funnel_result.errors}")
            return False

        # 2. 수치 범위 검증
        range_result = self.validator.validate_ranges(
            self.generated_data,
            rules={
                "total_events": (0, 1000000),
                "unique_users": (0, 100000)
            }
        )

        if not range_result.is_valid:
            logger.error(f"[{self.name}] Range validation failed: {range_result.errors}")
            return False

        logger.info(f"[{self.name}] Validation passed")
        return True


class PAGenerator(BaseGenerator):
    """
    PA (Product Analytics) 문제 생성기

    실제 구현 시 이 클래스를 완성하여 사용합니다.
    """

    def __init__(self):
        super().__init__("PAGenerator")
        self.validator = DataValidator()

    def generate(self, target_date: str) -> GenerationResult:
        """PA 문제 생성 로직"""
        # TODO: PA 문제 생성 로직 구현
        # 현재는 problems/generator.py의 generate() 함수를 사용
        pass

    def validate(self) -> bool:
        """PA 데이터 검증 로직"""
        # TODO: PA 데이터 검증 규칙 구현
        pass


class StreamGenerator(BaseGenerator):
    """
    Stream 데이터/문제 생성기

    실제 구현 시 이 클래스를 완성하여 사용합니다.
    """

    def __init__(self):
        super().__init__("StreamGenerator")
        self.validator = DataValidator()

    def generate(self, target_date: str) -> GenerationResult:
        """Stream 문제 생성 로직"""
        # TODO: Stream 문제 생성 로직 구현
        # 현재는 problems/generator_stream.py의 generate_stream_problems() 함수를 사용
        pass

    def validate(self) -> bool:
        """Stream 데이터 검증 로직"""
        # TODO: Stream 데이터 검증 규칙 구현
        pass


class RCAGenerator(BaseGenerator):
    """
    RCA (Root Cause Analysis) 시나리오 생성기

    실제 구현 시 이 클래스를 완성하여 사용합니다.
    """

    def __init__(self):
        super().__init__("RCAGenerator")
        self.validator = DataValidator()

    def generate(self, target_date: str) -> GenerationResult:
        """RCA 시나리오 생성 로직"""
        # TODO: RCA 시나리오 생성 로직 구현
        pass

    def validate(self) -> bool:
        """RCA 데이터 검증 로직"""
        # TODO: RCA 데이터 검증 규칙 구현
        pass


# ============ 사용 예시 ============

def example_usage():
    """BaseGenerator 사용 예시"""

    # 1. Generator 인스턴스 생성
    generator = ExampleGenerator(name="MyGenerator")

    # 2. run() 메서드로 실행 (시간 측정, 로깅, 예외 처리 포함)
    result = generator.run("2026-01-16")

    # 3. 결과 확인
    if result.success:
        print(f"✓ 생성 성공!")
        print(f"  - 소요 시간: {result.duration_seconds:.2f}초")
        print(f"  - 생성 데이터: {result.data}")
    else:
        print(f"✗ 생성 실패: {result.error}")

    # 4. 결과 로깅 (선택)
    generator.log_result(result)

    # 5. 마지막 결과 조회
    last_result = generator.last_result
    print(f"\n마지막 실행 결과: {last_result.to_dict()}")


def batch_generation_example():
    """여러 날짜에 대해 일괄 생성 예시"""
    from datetime import timedelta

    generator = ExampleGenerator()
    start_date = date(2026, 1, 1)

    results = []
    for i in range(7):  # 7일치 생성
        target = (start_date + timedelta(days=i)).isoformat()
        result = generator.run(target)
        results.append(result)

        if result.success:
            print(f"✓ {target}: {result.duration_seconds:.2f}s")
        else:
            print(f"✗ {target}: {result.error}")

    # 전체 성공률 계산
    success_count = sum(1 for r in results if r.success)
    print(f"\n성공률: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")


if __name__ == "__main__":
    print("=== BaseGenerator 사용 예시 ===\n")
    example_usage()
    print("\n=== 일괄 생성 예시 ===\n")
    batch_generation_example()
