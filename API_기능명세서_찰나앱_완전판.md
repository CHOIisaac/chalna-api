# 📱 찰나(Chalna) 앱 - 완전한 API 기능명세서

> **경조사 관리 및 인맥 장부 모바일 앱**  
> **대상**: 백엔드 개발팀  
> **작성일**: 2025년 1월  
> **제외 기능**: 게스트북, 베뉴(장소) 관리

---

## 🏗️ **시스템 아키텍처**

### **📱 클라이언트**
- **프레임워크**: React Native 0.79.6 + Expo SDK 53
- **네비게이션**: Expo Router (파일 기반 라우팅)
- **언어**: TypeScript
- **주요 패키지**: @expo/vector-icons, react-native-svg, @react-native-community/datetimepicker

### **🔗 API 통신**
- **프로토콜**: REST API (JSON)
- **인증**: JWT 토큰 기반
- **Base URL**: `https://api.chalna.co.kr/v1`
- **헤더**: `Authorization: Bearer {token}`
- **Content-Type**: `application/json`

---

## 🔧 **상수 및 설정값**

### **📋 1.1 경조사 타입 (EventType)**
```typescript
const EVENT_TYPES = {
  WEDDING: "결혼식",
  FUNERAL: "장례식", 
  BIRTHDAY: "생일",
  FIRST_BIRTHDAY: "돌잔치",
  GRADUATION: "졸업식",
  OPENING: "개업식",
  ANNIVERSARY: "기념일",
  OTHER: "기타"
};

// 프론트엔드에서 사용하는 배열
const eventTypeOptions = ['결혼식', '장례식', '돌잔치', '개업식', '생일', '졸업식', '기념일', '기타'];
```

### **👥 1.2 관계 타입 (RelationshipType)**
```typescript
const RELATIONSHIP_TYPES = {
  FAMILY: "가족",
  FRIEND: "친구",
  COLLEAGUE: "직장동료",
  ACQUAINTANCE: "지인",
  NEIGHBOR: "이웃",
  RELATIVE: "친척",
  TEACHER: "선생님",
  OTHER: "기타"
};
```

### **📊 1.3 상태 타입 (StatusType)**
```typescript
const STATUS_TYPES = {
  PENDING: "예정",
  COMPLETED: "완료",
  IN_PROGRESS: "진행중"
};

// 프론트엔드에서 사용하는 배열
const statusOptions = ['예정', '완료'];
```




### **⚙️ 1.5 앱 설정 변수**
```typescript
const APP_SETTINGS = {
  // 페이지네이션
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  
  // 캐시 시간 (분)
  CACHE_DURATIONS: {
    USER_PROFILE: 60,
    STATISTICS: 5,
    NOTIFICATIONS: 1
  },
  
  // 파일 업로드 제한
  MAX_FILE_SIZE: 5 * 1024 * 1024, // 5MB
  ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/webp'],
  
  // API 제한
  RATE_LIMIT_PER_MINUTE: 100,
  
  // 토큰 만료 시간
  JWT_EXPIRES_IN: '24h',
  REFRESH_TOKEN_EXPIRES_IN: '7d'
};
```

### **📱 1.6 알림 타입**
```typescript
const NOTIFICATION_TYPES = {
  SCHEDULE_REMINDER: 'schedule_reminder',
  EVENT_UPDATE: 'event_update', 
  PAYMENT_DUE: 'payment_due',
  SYSTEM_UPDATE: 'system_update',
  WEEKLY_REPORT: 'weekly_report'
};

```

### **🔢 1.7 검증 규칙**
```typescript
const VALIDATION_RULES = {
  // 사용자 정보
  NAME_MIN_LENGTH: 2,
  NAME_MAX_LENGTH: 50,
  PHONE_PATTERN: /^010-\d{4}-\d{4}$/,
  EMAIL_PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  
  // 경조사 정보
  TITLE_MIN_LENGTH: 2,
  TITLE_MAX_LENGTH: 100,
  LOCATION_MAX_LENGTH: 200,
  MEMO_MAX_LENGTH: 500,
  
  // 금액
  MIN_AMOUNT: 1000,
  MAX_AMOUNT: 10000000,
  
  // 비밀번호
  PASSWORD_MIN_LENGTH: 8,
  PASSWORD_PATTERN: /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]/
};
```

---

## 👤 **2. 사용자 관리 (Authentication)**

### **2.1 로그인**
```http
POST /api/auth/login
Content-Type: application/json

Request Body:
{
  "email": "user@example.com",
  "password": "password123"
}

Response 200:
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "refresh_token_here",
    "user": {
      "id": "user_uuid_123",
      "name": "김철수",
      "email": "user@example.com",
      "phone": "010-1234-5678",
      "profileImage": "https://storage.chalna.co.kr/profiles/user_123.jpg",
      "createdAt": "2025-01-01T00:00:00Z",
      "settings": {
        "notifications": true,
        "autoBackup": true,
        "theme": "light",
        "language": "ko"
      }
    }
  },
  "message": "로그인 성공"
}

Error 401:
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "이메일 또는 비밀번호가 잘못되었습니다.",
    "field": null
  }
}
```

### **2.2 토큰 갱신**
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refreshToken": "refresh_token_here"
}

Response 200:
{
  "success": true,
  "data": {
    "token": "new_jwt_token",
    "refreshToken": "new_refresh_token"
  }
}
```

### **2.3 사용자 정보 조회**
```http
GET /api/user/profile
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "id": "user_uuid_123",
    "name": "김철수",
    "email": "user@example.com", 
    "phone": "010-1234-5678",
    "profileImage": "https://storage.chalna.co.kr/profiles/user_123.jpg",
    "createdAt": "2025-01-01T00:00:00Z",
    "updatedAt": "2025-01-15T10:30:00Z",
    "stats": {
      "totalEvents": 24,
      "totalContacts": 127,
      "totalGiven": 2500000,
      "totalReceived": 2200000,
      "balance": 300000
    },
    "settings": {
      "notifications": true,
      "autoBackup": true,
      "theme": "light",
      "language": "ko"
    }
  }
}
```

### **2.4 사용자 정보 수정**
```http
PUT /api/user/profile
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "김철수",
  "phone": "010-1234-5678",
  "profileImage": "https://storage.chalna.co.kr/profiles/user_123_new.jpg"
}

Response 200:
{
  "success": true,
  "data": {
    "id": "user_uuid_123",
    "name": "김철수",
    "phone": "010-1234-5678",
    "profileImage": "https://storage.chalna.co.kr/profiles/user_123_new.jpg",
    "updatedAt": "2025-01-15T11:00:00Z"
  },
  "message": "프로필이 업데이트되었습니다."
}
```

---

## 📅 **3. 일정 관리 (Schedules)**

### **3.1 일정 목록 조회**
```http
GET /api/schedules?month=2025-01&status=all&type=all&page=1&limit=20
Authorization: Bearer {token}

Query Parameters:
- month: string (YYYY-MM format, optional)
- status: enum ('all'|'예정'|'완료'|'진행중', default: 'all')
- type: enum ('all'|'결혼식'|'장례식'|'돌잔치'|'개업식'|'생일'|'졸업식'|'기념일'|'기타', default: 'all')
- page: number (default: 1)
- limit: number (default: 20, max: 100)
- search: string (제목 검색, optional)
- sortBy: enum ('date'|'amount'|'title'|'createdAt', default: 'date')
- sortOrder: enum ('asc'|'desc', default: 'desc')

Response 200:
{
  "success": true,
  "data": {
    "schedules": [
      {
        "id": "schedule_uuid_123",
        "type": "결혼식",
        "title": "김철수 결혼식",
        "date": "2025-02-15",
        "time": "12:00",
        "location": "롯데호텔 크리스탈볼룸",
        "amount": 100000,
        "status": "예정",
        "memo": "드레스코드: 정장",
        "contactInfo": {
          "host": "김철수, 박영희",
          "phone": "010-1234-5678"
        },
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 3,
      "totalItems": 45,
      "hasNext": true,
      "hasPrev": false
    },
    "statistics": {
      "total": 45,
      "pending": 15,
      "completed": 28,
      "inProgress": 2,
      "thisMonth": 8,
      "nextMonth": 12,
      "totalAmount": 4500000,
      "thisMonthAmount": 800000
    }
  }
}
```

### **3.2 일정 상세 조회**
```http
GET /api/schedules/{scheduleId}
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "id": "schedule_uuid_123",
    "type": "결혼식",
    "title": "김철수 결혼식",
    "date": "2025-02-15",
    "time": "12:00",
    "location": "롯데호텔 크리스탈볼룸",
    "amount": 100000,
    "status": "예정",
    "memo": "드레스코드: 정장\n주차 가능\n2시간 소요 예상",
    "contactInfo": {
      "host": "김철수, 박영희",
      "phone": "010-1234-5678",
      "email": "kim@example.com"
    },
    "additionalInfo": {
      "dressCode": "정장/드레스",
      "giftInfo": "축하금 또는 선물",
      "parking": true,
      "transportInfo": "지하철 2호선 잠실역 3번 출구 도보 5분"
    },
    "relatedContacts": [
      {
        "id": "contact_uuid_456",
        "name": "김철수",
        "relationship": "친구",
        "balance": 50000
      }
    ],
    "createdAt": "2025-01-01T00:00:00Z",
    "updatedAt": "2025-01-01T00:00:00Z"
  }
}
```

### **3.3 일정 추가**
```http
POST /api/schedules
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "결혼식",
  "title": "김철수 결혼식",
  "date": "2025-02-15",
  "time": "12:00",
  "location": "롯데호텔 크리스탈볼룸",
  "amount": 100000,
  "status": "예정",
  "memo": "드레스코드: 정장",
  "contactInfo": {
    "host": "김철수, 박영희",
    "phone": "010-1234-5678",
    "email": "kim@example.com"
  },
  "additionalInfo": {
    "dressCode": "정장/드레스",
    "giftInfo": "축하금",
    "parking": true
  }
}

Response 201:
{
  "success": true,
  "data": {
    "id": "schedule_uuid_new_789",
    "type": "결혼식",
    "title": "김철수 결혼식",
    // ... 생성된 일정 정보
    "createdAt": "2025-01-15T12:00:00Z",
    "updatedAt": "2025-01-15T12:00:00Z"
  },
  "message": "일정이 추가되었습니다."
}

Validation Errors 400:
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력 데이터가 올바르지 않습니다.",
    "details": [
      {
        "field": "title",
        "message": "일정명은 2자 이상 100자 이하로 입력해주세요.",
        "value": "김"
      },
      {
        "field": "amount",
        "message": "금액은 1,000원 이상 10,000,000원 이하로 입력해주세요.",
        "value": 500
      }
    ]
  }
}
```

### **3.4 달력 뷰 데이터**
```http
GET /api/schedules/calendar?year=2025&month=02
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "calendar": [
      {
        "date": "2025-02-15",
        "events": [
          {
            "id": "schedule_uuid_123",
            "type": "결혼식",
            "title": "김철수 결혼식",
            "time": "12:00",
            "status": "예정",
            "amount": 100000,
            "color": "#E53E3E"
          },
          {
            "id": "schedule_uuid_124", 
            "type": "장례식",
            "title": "박영희 어머님 장례식",
            "time": "14:00",
            "status": "예정",
            "amount": 50000,
            "color": "#4A5568"
          }
        ],
        "totalAmount": 150000,
        "eventCount": 2
      }
    ],
    "monthSummary": {
      "totalEvents": 12,
      "totalAmount": 1200000,
      "byType": {
        "결혼식": { "count": 6, "amount": 600000 },
        "장례식": { "count": 2, "amount": 100000 },
        "돌잔치": { "count": 3, "amount": 300000 },
        "기타": { "count": 1, "amount": 200000 }
      }
    }
  }
}
```

---

## 👥 **4. 인맥 장부 (Ledgers/Contacts)**

### **4.1 인맥 목록 조회**
```http
GET /api/contacts?search=김&relationship=all&sort=name&page=1&limit=20
Authorization: Bearer {token}

Query Parameters:
- search: string (이름 검색, optional)
- relationship: enum ('all'|'가족'|'친구'|'직장동료'|'지인'|'이웃'|'친척'|'선생님'|'기타', default: 'all')
- sort: enum ('name'|'balance'|'lastEvent'|'eventCount'|'totalGiven'|'totalReceived', default: 'name')
- order: enum ('asc'|'desc', default: 'asc')
- page: number (default: 1)
- limit: number (default: 20, max: 100)
- balanceFilter: enum ('all'|'positive'|'negative'|'zero', default: 'all')

Response 200:
{
  "success": true,
  "data": {
    "contacts": [
      {
        "id": "contact_uuid_456",
        "name": "김철수",
        "relationship": "친구",
        "phone": "010-1234-5678",
        "email": "kim@example.com",
        "profileImage": "https://storage.chalna.co.kr/contacts/contact_456.jpg",
        "totalGiven": 300000,
        "totalReceived": 250000,
        "balance": 50000,
        "lastEventDate": "2024-12-15",
        "lastEventType": "결혼식",
        "eventCount": 5,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-12-15T14:30:00Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 7,
      "totalItems": 127,
      "hasNext": true,
      "hasPrev": false
    },
    "statistics": {
      "totalContacts": 127,
      "totalGiven": 12500000,
      "totalReceived": 11000000,
      "totalBalance": 1500000,
      "positiveBalance": 85,
      "negativeBalance": 42,
      "zeroBalance": 0,
      "byRelationship": {
        "친구": { "count": 45, "balance": 800000 },
        "가족": { "count": 12, "balance": 500000 },
        "직장동료": { "count": 35, "balance": 200000 },
        "지인": { "count": 25, "balance": -50000 },
        "기타": { "count": 10, "balance": 50000 }
      }
    }
  }
}
```

### **4.2 인맥 상세 조회**
```http
GET /api/contacts/{contactId}
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "contact": {
      "id": "contact_uuid_456",
      "name": "김철수",
      "relationship": "친구",
      "phone": "010-1234-5678", 
      "email": "kim@example.com",
      "profileImage": "https://storage.chalna.co.kr/contacts/contact_456.jpg",
      "address": "서울시 강남구 테헤란로 123",
      "birthday": "1990-05-15",
      "company": "삼성전자",
      "position": "대리",
      "totalGiven": 300000,
      "totalReceived": 250000,
      "balance": 50000,
      "memo": "대학교 동기, 매우 친한 사이",
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-12-15T14:30:00Z"
    },
    "transactions": [
      {
        "id": "transaction_uuid_789",
        "type": "결혼식",
        "title": "김철수 결혼식",
        "date": "2024-12-15",
        "amount": 100000,
        "direction": "given",
        "status": "완료",
        "memo": "축하합니다!",
        "location": "롯데호텔",
        "createdAt": "2024-12-15T14:30:00Z"
      },
      {
        "id": "transaction_uuid_790",
        "type": "생일",
        "title": "김철수 생일",
        "date": "2024-05-15",
        "amount": 50000,
        "direction": "received",
        "status": "완료",
        "memo": "생일 축하",
        "createdAt": "2024-05-15T18:00:00Z"
      }
    ],
    "upcomingEvents": [
      {
        "id": "schedule_uuid_999",
        "type": "기념일",
        "title": "김철수 승진 축하",
        "date": "2025-03-01",
        "estimatedAmount": 100000,
        "status": "예정"
      }
    ],
    "statistics": {
      "relationshipDuration": "1년 2개월",
      "averageGiven": 75000,
      "averageReceived": 62500,
      "mostFrequentEventType": "결혼식",
      "lastInteraction": "2024-12-15"
    }
  }
}
```

### **4.3 장부 기록 추가**
```http
POST /api/contacts/{contactId}/transactions
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "결혼식",
  "title": "김철수 결혼식",
  "date": "2025-02-15",
  "amount": 100000,
  "direction": "given",
  "status": "완료",
  "memo": "축하합니다!",
  "location": "롯데호텔 크리스탈볼룸",
  "scheduleId": "schedule_uuid_123"
}

Response 201:
{
  "success": true,
  "data": {
    "id": "transaction_uuid_new_888",
    "contactId": "contact_uuid_456",
    "type": "결혼식",
    "title": "김철수 결혼식",
    "date": "2025-02-15",
    "amount": 100000,
    "direction": "given",
    "status": "완료",
    "memo": "축하합니다!",
    "location": "롯데호텔 크리스탈볼룸",
    "scheduleId": "schedule_uuid_123",
    "createdAt": "2025-01-15T12:30:00Z",
    "updatedAt": "2025-01-15T12:30:00Z"
  },
  "updatedContact": {
    "totalGiven": 400000,
    "totalReceived": 250000,
    "balance": 150000,
    "lastEventDate": "2025-02-15",
    "lastEventType": "결혼식",
    "eventCount": 6
  },
  "message": "장부 기록이 추가되었습니다."
}
```

---

## 📊 **5. 통계 (Statistics)**

### **5.1 대시보드 통계**
```http
GET /api/statistics/dashboard?period=thisMonth
Authorization: Bearer {token}

Query Parameters:
- period: enum ('thisMonth'|'lastMonth'|'thisYear'|'lastYear', default: 'thisMonth')

Response 200:
{
  "success": true,
  "data": {
    "quickStats": [
      {
        "id": "monthly_wedding_given",
        "title": "이번 달 축의금",
        "amount": "450,000원",
        "rawAmount": 450000,
        "change": "+12.5%",
        "changeValue": 50000,
        "changeLabel": "지난 달 대비",
        "trend": "up",
        "icon": "gift",
        "bgColor": "#E8F5E8",
        "iconColor": "#22C55E",
        "category": "income"
      },
      {
        "id": "monthly_funeral_given",
        "title": "이번 달 조의금", 
        "amount": "150,000원",
        "rawAmount": 150000,
        "change": "-5.2%",
        "changeValue": -8000,
        "changeLabel": "지난 달 대비",
        "trend": "down",
        "icon": "flower",
        "bgColor": "#F5F5F5",
        "iconColor": "#6B7280",
        "category": "expense"
      },
      {
        "id": "yearly_events",
        "title": "연간 경조사",
        "amount": "24건",
        "rawAmount": 24,
        "change": "+8건",
        "changeValue": 8,
        "changeLabel": "작년 대비",
        "trend": "up",
        "icon": "calendar",
        "bgColor": "#EEF2FF",
        "iconColor": "#3B82F6",
        "category": "count"
      },
      {
        "id": "average_wedding_amount",
        "title": "평균 축의금",
        "amount": "75,000원",
        "rawAmount": 75000,
        "change": "±0%",
        "changeValue": 0,
        "changeLabel": "지난 달 동일",
        "trend": "neutral",
        "icon": "trending",
        "bgColor": "#FFF7ED",
        "iconColor": "#F97316",
        "category": "average"
      }
    ],
    "recentEvents": [
      {
        "id": "event_uuid_recent_1",
        "type": "결혼식",
        "title": "김철수 결혼식",
        "date": "2025-01-15",
        "amount": 100000,
        "direction": "given",
        "status": "완료",
        "timeAgo": "3일 전",
        "contactName": "김철수",
        "relationship": "친구"
      }
    ],
    "monthlyOverview": {
      "totalIncome": 600000,
      "totalExpense": 450000,
      "netAmount": 150000,
      "eventCount": 8,
      "completionRate": 87.5
    }
  }
}
```

### **5.2 월별 통계**
```http
GET /api/statistics/monthly?year=2025&months=12
Authorization: Bearer {token}

Query Parameters:
- year: number (default: current year)
- months: number (최근 몇 개월, default: 12, max: 24)

Response 200:
{
  "success": true,
  "data": {
    "monthlyData": [
      {
        "period": "2025-01",
        "month": "1월",
        "income": 200000,
        "expense": 350000,
        "events": 3,
        "net": -150000,
        "completedEvents": 2,
        "pendingEvents": 1,
        "avgAmountPerEvent": 183333,
        "details": {
          "wedding": { "count": 1, "amount": 100000 },
          "funeral": { "count": 1, "amount": 50000 },
          "birthday": { "count": 1, "amount": 200000 }
        }
      }
    ],
    "summary": {
      "totalIncome": 2400000,
      "totalExpense": 4200000,
      "totalEvents": 36,
      "averageMonthlyIncome": 200000,
      "averageMonthlyExpense": 350000,
      "bestMonth": {
        "period": "2024-06",
        "net": 500000
      },
      "worstMonth": {
        "period": "2024-12",
        "net": -800000
      }
    }
  }
}
```

### **5.3 경조사 타입별 통계**
```http
GET /api/statistics/event-types?year=2025&includeIncome=true&includeExpense=true
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "eventTypeStats": [
      {
        "type": "결혼식",
        "count": 8,
        "totalAmount": 800000,
        "averageAmount": 100000,
        "percentage": 45.5,
        "color": "#FF6B6B",
        "trend": "+15%",
        "details": {
          "given": { "count": 6, "amount": 600000 },
          "received": { "count": 2, "amount": 200000 }
        }
      },
      {
        "type": "장례식",
        "count": 3,
        "totalAmount": 300000,
        "averageAmount": 100000,
        "percentage": 18.2,
        "color": "#4ECDC4",
        "trend": "-5%",
        "details": {
          "given": { "count": 3, "amount": 300000 },
          "received": { "count": 0, "amount": 0 }
        }
      }
    ],
    "totals": {
      "totalEvents": 18,
      "totalAmount": 1650000,
      "mostPopularType": "결혼식",
      "highestAmountType": "결혼식"
    }
  }
}
```

### **5.4 관계별 통계**
```http
GET /api/statistics/relationships?year=2025&sortBy=amount&order=desc
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "relationshipStats": [
      {
        "relation": "친구",
        "count": 12,
        "totalAmount": 1200000,
        "avgAmount": 100000,
        "color": "#FF9F43",
        "balance": 200000,
        "details": {
          "given": { "count": 8, "amount": 800000 },
          "received": { "count": 4, "amount": 400000 }
        },
        "topContacts": [
          {
            "name": "김철수",
            "amount": 300000,
            "eventCount": 3
          }
        ]
      },
      {
        "relation": "가족",
        "count": 5,
        "totalAmount": 1000000,
        "avgAmount": 200000,
        "color": "#6C5CE7",
        "balance": -100000,
        "details": {
          "given": { "count": 2, "amount": 400000 },
          "received": { "count": 3, "amount": 600000 }
        }
      }
    ],
    "insights": {
      "mostGenerousRelation": "가족",
      "mostFrequentRelation": "친구",
      "bestBalanceRelation": "친구",
      "totalBalance": 1500000
    }
  }
}
```

---

## 🔔 **6. 알림 (Notifications)**

### **6.1 알림 목록 조회**
```http
GET /api/notifications?read=all&type=all&limit=20&offset=0
Authorization: Bearer {token}

Query Parameters:
- read: enum ('all'|'read'|'unread', default: 'all')
- type: enum ('all'|'schedule_reminder'|'event_update'|'payment_due'|'system_update'|'weekly_report', default: 'all')
- limit: number (default: 20, max: 100)
- offset: number (default: 0)
- sortBy: enum ('createdAt'|'priority', default: 'createdAt')
- order: enum ('desc'|'asc', default: 'desc')

Response 200:
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "notification_uuid_123",
        "title": "김철수 결혼식 알림",
        "message": "💒 결혼식이 곧 다가옵니다!\n\n김철수님의 결혼식이 내일 오후 12시에 진행됩니다. 축하의 마음을 담아 참석해주시면 감사하겠습니다.",
        "type": "schedule_reminder",
        "category": "wedding",
        "priority": "high",
        "read": false,
        "createdAt": "2025-01-15T10:00:00Z",
        "readAt": null,
        "scheduleId": "schedule_uuid_123",
        "actionRequired": true,
        "actions": [
          {
            "type": "view_schedule",
            "label": "일정 보기",
            "url": "/schedules/schedule_uuid_123"
          },
          {
            "type": "mark_completed",
            "label": "완료 처리"
          }
        ],
        "metadata": {
          "eventDate": "2025-01-16T12:00:00Z",
          "location": "롯데호텔 크리스탈볼룸",
          "estimatedAmount": 100000
        }
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 2,
      "totalItems": 15,
      "hasNext": true,
      "hasPrev": false
    },
    "summary": {
      "total": 15,
      "unread": 3,
      "highPriority": 1,
      "thisWeek": 5,
      "actionRequired": 2,
      "byType": {
        "schedule_reminder": 8,
        "event_update": 3,
        "system_update": 2,
        "weekly_report": 2
      }
    }
  }
}
```

### **6.2 알림 상세 조회**
```http
GET /api/notifications/{notificationId}
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "id": "notification_uuid_123",
    "title": "김철수 결혼식 알림",
    "message": "💒 결혼식이 곧 다가옵니다!\n\n김철수님의 결혼식이 내일 오후 12시에 진행됩니다. 축하의 마음을 담아 참석해주시면 감사하겠습니다.\n\n※ 참석 확인 및 축하 인사는 미리 연락 부탁드립니다.",
    "type": "schedule_reminder",
    "category": "wedding",
    "priority": "high",
    "read": false,
    "createdAt": "2025-01-15T10:00:00Z",
    "readAt": null,
    "relatedSchedule": {
      "id": "schedule_uuid_123",
      "title": "김철수 결혼식",
      "date": "2025-01-16",
      "time": "12:00",
      "location": "롯데호텔 크리스탈볼룸",
      "type": "결혼식",
      "amount": 100000,
      "status": "예정"
    },
    "relatedContact": {
      "id": "contact_uuid_456",
      "name": "김철수",
      "relationship": "친구",
      "phone": "010-1234-5678"
    },
    "actions": [
      {
        "type": "view_schedule",
        "label": "일정 보기",
        "url": "/schedules/schedule_uuid_123"
      },
      {
        "type": "call_contact",
        "label": "전화걸기",
        "phone": "010-1234-5678"
      },
      {
        "type": "mark_completed",
        "label": "완료 처리"
      }
    ]
  }
}
```

### **6.3 푸시 토큰 등록/업데이트**
```http
POST /api/notifications/push-token
Authorization: Bearer {token}
Content-Type: application/json

{
  "token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
  "platform": "ios",
  "deviceId": "unique_device_identifier_123",
  "deviceName": "김철수의 iPhone",
  "appVersion": "1.0.0",
  "osVersion": "17.2.1"
}

Response 200:
{
  "success": true,
  "data": {
    "tokenId": "token_uuid_789",
    "token": "ExponentPushToken[xxxxxxxxxxxxxxxxxxxxxx]",
    "platform": "ios",
    "deviceId": "unique_device_identifier_123",
    "isActive": true,
    "registeredAt": "2025-01-15T12:00:00Z"
  },
  "message": "푸시 토큰이 등록되었습니다."
}
```

### **6.4 알림 설정 관리**
```http
GET /api/notifications/settings
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "general": {
      "enabled": true,
      "sound": true,
      "vibration": true,
      "badge": true
    },
    "scheduleReminders": {
      "enabled": true,
      "timing": [
        { "value": 1440, "label": "1일 전", "enabled": true },
        { "value": 60, "label": "1시간 전", "enabled": true },
        { "value": 10, "label": "10분 전", "enabled": false }
      ]
    },
    "eventUpdates": {
      "enabled": true,
      "newEvents": true,
      "eventChanges": true,
      "eventCancellations": true
    },
    "reports": {
      "weeklyReport": true,
      "monthlyReport": false,
      "yearlyReport": true
    },
    "marketing": {
      "promotions": false,
      "newFeatures": true,
      "surveys": false
    }
  }
}

PUT /api/notifications/settings
Authorization: Bearer {token}
Content-Type: application/json

{
  "scheduleReminders": {
    "enabled": false
  },
  "reports": {
    "weeklyReport": false,
    "monthlyReport": true
  }
}
```

---

## 🔧 **7. 설정 (Settings)**

### **7.1 앱 설정 조회**
```http
GET /api/settings
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "notifications": {
      "push": true,
      "sound": true,
      "vibration": true,
      "badge": true,
      "eventReminders": true,
      "weeklyReport": false,
      "monthlyReport": true,
      "reminderTiming": [1440, 60]
    },
    "backup": {
      "auto": true,
      "frequency": "weekly",
      "lastBackup": "2025-01-10T03:00:00Z",
      "nextBackup": "2025-01-17T03:00:00Z",
      "cloudProvider": "icloud"
    },
    "display": {
      "theme": "light",
      "language": "ko",
      "currency": "KRW",
      "dateFormat": "YYYY-MM-DD",
      "timeFormat": "24h"
    },
    "privacy": {
      "analyticsEnabled": true,
      "crashReportsEnabled": true,
      "dataSharingEnabled": false
    },
    "security": {
      "biometricEnabled": false,
      "passcodeEnabled": false,
      "sessionTimeout": 3600
    }
  }
}
```

### **7.2 설정 업데이트**
```http
PUT /api/settings
Authorization: Bearer {token}
Content-Type: application/json

{
  "notifications": {
    "push": false,
    "eventReminders": true,
    "reminderTiming": [1440]
  },
  "backup": {
    "auto": false,
    "frequency": "daily"
  },
  "display": {
    "theme": "dark"
  }
}

Response 200:
{
  "success": true,
  "data": {
    // 업데이트된 전체 설정 객체
  },
  "message": "설정이 업데이트되었습니다."
}
```

### **7.3 데이터 백업**
```http
POST /api/backup/create
Authorization: Bearer {token}
Content-Type: application/json

{
  "includeContacts": true,
  "includeSchedules": true,
  "includeTransactions": true,
  "includeNotifications": false,
  "format": "json",
  "compression": true
}

Response 200:
{
  "success": true,
  "data": {
    "backupId": "backup_uuid_123",
    "filename": "chalna_backup_20250115_120000.zip",
    "downloadUrl": "https://storage.chalna.co.kr/backups/user_123/chalna_backup_20250115_120000.zip",
    "size": 2621440,
    "sizeFormatted": "2.5MB",
    "createdAt": "2025-01-15T12:00:00Z",
    "expiresAt": "2025-01-22T12:00:00Z",
    "includedData": {
      "contacts": 127,
      "schedules": 45,
      "transactions": 238,
      "notifications": 0
    }
  },
  "message": "백업이 생성되었습니다."
}
```

### **7.4 데이터 초기화**
```http
DELETE /api/user/data
Authorization: Bearer {token}
Content-Type: application/json

{
  "confirmPassword": "user_password",
  "deleteType": "schedules",
  "confirmationCode": "DELETE_SCHEDULES"
}

Response 200:
{
  "success": true,
  "data": {
    "deletedItems": {
      "schedules": 45,
      "relatedTransactions": 12
    },
    "completedAt": "2025-01-15T12:30:00Z"
  },
  "message": "일정 데이터가 삭제되었습니다."
}
```

---

## 📤 **8. 데이터 내보내기/가져오기**

### **8.1 데이터 내보내기**
```http
GET /api/export?format=json&type=all&includeImages=false
Authorization: Bearer {token}

Query Parameters:
- format: enum ('json'|'csv'|'excel', default: 'json')
- type: enum ('all'|'schedules'|'contacts'|'transactions'|'statistics', default: 'all')
- includeImages: boolean (default: false)
- dateRange: string ('YYYY-MM-DD,YYYY-MM-DD', optional)

Response 200:
{
  "success": true,
  "data": {
    "exportId": "export_uuid_456",
    "filename": "chalna_export_20250115.json",
    "downloadUrl": "https://storage.chalna.co.kr/exports/user_123/chalna_export_20250115.json",
    "size": 5242880,
    "sizeFormatted": "5.0MB",
    "format": "json",
    "createdAt": "2025-01-15T13:00:00Z",
    "expiresAt": "2025-01-16T13:00:00Z",
    "includedData": {
      "contacts": 127,
      "schedules": 45,
      "transactions": 238,
      "images": 0
    }
  },
  "message": "데이터 내보내기가 완료되었습니다."
}
```

### **8.2 데이터 가져오기**
```http
POST /api/import
Authorization: Bearer {token}
Content-Type: multipart/form-data

Form Data:
- file: [파일]
- format: "json"
- mergeStrategy: "append"
- validateData: true
- createBackup: true

Response 200:
{
  "success": true,
  "data": {
    "importId": "import_uuid_789",
    "status": "completed",
    "importedData": {
      "contacts": {
        "imported": 50,
        "updated": 10,
        "skipped": 5,
        "errors": 2
      },
      "schedules": {
        "imported": 20,
        "updated": 5,
        "skipped": 1,
        "errors": 0
      }
    },
    "backupCreated": {
      "backupId": "backup_uuid_pre_import_123",
      "createdAt": "2025-01-15T14:00:00Z"
    },
    "errors": [
      {
        "row": 3,
        "field": "phone",
        "message": "잘못된 전화번호 형식",
        "value": "010-1234"
      }
    ],
    "completedAt": "2025-01-15T14:05:00Z"
  },
  "message": "데이터 가져오기가 완료되었습니다."
}
```

---

## ⚠️ **9. 오류 처리**

### **9.1 표준 오류 응답**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력 데이터가 올바르지 않습니다.",
    "timestamp": "2025-01-15T12:00:00Z",
    "requestId": "req_uuid_123",
    "details": [
      {
        "field": "email",
        "message": "올바른 이메일 형식이 아닙니다.",
        "value": "invalid-email",
        "code": "INVALID_FORMAT"
      },
      {
        "field": "amount",
        "message": "금액은 1,000원 이상이어야 합니다.",
        "value": 500,
        "code": "MIN_VALUE_ERROR"
      }
    ]
  }
}
```

### **9.2 주요 오류 코드**
| 코드 | 설명 | HTTP Status | 해결방법 |
|------|------|-------------|----------|
| `UNAUTHORIZED` | 인증 실패 | 401 | 로그인 후 재시도 |
| `TOKEN_EXPIRED` | 토큰 만료 | 401 | 토큰 갱신 후 재시도 |
| `FORBIDDEN` | 권한 없음 | 403 | 접근 권한 확인 |
| `NOT_FOUND` | 리소스 없음 | 404 | 존재하는 리소스인지 확인 |
| `VALIDATION_ERROR` | 입력 검증 실패 | 400 | 입력값 형식 확인 |
| `DUPLICATE_ERROR` | 중복 데이터 | 409 | 기존 데이터 확인 후 수정 |
| `RATE_LIMITED` | 요청 제한 초과 | 429 | 잠시 후 재시도 |
| `SERVER_ERROR` | 서버 오류 | 500 | 관리자에게 문의 |
| `MAINTENANCE` | 서버 점검 중 | 503 | 점검 완료 후 재시도 |

### **9.3 에러 코드 상세**
```typescript
const ERROR_CODES = {
  // 인증/권한 관련
  INVALID_CREDENTIALS: "이메일 또는 비밀번호가 잘못되었습니다.",
  TOKEN_EXPIRED: "인증 토큰이 만료되었습니다.",
  REFRESH_TOKEN_INVALID: "갱신 토큰이 유효하지 않습니다.",
  
  // 검증 관련
  INVALID_EMAIL_FORMAT: "올바른 이메일 형식이 아닙니다.",
  INVALID_PHONE_FORMAT: "올바른 전화번호 형식이 아닙니다.",
  PASSWORD_TOO_WEAK: "비밀번호가 너무 약합니다.",
  
  // 데이터 관련
  CONTACT_NOT_FOUND: "연락처를 찾을 수 없습니다.",
  SCHEDULE_NOT_FOUND: "일정을 찾을 수 없습니다.",
  DUPLICATE_CONTACT: "이미 존재하는 연락처입니다.",
  
  // 비즈니스 로직 관련
  AMOUNT_TOO_LOW: "최소 금액보다 작습니다.",
  AMOUNT_TOO_HIGH: "최대 금액을 초과했습니다.",
  INVALID_DATE_RANGE: "잘못된 날짜 범위입니다.",
  
  // 파일 관련
  FILE_TOO_LARGE: "파일 크기가 너무 큽니다.",
  UNSUPPORTED_FILE_TYPE: "지원하지 않는 파일 형식입니다.",
  
  // 시스템 관련
  DATABASE_ERROR: "데이터베이스 오류가 발생했습니다.",
  EXTERNAL_SERVICE_ERROR: "외부 서비스 연결 오류입니다.",
  BACKUP_FAILED: "백업 생성에 실패했습니다."
};
```

---

## 📋 **10. 데이터 모델 정의**

### **10.1 사용자 (User)**
```typescript
interface User {
  id: string;
  email: string;
  name: string;
  phone: string;
  profileImage?: string;
  address?: string;
  birthday?: string;
  settings: UserSettings;
  stats: UserStats;
  createdAt: string;
  updatedAt: string;
  lastLoginAt?: string;
  emailVerified: boolean;
  phoneVerified: boolean;
}

interface UserSettings {
  notifications: NotificationSettings;
  backup: BackupSettings;
  display: DisplaySettings;
  privacy: PrivacySettings;
  security: SecuritySettings;
}

interface UserStats {
  totalEvents: number;
  totalContacts: number;
  totalGiven: number;
  totalReceived: number;
  balance: number;
  averageEventAmount: number;
  mostFrequentEventType: string;
  relationshipDistribution: Record<string, number>;
}
```

### **10.2 일정 (Schedule)**
```typescript
interface Schedule {
  id: string;
  userId: string;
  type: EventType;
  title: string;
  date: string; // YYYY-MM-DD
  time?: string; // HH:MM
  location: string;
  amount: number;
  status: StatusType;
  memo?: string;
  contactInfo?: {
    host?: string;
    phone?: string;
    email?: string;
  };
  additionalInfo?: {
    dressCode?: string;
    giftInfo?: string;
    parking?: boolean;
    transportInfo?: string;
  };
  relatedContactIds?: string[];
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}
```

### **10.3 연락처 (Contact)**
```typescript
interface Contact {
  id: string;
  userId: string;
  name: string;
  relationship: RelationshipType;
  phone?: string;
  email?: string;
  profileImage?: string;
  address?: string;
  birthday?: string;
  company?: string;
  position?: string;
  totalGiven: number;
  totalReceived: number;
  balance: number;
  lastEventDate?: string;
  lastEventType?: EventType;
  eventCount: number;
  memo?: string;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
}
```

### **10.4 거래 (Transaction)**
```typescript
interface Transaction {
  id: string;
  userId: string;
  contactId: string;
  scheduleId?: string;
  type: EventType;
  title: string;
  date: string;
  amount: number;
  direction: 'given' | 'received';
  status: StatusType;
  memo?: string;
  location?: string;
  receiptImage?: string;
  createdAt: string;
  updatedAt: string;
}
```

### **10.5 알림 (Notification)**
```typescript
interface Notification {
  id: string;
  userId: string;
  title: string;
  message: string;
  type: NotificationType;
  category?: string;
  priority: 'low' | 'medium' | 'high';
  read: boolean;
  actionRequired: boolean;
  scheduleId?: string;
  contactId?: string;
  metadata?: Record<string, any>;
  actions?: NotificationAction[];
  createdAt: string;
  readAt?: string;
  expiresAt?: string;
}

interface NotificationAction {
  type: string;
  label: string;
  url?: string;
  phone?: string;
  data?: Record<string, any>;
}
```

---

## 🚀 **11. 성능 및 보안 요구사항**

### **11.1 성능 요구사항**
```typescript
const PERFORMANCE_TARGETS = {
  // API 응답 시간
  RESPONSE_TIME_TARGET: 200, // ms
  RESPONSE_TIME_MAX: 1000, // ms
  
  // 데이터베이스
  DB_QUERY_TIME_TARGET: 50, // ms
  DB_CONNECTION_POOL_SIZE: 20,
  
  // 캐싱
  CACHE_HIT_RATIO_TARGET: 0.85,
  CACHE_TTL_DEFAULT: 300, // 5분
  
  // 페이지네이션
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  
  // 파일 업로드
  MAX_FILE_SIZE: 5 * 1024 * 1024, // 5MB
  IMAGE_RESIZE_QUALITY: 0.8,
  THUMBNAIL_SIZE: 200, // px
  
  // 동시 접속
  CONCURRENT_USERS_TARGET: 1000,
  CONNECTION_TIMEOUT: 30000 // ms
};
```

### **11.2 보안 요구사항**
```typescript
const SECURITY_CONFIG = {
  // JWT 설정
  JWT_SECRET_LENGTH: 256,
  JWT_EXPIRES_IN: '24h',
  REFRESH_TOKEN_EXPIRES_IN: '7d',
  
  // 비밀번호 정책
  PASSWORD_MIN_LENGTH: 8,
  PASSWORD_REQUIRE_UPPERCASE: true,
  PASSWORD_REQUIRE_LOWERCASE: true,
  PASSWORD_REQUIRE_NUMBERS: true,
  PASSWORD_REQUIRE_SYMBOLS: true,
  PASSWORD_HISTORY_COUNT: 5,
  
  // Rate Limiting
  RATE_LIMIT_WINDOW: 60000, // 1분
  RATE_LIMIT_MAX_REQUESTS: 100,
  RATE_LIMIT_MAX_LOGIN_ATTEMPTS: 5,
  ACCOUNT_LOCKOUT_DURATION: 900000, // 15분
  
  // 암호화
  ENCRYPTION_ALGORITHM: 'AES-256-GCM',
  HASH_ALGORITHM: 'SHA-256',
  SALT_ROUNDS: 12,
  
  // CORS 설정
  ALLOWED_ORIGINS: [
    'exp://192.168.1.100:8081',
    'https://chalna.co.kr',
    'https://app.chalna.co.kr'
  ],
  
  // 세션 관리
  SESSION_TIMEOUT: 3600000, // 1시간
  MAX_SESSIONS_PER_USER: 5
};
```

### **11.3 데이터 보안**
```typescript
const DATA_SECURITY = {
  // 개인정보 암호화 필드
  ENCRYPTED_FIELDS: [
    'phone',
    'email',
    'address',
    'birthday'
  ],
  
  // 감사 로그 대상
  AUDIT_ACTIONS: [
    'user_login',
    'user_logout',
    'data_export',
    'data_import',
    'settings_change',
    'password_change',
    'account_deletion'
  ],
  
  // 데이터 보존 정책
  DATA_RETENTION: {
    USER_DATA: '3년',
    AUDIT_LOGS: '1년',
    BACKUP_FILES: '30일',
    TEMPORARY_FILES: '24시간'
  },
  
  // GDPR 준수
  GDPR_COMPLIANCE: {
    DATA_PORTABILITY: true,
    RIGHT_TO_ERASURE: true,
    DATA_MINIMIZATION: true,
    CONSENT_MANAGEMENT: true
  }
};
```

---

## 🧪 **12. 테스트 및 모니터링**

### **12.1 테스트 계정**
```typescript
const TEST_ACCOUNTS = {
  ADMIN: {
    email: 'admin@chalna.co.kr',
    password: 'Admin123!@#',
    role: 'admin'
  },
  USER_BASIC: {
    email: 'test@chalna.co.kr',
    password: 'Test123!@#',
    role: 'user'
  },
  USER_PREMIUM: {
    email: 'premium@chalna.co.kr',
    password: 'Premium123!@#',
    role: 'premium'
  }
};
```

### **12.2 개발 환경 설정**
```typescript
const ENVIRONMENT_CONFIG = {
  DEVELOPMENT: {
    BASE_URL: 'https://api-dev.chalna.co.kr/v1',
    DATABASE_URL: 'postgresql://dev_user:password@dev-db:5432/chalna_dev',
    REDIS_URL: 'redis://dev-redis:6379',
    LOG_LEVEL: 'debug',
    ENABLE_CORS: true,
    RATE_LIMITING: false
  },
  STAGING: {
    BASE_URL: 'https://api-staging.chalna.co.kr/v1',
    DATABASE_URL: 'postgresql://staging_user:password@staging-db:5432/chalna_staging',
    REDIS_URL: 'redis://staging-redis:6379',
    LOG_LEVEL: 'info',
    ENABLE_CORS: true,
    RATE_LIMITING: true
  },
  PRODUCTION: {
    BASE_URL: 'https://api.chalna.co.kr/v1',
    DATABASE_URL: process.env.DATABASE_URL,
    REDIS_URL: process.env.REDIS_URL,
    LOG_LEVEL: 'warn',
    ENABLE_CORS: false,
    RATE_LIMITING: true
  }
};
```

### **12.3 모니터링 지표**
```typescript
const MONITORING_METRICS = {
  // 시스템 메트릭
  SYSTEM: [
    'cpu_usage_percent',
    'memory_usage_percent',
    'disk_usage_percent',
    'network_io_bytes'
  ],
  
  // 애플리케이션 메트릭
  APPLICATION: [
    'api_requests_total',
    'api_request_duration_seconds',
    'api_errors_total',
    'active_users_count',
    'database_connections_active'
  ],
  
  // 비즈니스 메트릭
  BUSINESS: [
    'new_users_daily',
    'events_created_daily',
    'contacts_added_daily',
    'notifications_sent_daily',
    'user_retention_rate'
  ],
  
  // 알림 임계값
  ALERT_THRESHOLDS: {
    API_ERROR_RATE: 0.05, // 5%
    RESPONSE_TIME_P95: 1000, // 1초
    CPU_USAGE: 0.8, // 80%
    MEMORY_USAGE: 0.85, // 85%
    DISK_USAGE: 0.9 // 90%
  }
};
```

---

## 📞 **13. 개발 지원**

### **13.1 API 문서 및 도구**
```typescript
const DEVELOPMENT_RESOURCES = {
  // API 문서
  SWAGGER_UI: 'https://api-dev.chalna.co.kr/docs',
  REDOC: 'https://api-dev.chalna.co.kr/redoc',
  POSTMAN_COLLECTION: 'https://documenter.getpostman.com/view/chalna-api',
  
  // 개발 도구
  HEALTH_CHECK: 'https://api-dev.chalna.co.kr/health',
  STATUS_PAGE: 'https://status.chalna.co.kr',
  METRICS_DASHBOARD: 'https://metrics.chalna.co.kr',
  
  // SDK 및 라이브러리
  JAVASCRIPT_SDK: 'https://github.com/chalna/chalna-js-sdk',
  TYPESCRIPT_TYPES: 'https://github.com/chalna/chalna-types',
  
  // 샘플 코드
  EXAMPLES_REPO: 'https://github.com/chalna/api-examples',
  INTEGRATION_GUIDES: 'https://docs.chalna.co.kr/integration'
};
```

### **13.2 연락처**
```typescript
const SUPPORT_CONTACTS = {
  TECHNICAL: {
    email: 'dev@chalna.co.kr',
    slack: '#dev-chalna',
    response_time: '2시간 이내'
  },
  FRONTEND_TEAM: {
    email: 'frontend@chalna.co.kr',
    lead: '김개발 (kim.dev@chalna.co.kr)',
    mobile: '010-1234-5678'
  },
  API_ISSUES: {
    email: 'api-support@chalna.co.kr',
    emergency: '010-9999-0000',
    escalation: 'cto@chalna.co.kr'
  },
  BUSINESS: {
    email: 'business@chalna.co.kr',
    product_manager: 'pm@chalna.co.kr'
  }
};
```

### **13.3 릴리스 및 배포**
```typescript
const RELEASE_SCHEDULE = {
  // 정기 릴리스
  MAJOR_RELEASE: '분기별 (3개월)',
  MINOR_RELEASE: '월별',
  PATCH_RELEASE: '주별 또는 필요시',
  HOTFIX: '즉시 (긴급시)',
  
  // 배포 환경
  DEPLOYMENT_STAGES: [
    'development',
    'staging', 
    'production'
  ],
  
  // 배포 시간
  DEPLOYMENT_WINDOW: {
    PLANNED: '화요일 02:00-04:00 KST',
    EMERGENCY: '언제든지',
    MAINTENANCE: '일요일 01:00-05:00 KST'
  },
  
  // 롤백 정책
  ROLLBACK_TIME: '15분 이내',
  AUTO_ROLLBACK_TRIGGERS: [
    'error_rate > 5%',
    'response_time > 2s',
    'health_check_fail'
  ]
};
```

---

**📝 이 명세서는 프론트엔드에서 구현된 모든 기능과 변수, 상수를 포함한 완전한 API 명세서입니다. 백엔드 구현 시 이 문서를 참고하여 일관성 있는 API를 개발해주세요.**

**🔄 업데이트**: 이 문서는 프론트엔드 개발 진행에 따라 지속적으로 업데이트됩니다. 최신 버전은 항상 개발팀 공유 저장소에서 확인해주세요.**
