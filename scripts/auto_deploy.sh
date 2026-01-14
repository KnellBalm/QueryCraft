#!/bin/bash

# QueryCraft 워크스테이션 자동 배포 스크립트 (dev 브랜치용)
# 1분마다 cron으로 실행됨

PROJECT_DIR="/home/naca11/QueryCraft"
cd $PROJECT_DIR

# 1. 변경사항 fetch
git fetch origin dev > /dev/null 2>&1

# 2. 로컬과 원격 차이 비교
LOCAL=$(git rev-parse dev)
REMOTE=$(git rev-parse origin/dev)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date)] New changes detected in dev branch. Updating..."
    
    # 3. Pull 및 브랜치 체크아웃
    git checkout dev
    git pull origin dev
    
    # 4. 도커 재시작
    docker compose -f docker-compose.dev.yml up -d --build
    
    echo "[$(date)] Deployment finished."
else
    # 변경사항 없음
    # echo "[$(date)] No changes."
    exit 0
fi
