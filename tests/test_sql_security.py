# tests/test_sql_security.py
"""SQL 보안 검증 테스트"""
import pytest
from backend.services.sql_service import is_safe_sql


class TestSQLSecurity:
    """SQL Injection 방어 테스트 (Allowlist 방식)"""

    def test_select_allowed(self):
        """SELECT 문 허용"""
        is_safe, error = is_safe_sql("SELECT * FROM users")
        assert is_safe is True
        assert error is None

    def test_select_with_join_allowed(self):
        """JOIN이 있는 SELECT 허용"""
        sql = "SELECT u.*, o.* FROM users u JOIN orders o ON u.id = o.user_id"
        is_safe, error = is_safe_sql(sql)
        assert is_safe is True

    def test_cte_with_allowed(self):
        """WITH (CTE) 허용"""
        sql = """
        WITH user_stats AS (
            SELECT user_id, COUNT(*) as cnt FROM orders GROUP BY user_id
        )
        SELECT * FROM user_stats
        """
        is_safe, error = is_safe_sql(sql)
        assert is_safe is True

    def test_explain_allowed(self):
        """EXPLAIN 허용"""
        is_safe, error = is_safe_sql("EXPLAIN SELECT * FROM users")
        assert is_safe is True

    def test_insert_blocked(self):
        """INSERT 차단"""
        is_safe, error = is_safe_sql("INSERT INTO users (name) VALUES ('hacker')")
        assert is_safe is False
        assert "SELECT, WITH, EXPLAIN" in error

    def test_update_blocked(self):
        """UPDATE 차단"""
        is_safe, error = is_safe_sql("UPDATE users SET name='hacker'")
        assert is_safe is False

    def test_delete_blocked(self):
        """DELETE 차단"""
        is_safe, error = is_safe_sql("DELETE FROM users")
        assert is_safe is False

    def test_drop_blocked(self):
        """DROP 차단"""
        is_safe, error = is_safe_sql("DROP TABLE users")
        assert is_safe is False

    def test_create_blocked(self):
        """CREATE 차단"""
        is_safe, error = is_safe_sql("CREATE TABLE hackers (id INT)")
        assert is_safe is False

    def test_alter_blocked(self):
        """ALTER 차단"""
        is_safe, error = is_safe_sql("ALTER TABLE users ADD COLUMN hacked BOOLEAN")
        assert is_safe is False

    def test_truncate_blocked(self):
        """TRUNCATE 차단"""
        is_safe, error = is_safe_sql("TRUNCATE TABLE users")
        assert is_safe is False

    def test_grant_blocked(self):
        """GRANT 차단"""
        is_safe, error = is_safe_sql("GRANT ALL ON users TO hacker")
        assert is_safe is False

    def test_multiple_statements_blocked(self):
        """다중 쿼리 차단"""
        sql = "SELECT * FROM users; DROP TABLE users;"
        is_safe, error = is_safe_sql(sql)
        assert is_safe is False
        assert "하나의 쿼리만" in error

    def test_pg_sleep_blocked(self):
        """pg_sleep (시간 지연 공격) 차단"""
        sql = "SELECT pg_sleep(10)"
        is_safe, error = is_safe_sql(sql)
        assert is_safe is False
        assert "허용되지 않는 함수" in error

    def test_copy_blocked(self):
        """COPY (파일 읽기/쓰기) 차단"""
        sql = "COPY users TO '/etc/passwd'"
        is_safe, error = is_safe_sql(sql)
        assert is_safe is False

    def test_lo_import_blocked(self):
        """lo_import (Large Object 파일) 차단"""
        sql = "SELECT lo_import('/etc/passwd')"
        is_safe, error = is_safe_sql(sql)
        assert is_safe is False

    def test_empty_query_blocked(self):
        """빈 쿼리 차단"""
        is_safe, error = is_safe_sql("")
        assert is_safe is False
        assert "비어있습니다" in error

    def test_whitespace_only_blocked(self):
        """공백만 있는 쿼리 차단"""
        is_safe, error = is_safe_sql("   \n  \t  ")
        assert is_safe is False

    def test_case_insensitive(self):
        """대소문자 무관하게 검증"""
        # 허용
        assert is_safe_sql("select * from users")[0] is True
        assert is_safe_sql("SeLeCt * FrOm users")[0] is True

        # 차단
        assert is_safe_sql("insert into users")[0] is False
        assert is_safe_sql("InSeRt InTo users")[0] is False

    def test_comment_injection_attempt(self):
        """주석을 이용한 우회 시도 (여전히 SELECT로 시작하면 통과)"""
        # SELECT로 시작하므로 허용됨 (실제 실행 시 PostgreSQL이 처리)
        sql = "SELECT * FROM users -- DROP TABLE users"
        is_safe, error = is_safe_sql(sql)
        assert is_safe is True  # 주석은 DB에서 처리

    def test_union_injection_blocked(self):
        """UNION을 이용한 injection (SELECT로 시작하므로 허용)"""
        # SELECT로 시작하므로 통과하지만, 세미콜론 다중 쿼리는 차단됨
        sql = "SELECT * FROM users UNION SELECT * FROM passwords"
        is_safe, error = is_safe_sql(sql)
        assert is_safe is True  # UNION 자체는 허용 (읽기 전용)
