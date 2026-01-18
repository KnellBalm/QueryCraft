# Cloud Scheduler Cron 설정 Implementation Plan

## 🎯 목표

기존에 생성된 Cloud Scheduler `querycraft-daily-generation`에 Cron 표현식과 타임존을 설정하여 매일 정해진 시간에 자동 실행되도록 구성합니다.

---

## 📋 현재 상태

### 완료된 작업 ✅
- Scheduler 생성: `querycraft-daily-generation`
- 대상 URL 설정: Cloud Run Worker Job
- 서비스 계정 권한 부여 (OIDC)

### 미완료 작업 ❌
- Cron 표현식 설정
- 타임존 설정 (`Asia/Seoul`)
- Cloud Logging 알림 규칙
- (선택) Slack/이메일 알림

---

## 🔧 Proposed Changes

### 1. Cron 표현식 및 타임존 설정

#### 1-1. GCP Console 접속

```
https://console.cloud.google.com/cloudscheduler
```

#### 1-2. Scheduler 편집

1. **Scheduler 선택**: `querycraft-daily-generation` 클릭
2. **편집 버튼** 클릭 (상단 또는 "⋮" 메뉴)

#### 1-3. 설정 값 입력

| 항목 | 설정 값 | 설명 |
|------|---------|------|
| **Frequency** (빈도) | `0 1 * * *` | 매일 오전 1시 |
| **Timezone** (타임존) | `Asia/Seoul` | 한국 표준시(KST) |

> **💡 Cron 표현식 설명**
> - `0 1 * * *` = 매일 오전 1시 0분
> - KST 오전 1시 = UTC 16:00 (전날)

> [!WARNING]
> **타임존 주의사항**
> - Cloud Scheduler의 기본 타임존은 UTC입니다
> - 반드시 `Asia/Seoul`로 설정해야 한국 시간 기준으로 작동합니다
> - UTC로 설정 시 `0 16 * * *` (UTC 16:00 = KST 01:00)로 입력해야 합니다

---

### 2. 재시도 정책 (Retry Configuration)

#### 2-1. 재시도 설정

Cloud Scheduler 편집 화면에서 "Retry configuration" 섹션:

| 항목 | 권장 값 | 설명 |
|------|---------|------|
| **Max retry attempts** | `3` | 최대 3회 재시도 |
| **Max retry duration** | `1800s` (30분) | 재시도 최대 기간 |
| **Min backoff duration** | `5s` | 최소 대기 시간 |
| **Max backoff duration** | `3600s` (1시간) | 최대 대기 시간 |
| **Max doublings** | `5` | 백오프 2배 증가 최대 횟수 |

> **재시도 전략**
> - 실패 시 5초 후 첫 재시도
> - 이후 지수적으로 증가 (10s, 20s, 40s, ...)
> - 최대 1시간까지 대기
> - 30분 내 3회 재시도 후 최종 실패

---

### 3. Cloud Logging 알림 규칙

#### 3-1. Logging 쿼리

Cloud Run Worker 실패 로그를 감지하는 쿼리:

```
resource.type="cloud_run_job"
resource.labels.job_name="querycraft-worker"
severity>=ERROR
```

#### 3-2. 알림 채널 생성

**GCP Console → Monitoring → Alerting → Notification Channels**

1. **이메일 채널**
   - Channel Type: Email
   - Display Name: `QueryCraft Admin Email`
   - Email Address: 관리자 이메일

2. **(선택) Slack 채널**
   - Channel Type: Slack
   - Display Name: `QueryCraft Alerts`
   - Slack Webhook URL: `https://hooks.slack.com/services/...`

#### 3-3. 알림 정책 생성

**GCP Console → Monitoring → Alerting → Create Policy**

```yaml
Display Name: "QueryCraft Worker Failure Alert"

Conditions:
  - Log match:
      Filter: |
        resource.type="cloud_run_job"
        resource.labels.job_name="querycraft-worker"
        severity>=ERROR
      
      Duration: 1 minute
      Alignment: Count
      Threshold: count > 0

Notifications:
  - Channels: 
      - QueryCraft Admin Email
      - (Optional) QueryCraft Alerts Slack

Documentation:
  "QueryCraft Worker job failed during scheduled execution.
   Check Cloud Run logs for details: 
   https://console.cloud.google.com/run/jobs/details/asia-northeast1/querycraft-worker/logs"
```

---

### 4. (선택) Slack 알림 고급 설정

#### 4-1. Slack Webhook 생성

1. Slack 워크스페이스 → Apps → Incoming Webhooks
2. Add to Channel → `#querycraft-alerts` 채널 선택
3. Webhook URL 복사

#### 4-2. Cloud Function으로 커스텀 알림

**목적**: 더 상세한 정보와 포맷팅된 메시지 전송

```python
# functions/slack_alert.py
import json
import requests
from flask import Request

SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

def send_alert(request: Request):
    """Cloud Logging에서 트리거된 알림을 Slack으로 전송"""
    
    log_entry = request.get_json()
    
    message = {
        "text": "⚠️ *QueryCraft Worker 실패 알림*",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⚠️ QueryCraft Worker Job Failed"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{log_entry.get('timestamp')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{log_entry.get('severity')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:*\n```{log_entry.get('textPayload', 'N/A')}```"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Logs"
                        },
                        "url": "https://console.cloud.google.com/run/jobs/details/asia-northeast1/querycraft-worker/logs"
                    }
                ]
            }
        ]
    }
    
    response = requests.post(SLACK_WEBHOOK, json=message)
    return f"Slack notification sent: {response.status_code}"
```

배포:
```bash
gcloud functions deploy querycraft-slack-alert \
  --runtime python312 \
  --trigger-topic querycraft-worker-errors \
  --entry-point send_alert \
  --region asia-northeast1
```

---

## 🧪 Verification Plan

### 1. 수동 테스트

#### 1-1. Scheduler 즉시 실행

```bash
gcloud scheduler jobs run querycraft-daily-generation --location=asia-northeast1
```

**기대 결과**:
- Cloud Run Worker Job 실행됨
- 데이터 및 문제 생성 완료
- 성공 로그 확인

#### 1-2. 실패 시나리오 테스트

Worker에 일부러 에러 발생시켜 재시도 및 알림 작동 확인:

```python
# worker/main.py (임시 수정)
def main():
    raise Exception("Test failure for alert testing")
```

**기대 결과**:
- 3회 재시도됨
- 30분 후 최종 실패
- 이메일/Slack 알림 수신

### 2. 로그 확인

```bash
# Scheduler 실행 로그
gcloud scheduler jobs describe querycraft-daily-generation --location=asia-northeast1

# Worker 실행 로그
gcloud logging read "resource.type=cloud_run_job 
  AND resource.labels.job_name=querycraft-worker" \
  --limit 50 --format json
```

### 3. 다음날 자동 실행 확인

- 다음날 오전 1시 이후 확인
- Supabase `problems` 테이블에 새 문제 생성 확인
- DuckDB 데이터 업데이트 확인

---

## 📊 gcloud CLI 명령어 참조

### Scheduler 상태 확인
```bash
gcloud scheduler jobs describe querycraft-daily-generation \
  --location=asia-northeast1
```

### Scheduler 업데이트 (CLI 방식)
```bash
gcloud scheduler jobs update http querycraft-daily-generation \
  --location=asia-northeast1 \
  --schedule="0 1 * * *" \
  --time-zone="Asia/Seoul"
```

### 다음 실행 시간 확인
```bash
gcloud scheduler jobs describe querycraft-daily-generation \
  --location=asia-northeast1 \
  --format="value(schedule, timeZone, status.nextRun)"
```

---

## 🚨 Troubleshooting

### 문제: Scheduler가 실행되지 않음

**원인 체크리스트**:
1. Cron 표현식 오류 → [crontab.guru](https://crontab.guru/) 에서 검증
2. 타임존 불일치 → `Asia/Seoul` 확인
3. 서비스 계정 권한 → `roles/run.developer` 확인
4. Worker Job 상태 → Cloud Run Job이 활성화되어 있는지 확인

### 문제: 재시도가 작동하지 않음

**해결 방법**:
- Cloud Scheduler의 "Retry configuration" 재확인
- Worker의 Exit Code 확인 (0이 아닌 값이어야 재시도됨)

### 문제: 알림이 오지 않음

**해결 방법**:
1. Notification Channel 활성화 확인
2. Alert Policy 조건 재확인
3. Test 버튼으로 알림 채널 테스트

---

## 📝 완료 체크리스트

- [ ] GCP Console에서 Cron 표현식 `0 1 * * *` 설정
- [ ] 타임존 `Asia/Seoul` 설정
- [ ] 재시도 정책 구성 (3회, 30분, 지수 백오프)
- [ ] 알림 채널 생성 (이메일 필수, Slack 선택)
- [ ] 알림 정책 생성 및 활성화
- [ ] 수동 테스트 실행 및 로그 확인
- [ ] 실패 시나리오 테스트
- [ ] 다음날 자동 실행 확인

---

## 🔗 참고 자료

- [Cloud Scheduler 문서](https://cloud.google.com/scheduler/docs)
- [Cron 표현식 가이드](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules)
- [Cloud Run Job 트리거](https://cloud.google.com/run/docs/execute/jobs-on-schedule)
- [Cloud Monitoring 알림](https://cloud.google.com/monitoring/alerts)
