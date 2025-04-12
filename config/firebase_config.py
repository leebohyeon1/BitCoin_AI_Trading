# Firebase 클라우드 로깅 설정
FIREBASE_CONFIG = {
    # Firebase 연결 활성화 여부
    "use_firebase": True,
    
    # Firebase 인증 정보 파일 경로
    "credentials_file": "config/firebase_credentials.json",
    
    # Firebase 프로젝트 ID
    "project_id": "bitcoin-ai-trading",
    
    # 로그 컬렉션 명명 규칙
    "collections": {
        "app_logs": "app_logs",
        "trade_logs": "trade_logs",
        "analysis_logs": "analysis_logs",
        "error_logs": "error_logs"
    },
    
    # 로깅 옵션
    "options": {
        "max_log_retention_days": 30,  # 클라우드에 로그 보관 일수
        "batch_size": 10,              # 일괄 업로드할 로그 수 (향후 최적화용)
        "sync_interval": 60,           # 로그 동기화 간격 (초)
    }
}

# 파이어베이스 계정 정보가 없는 경우 아래 샘플을 참고하여 firebase_credentials.json 파일 생성
# {
#   "type": "service_account",
#   "project_id": "bitcoin-ai-trading",
#   "private_key_id": "YOUR_PRIVATE_KEY_ID",
#   "private_key": "YOUR_PRIVATE_KEY",
#   "client_email": "firebase-adminsdk-xxxxx@bitcoin-ai-trading.iam.gserviceaccount.com",
#   "client_id": "YOUR_CLIENT_ID",
#   "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#   "token_uri": "https://oauth2.googleapis.com/token",
#   "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#   "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40bitcoin-ai-trading.iam.gserviceaccount.com",
#   "universe_domain": "googleapis.com"
# }
