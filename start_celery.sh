#!/bin/bash

# 🚀 Celery Worker 및 Beat 실행 스크립트
# 사용법:
#   ./start_celery.sh worker    # Worker만 실행
#   ./start_celery.sh beat      # Beat만 실행
#   ./start_celery.sh all       # Worker와 Beat 모두 실행

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 환경 변수 확인
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env 파일이 없습니다. .env.example을 참고하여 생성해주세요.${NC}"
fi

# Redis 연결 체크
echo -e "${GREEN}🔍 Redis 연결 확인 중...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}❌ Redis에 연결할 수 없습니다. Redis를 먼저 실행해주세요:${NC}"
    echo -e "${YELLOW}   docker-compose -f docker-compose.local.yml up redis -d${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Redis 연결 성공${NC}"

# Worker 실행 함수
start_worker() {
    echo -e "${GREEN}🚀 Celery Worker 시작...${NC}"
    uv run celery -A app.core.celery_app worker \
        --loglevel=info \
        --concurrency=4 \
        --pool=solo
}

# Beat 실행 함수
start_beat() {
    echo -e "${GREEN}⏰ Celery Beat 시작...${NC}"
    uv run celery -A app.core.celery_app beat \
        --loglevel=info
}

# 모두 실행 함수 (백그라운드)
start_all() {
    echo -e "${GREEN}🚀 Celery Worker 및 Beat 시작...${NC}"
    
    # Worker 백그라운드 실행
    uv run celery -A app.core.celery_app worker \
        --loglevel=info \
        --concurrency=4 \
        --pool=solo &
    
    WORKER_PID=$!
    echo -e "${GREEN}✅ Worker 시작 (PID: $WORKER_PID)${NC}"
    
    # 잠시 대기
    sleep 2
    
    # Beat 실행
    uv run celery -A app.core.celery_app beat \
        --loglevel=info
}

# Flower 실행 함수 (모니터링)
start_flower() {
    echo -e "${GREEN}🌸 Celery Flower 시작...${NC}"
    uv run celery -A app.core.celery_app flower \
        --port=5555
}

# 인자에 따른 실행
case "${1:-all}" in
    worker)
        start_worker
        ;;
    beat)
        start_beat
        ;;
    all)
        start_all
        ;;
    flower)
        start_flower
        ;;
    *)
        echo -e "${RED}❌ 잘못된 인자입니다.${NC}"
        echo -e "${YELLOW}사용법: $0 {worker|beat|all|flower}${NC}"
        echo -e "${YELLOW}  worker  - Worker만 실행${NC}"
        echo -e "${YELLOW}  beat    - Beat 스케줄러만 실행${NC}"
        echo -e "${YELLOW}  all     - Worker와 Beat 모두 실행 (기본값)${NC}"
        echo -e "${YELLOW}  flower  - Flower 모니터링 대시보드 실행${NC}"
        exit 1
        ;;
esac

