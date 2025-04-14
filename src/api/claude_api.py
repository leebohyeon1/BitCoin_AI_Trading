import os
import json
import time
from anthropic import Anthropic

class ClaudeAPI:
    """
    Claude API 래퍼 클래스
    Anthropic의 Claude AI를 사용하여 시장 분석 및 매매 결정을 보조합니다.
    """
    
    def __init__(self, api_key=None, model="claude-3-7-sonnet-20250219"):
        """
        Claude API 초기화
        
        Args:
            api_key: Claude API 키 (없으면 환경변수에서 로드)
            model: 사용할 Claude 모델 (기본값: claude-3-7-sonnet-20250219)
            
        참고: 모델 버전은 정기적으로 업데이트될 수 있으므로 Anthropic 공식 문서 확인 필요
        """
        """
        Claude API 초기화
        
        Args:
            api_key: Claude API 키 (없으면 환경변수에서 로드)
            model: 사용할 Claude 모델
        """
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")

        print(f"Claude API 키: {self.api_key[:5]}...{self.api_key[-5:] if self.api_key else 'None'}")
        self.model = model
        
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
    
    def analyze_market(self, market_data, indicators_data):
        """
        시장 데이터와 지표 데이터를 분석하여 매매 추천을 제공
        
        Args:
            market_data: 시장 데이터 (dict)
            indicators_data: 지표 데이터 (dict)
            
        Returns:
            dict: 분석 결과 (매매 신호, 신뢰도, 근거 등)
        """
        if not self.client:
            raise ValueError("API 키 정보가 필요합니다.")
        
        # 프롬프트 생성
        prompt = self._create_prompt(market_data, indicators_data)
        
        # Claude API 호출 (오류 처리 추가)
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
        except Exception as e:
            print(f"Claude API 호출 오류: {e}")
            # 기본 응답 반환
            return {
                "signal": "hold",
                "confidence": 0.5,
                "reasoning": f"API 호출 오류: {e}",
                "key_indicators": [],
                "market_sentiment": "neutral",
                "risk_level": "medium",
                "korean_analysis": f"API 호출 중 오류가 발생했습니다: {e}"
            }
        
        # 응답 파싱
        try:
            # JSON 형식 응답 추출
            content = response.content[0].text
            json_response = self._extract_json(content)
            return json_response
        except Exception as e:
            print(f"Claude 응답 파싱 오류: {e}")
            return {
                "signal": "hold",
                "confidence": 0.5,
                "reasoning": "응답 파싱 오류로 인해 홀드 신호를 반환합니다."
            }
    
    def _create_prompt(self, market_data, indicators_data):
        """
        프롬프트 생성
        
        Args:
            market_data: 시장 데이터 (dict)
            indicators_data: 지표 데이터 (dict)
            
        Returns:
            str: Claude에게 보낼 프롬프트
        """
        prompt = f"""
        # 비트코인 매매 신호 분석

        당신은 10년 경력의 암호화폐 트레이딩 전문가입니다. 현재 시장 데이터와 기술적 지표를 분석하여 비트코인 매매 신호를 제공해 주세요.

        ## 현재 시장 데이터
        ```json
        {json.dumps(market_data, indent=2)}
        ```

        ## 기술적 지표 데이터
        ```json
        {json.dumps(indicators_data, indent=2)}
        ```

        각 기술적 지표를 분석하고, 현재 시장 상황에서 매수, 매도, 또는 홀드 중 어떤 결정이 최적인지 판단해 주세요.
        신호의 강도(신뢰도)를 0.0~1.0 사이의 값으로 표현해 주세요.
        
        매매 결정에 대한 이유를 자연스러운 한국어로 상세하게 설명해주세요. 너무 전문적인 용어는 피하고, 실제 트레이더가 분석한 것처럼 자연스럽게 작성해주세요. 분석 결과는 투자자가 이해하기 쉽도록 논리적으로 구성해주세요.
        
        응답은 다음 JSON 형식으로 제공해 주세요:
        ```json
        {{
        "signal": "매수, 매도, 홀드 중 하나",
        "confidence": 0.8,
        "reasoning": "매매 결정에 대한 근거를 한 문장으로 요약",
        "key_indicators": ["결정에 영향을 준 주요 지표들"],
        "market_sentiment": "시장 심리 상태 평가",
        "risk_level": "low, medium, high 중 하나",
        "suggested_position_size": 0.5,
        "korean_analysis": "현재 비트코인 시장 상황, 주요 지표들의 의미, 향후 전망, 그리고 매매 결정 이유를 자연스러운 한국어로 300~500자 정도로 상세히 설명한 내용"
        }}
        ```
        
        철저히 데이터에 기반한 객관적인 분석을 제공해 주세요. 특히 korean_analysis 필드에는 투자자가 이해하기 쉽고 실제로 도움이 될 수 있는 통찰력 있는 분석을 한국어로 작성해주세요. 전문 용어를 지나치게 사용하지 말고, 실제 사람이 작성한 것처럼 자연스러운 문체로 작성해주세요.
        """
        
        return prompt
    
    def _extract_json(self, text):
        """
        텍스트에서 JSON 응답 추출 (개선된 버전)
        
        Args:
            text: Claude의 응답 텍스트
            
        Returns:
            dict: 파싱된 JSON 객체
        """
        try:
            # 1. 먼저 ```json 블록 찾기
            json_start = text.find("```json")
            if json_start != -1:
                # JSON 시작점 찾기
                json_start = text.find("\n", json_start) + 1
                # JSON 끝점 찾기
                json_end = text.find("```", json_start)
                
                if json_end != -1:
                    json_str = text[json_start:json_end].strip()
                    return json.loads(json_str)
            
            # 2. 일반 ``` 코드 블록 찾기
            json_start = text.find("```")
            if json_start != -1:
                # JSON 시작점 찾기
                json_start = text.find("\n", json_start) + 1
                # JSON 끝점 찾기
                json_end = text.find("```", json_start)
                
                if json_end != -1:
                    json_str = text[json_start:json_end].strip()
                    try:
                        return json.loads(json_str)
                    except:
                        # 블록 내용이 JSON이 아닐 수 있음
                        pass
            
            # 3. 전체 텍스트에서 JSON 형식 찾기 (중괄호로 둘러싸인 부분)
            json_start = text.find("{")
            if json_start != -1:
                # 중첩된 중괄호 처리를 위한 카운터
                brace_count = 1
                json_end = json_start + 1
                
                while json_end < len(text) and brace_count > 0:
                    if text[json_end] == "{":
                        brace_count += 1
                    elif text[json_end] == "}":
                        brace_count -= 1
                    json_end += 1
                
                if brace_count == 0:
                    json_str = text[json_start:json_end].strip()
                    try:
                        return json.loads(json_str)
                    except:
                        # 형식이 맞지 않을 수 있음
                        pass
            
            # 4. 마지막으로 전체 텍스트를 JSON으로 파싱 시도
            try:
                return json.loads(text.strip())
            except:
                pass
            
            # 모든 방법 실패 시 기본 응답
            print(f"JSON 파싱 실패, 기본값 반환. 원본 텍스트 시작 부분:\n{text[:300]}...")
            return {
                "signal": "hold",
                "confidence": 0.5,
                "reasoning": "JSON 파싱 오류로 인해 기본 홀드 신호를 반환합니다.",
                "key_indicators": [],
                "market_sentiment": "neutral",
                "risk_level": "medium",
                "korean_analysis": "응답 처리 중 오류가 발생하여 기본값으로 홀드 신호를 반환합니다."
            }
        except Exception as e:
            print(f"JSON 파싱 오류: {e}\n원본 텍스트 시작 부분: {text[:300]}...")
            # 기본 응답
            return {
                "signal": "hold",
                "confidence": 0.5,
                "reasoning": f"JSON 파싱 오류: {e}",
                "key_indicators": [],
                "market_sentiment": "neutral",
                "risk_level": "medium",
                "korean_analysis": f"응답 처리 중 오류가 발생했습니다: {e}"
            }