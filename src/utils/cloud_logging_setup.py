#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
클라우드 로깅 설정 유틸리티 스크립트
Firebase Cloud Firestore 연결 및 설정을 도와줍니다.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent.parent.parent.absolute()

def check_firebase_setup():
    """Firebase 설정 상태 확인"""
    credentials_path = Path("C:\\firebase_credentials.json")
    sample_path = project_root / "config" / "firebase_credentials.sample.json"
    config_path = project_root / "config" / "firebase_config.py"
    
    # 설정 파일 존재 여부 확인
    if not config_path.exists():
        print("[오류] firebase_config.py 파일이 없습니다. 프로젝트 설정이 올바른지 확인하세요.")
        return False
        
    # 인증 파일 확인
    if not credentials_path.exists():
        print(f"[오류] firebase_credentials.json 파일이 없습니다. {sample_path} 파일을 참고하여 생성하세요.")
        return False
    
    # 인증 파일 내용 검증
    try:
        with open(credentials_path, 'r', encoding='utf-8') as f:
            creds = json.load(f)
            
        # 필요한 키가 있는지 확인
        required_keys = ["type", "project_id", "private_key_id", "private_key", "client_email"]
        missing_keys = [key for key in required_keys if key not in creds]
        
        if missing_keys:
            print(f"[오류] firebase_credentials.json 파일에 다음 필드가 없습니다: {', '.join(missing_keys)}")
            return False
            
        # 기본값이 수정되었는지 확인
        if creds.get("private_key") == "YOUR_PRIVATE_KEY":
            print("[오류] firebase_credentials.json 파일의 값이 아직 기본값입니다. Firebase 콘솔에서 발급받은 실제 인증 정보로 업데이트하세요.")
            return False
            
        print("[성공] Firebase 인증 정보가 올바르게 설정되었습니다.")
        print(f"- 프로젝트 ID: {creds.get('project_id')}")
        print(f"- 클라이언트 이메일: {creds.get('client_email')}")
        return True
        
    except json.JSONDecodeError:
        print("[오류] firebase_credentials.json 파일이 올바른 JSON 형식이 아닙니다.")
        return False
    except Exception as e:
        print(f"[오류] 인증 파일 확인 중 오류가 발생했습니다: {e}")
        return False

def test_firebase_connection():
    """Firebase 연결 테스트"""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        credentials_path = Path("C:\\firebase_credentials.json")
        
        # 이미 초기화되었는지 확인
        try:
            firebase_admin.get_app()
            print("[알림] Firebase가 이미 초기화되어 있습니다.")
        except ValueError:
            # 초기화되지 않은 경우에만 초기화
            cred = credentials.Certificate(str(credentials_path))
            firebase_admin.initialize_app(cred)
            print("[성공] Firebase 앱이 초기화되었습니다.")
        
        # Firestore 연결 테스트
        db = firestore.client()
        
        # 테스트 문서 작성
        test_ref = db.collection('test_logs').document('test_connection')
        test_ref.set({
            'timestamp': firestore.SERVER_TIMESTAMP,
            'message': 'Firebase 연결 테스트 성공',
            'level': 'info'
        })
        
        # 테스트 문서 읽기
        test_doc = test_ref.get()
        if test_doc.exists:
            print("[성공] Firestore 연결 및 쓰기/읽기 테스트 완료!")
            
            # 테스트 후 문서 삭제
            test_ref.delete()
            print("[정리] 테스트 문서가 삭제되었습니다.")
            return True
        else:
            print("[오류] 테스트 문서를 찾을 수 없습니다.")
            return False
    
    except ImportError:
        print("[오류] firebase-admin 패키지가 설치되지 않았습니다. 다음 명령어로 설치하세요:")
        print("pip install firebase-admin")
        return False
    except Exception as e:
        print(f"[오류] Firebase 연결 테스트 중 오류가 발생했습니다: {e}")
        return False

def create_sample_credentials():
    """샘플 인증 파일 복사"""
    sample_path = project_root / "config" / "firebase_credentials.sample.json"
    credentials_path = Path("C:\\firebase_credentials.json")
    
    if credentials_path.exists():
        print(f"[알림] {credentials_path} 파일이 이미 존재합니다. 덮어쓰지 않습니다.")
        return
    
    if not sample_path.exists():
        print(f"[오류] {sample_path} 파일이 없습니다.")
        return
    
    # 샘플 파일 복사
    with open(sample_path, 'r', encoding='utf-8') as src:
        with open(credentials_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    
    print(f"[성공] {credentials_path} 파일이 생성되었습니다.")
    print("[안내] 생성된 파일을 Firebase 콘솔에서 발급받은 실제 인증 정보로 업데이트하세요.")

def toggle_firebase_logging(enable=True):
    """Firebase 로깅 활성화/비활성화"""
    config_file = project_root / "config" / "firebase_config.py"
    
    if not config_file.exists():
        print(f"[오류] {config_file} 파일이 없습니다.")
        return False
    
    try:
        # 파일 내용 읽기
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # use_firebase 값 변경
        if "use_firebase\": True" in content and not enable:
            content = content.replace("use_firebase\": True", "use_firebase\": False")
            action = "비활성화"
        elif "use_firebase\": False" in content and enable:
            content = content.replace("use_firebase\": False", "use_firebase\": True")
            action = "활성화"
        else:
            if enable:
                print("[알림] Firebase 로깅이 이미 활성화되어 있습니다.")
            else:
                print("[알림] Firebase 로깅이 이미 비활성화되어 있습니다.")
            return True
        
        # 파일 다시 쓰기
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[성공] Firebase 로깅이 {action}되었습니다.")
        return True
        
    except Exception as e:
        print(f"[오류] 설정 파일 수정 중 오류가 발생했습니다: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Firebase Cloud 로깅 설정 유틸리티")
    
    # 명령어 그룹 추가
    command_group = parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument("--check", action="store_true", help="Firebase 설정 상태 확인")
    command_group.add_argument("--test", action="store_true", help="Firebase 연결 테스트")
    command_group.add_argument("--create-sample", action="store_true", help="샘플 인증 파일 생성")
    command_group.add_argument("--enable", action="store_true", help="Firebase 로깅 활성화")
    command_group.add_argument("--disable", action="store_true", help="Firebase 로깅 비활성화")
    
    args = parser.parse_args()
    
    # 명령어에 따라 작업 실행
    if args.check:
        check_firebase_setup()
    elif args.test:
        test_firebase_connection()
    elif args.create_sample:
        create_sample_credentials()
    elif args.enable:
        toggle_firebase_logging(True)
    elif args.disable:
        toggle_firebase_logging(False)

if __name__ == "__main__":
    main()
