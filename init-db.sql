-- 🗄️ 찰나(Chalna) API 데이터베이스 초기화 스크립트
-- PostgreSQL 데이터베이스 및 사용자 설정

-- 데이터베이스 생성 (이미 존재하면 무시)
SELECT 'CREATE DATABASE chalna'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'chalna')\gexec

-- 확장 프로그램 설치 (UUID 생성용)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 타임존 설정
SET timezone = 'Asia/Seoul';

-- 한국어 설정을 위한 collation (선택사항)
-- CREATE COLLATION IF NOT EXISTS korean (provider = libc, locale = 'ko_KR.UTF-8');

-- 초기 설정 완료 메시지
SELECT 'Database initialization completed!' as status;
