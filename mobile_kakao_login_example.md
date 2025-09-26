# 모바일 카카오 로그인 구현 가이드

## 1. 카카오 개발자 콘솔 설정

### 1.1 앱 등록
1. [Kakao Developers](https://developers.kakao.com/) 접속
2. "내 애플리케이션" → "애플리케이션 추가하기"
3. 앱 이름: "Chalna"
4. REST API 키 복사

### 1.2 플랫폼 설정
- **안드로이드**: 패키지명 설정 (예: `com.yourcompany.chalna`)
- **iOS**: 번들 ID 설정 (예: `com.yourcompany.chalna`)

## 2. React Native Expo 설정

### 2.1 패키지 설치
```bash
npx expo install expo-auth-session expo-crypto
npm install @react-native-kakao/sdk
```

### 2.2 app.json 설정
```json
{
  "expo": {
    "name": "Chalna",
    "slug": "chalna-app",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "light",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "plugins": [
      [
        "@react-native-kakao/sdk",
        {
          "kakaoAppKey": "your_kakao_app_key_here"
        }
      ]
    ],
    "android": {
      "package": "com.yourcompany.chalna"
    },
    "ios": {
      "bundleIdentifier": "com.yourcompany.chalna"
    }
  }
}
```

## 3. 카카오 로그인 구현

### 3.1 카카오 로그인 서비스
```typescript
// services/kakaoAuthService.ts
import { KakaoOAuthToken, login } from '@react-native-kakao/sdk';

export class KakaoAuthService {
  static async loginWithKakao(): Promise<string> {
    try {
      // 카카오 로그인
      const token: KakaoOAuthToken = await login();
      
      // 액세스 토큰 반환
      return token.accessToken;
    } catch (error) {
      console.error('카카오 로그인 실패:', error);
      throw error;
    }
  }
}
```

### 3.2 로그인 컴포넌트
```typescript
// components/KakaoLoginButton.tsx
import React from 'react';
import { TouchableOpacity, Text, StyleSheet, Alert } from 'react-native';
import { KakaoAuthService } from '../services/kakaoAuthService';

interface KakaoLoginButtonProps {
  onLoginSuccess: (jwtToken: string) => void;
}

export const KakaoLoginButton: React.FC<KakaoLoginButtonProps> = ({ onLoginSuccess }) => {
  const handleKakaoLogin = async () => {
    try {
      // 1. 카카오 로그인
      const kakaoAccessToken = await KakaoAuthService.loginWithKakao();
      
      // 2. 백엔드에 액세스 토큰 전송 (POST body로 안전하게 전송)
      const response = await fetch('http://192.168.0.95:8000/api/v1/kakao/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          access_token: kakaoAccessToken
        }),
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // 3. JWT 토큰 저장 및 콜백 호출
        onLoginSuccess(data.access_token);
        
        Alert.alert('로그인 성공', '카카오 로그인이 완료되었습니다.');
      } else {
        throw new Error('서버 로그인 실패');
      }
    } catch (error) {
      console.error('로그인 오류:', error);
      Alert.alert('로그인 실패', '로그인 중 오류가 발생했습니다.');
    }
  };

  return (
    <TouchableOpacity style={styles.button} onPress={handleKakaoLogin}>
      <Text style={styles.buttonText}>카카오로 로그인</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    backgroundColor: '#FEE500',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
```

### 3.3 메인 앱에서 사용
```typescript
// App.tsx
import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { KakaoLoginButton } from './components/KakaoLoginButton';

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [jwtToken, setJwtToken] = useState<string | null>(null);

  const handleLoginSuccess = (token: string) => {
    setJwtToken(token);
    setIsLoggedIn(true);
    
    // 토큰을 AsyncStorage에 저장
    // AsyncStorage.setItem('jwt_token', token);
  };

  if (isLoggedIn) {
    return (
      <View style={styles.container}>
        <Text>로그인 성공! JWT 토큰: {jwtToken?.substring(0, 20)}...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <KakaoLoginButton onLoginSuccess={handleLoginSuccess} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
});
```

## 4. API 호출 시 JWT 토큰 사용

```typescript
// services/apiService.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

export class ApiService {
  static async getAuthHeaders() {
    const token = await AsyncStorage.getItem('jwt_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    };
  }

  static async getProtectedData() {
    try {
      const headers = await this.getAuthHeaders();
      
      const response = await fetch('http://192.168.0.95:8000/api/v1/home/monthly-stats', {
        method: 'GET',
        headers,
      });
      
      if (response.ok) {
        return await response.json();
      } else {
        throw new Error('API 호출 실패');
      }
    } catch (error) {
      console.error('API 호출 오류:', error);
      throw error;
    }
  }
}
```

## 5. 테스트 방법

### 5.1 백엔드 서버 실행
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5.2 모바일 앱 실행
```bash
npx expo start
```

### 5.3 로그인 테스트
1. 모바일 앱에서 "카카오로 로그인" 버튼 클릭
2. 카카오 로그인 화면에서 로그인
3. 백엔드에서 JWT 토큰 발급 확인
4. 인증된 API 호출 테스트

## 6. 보안 주의사항

1. **토큰 전송**: 카카오 액세스 토큰은 POST body로만 전송 (쿼리 파라미터 사용 금지)
2. **HTTPS 사용**: 프로덕션에서는 반드시 HTTPS 사용
3. **토큰 저장**: JWT 토큰을 안전하게 저장 (AsyncStorage 사용)
4. **토큰 만료**: 카카오 액세스 토큰은 일정 시간 후 만료되므로 적절한 갱신 처리
5. **에러 처리**: 네트워크 오류, 로그인 실패 등에 대한 적절한 처리

## 7. 기타 주의사항

1. **네트워크 설정**: 모바일 앱과 백엔드 서버가 같은 네트워크에 있어야 함
2. **카카오 앱 키**: app.json에 올바른 카카오 앱 키 설정
3. **패키지명/번들ID**: 카카오 개발자 콘솔과 일치해야 함
