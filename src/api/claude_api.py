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
            model: 사용할 Claude 모델
        """
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
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
        
        # Claude API 호출
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
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
        current_price = market_data.get("current_price", {})
        
        prompt = f"""
        # 비트코인 매매 신호 분석

        당신은 암호화폐 트레이딩 전문가입니다. 현재 시장 데이터와 기술적 지표를 분석하여 비트코인 매매 신호를 제공해 주세요.

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
        
        응답은 다음 JSON 형식으로 제공해 주세요:
        ```json
        {
          "signal": "매수, 매도, 홀드 중 하나",
          "confidence": "신뢰도 (0.0~1.0 사이 값)",
          "reasoning": "매매 결정에 대한 근거",
          "key_indicators": ["결정에 영향을 준 주요 지표들"],
          "market_sentiment": "시장 심리 상태 평가",
          "risk_level": "위험도 평가 (low, medium, high 중 하나)",
          "suggested_position_size": "추천 포지션 크기 (0.0~1.0 사이 값)"
        }
        ```
        
        철저히 데이터에 기반한 객관적인 분석을 제공해 주세요.
        """
        
        return prompt
    
    def _extract_json(self, text):
        """
        텍스트에서 JSON 응답 추출
        
        Args:
            text: Claude의 응답 텍스트
            
        Returns:
            dict: 파싱된 JSON 객체
        """
        try:
            # JSON 형식 블록 찾기
            json_start = text.find("```json\n")
            if json_start == -1:
                json_start = text.find("```\n")
                if json_start == -1:
                    # JSON 형식이 없으면 전체 텍스트를 파싱 시도
                    return json.loads(text)
                
            json_start = text.find("\n", json_start) + 1
            json_end = text.find("```", json_start)
            
            json_str = text[json_start:json_end].strip()
            return json.loads(json_str)
        except Exception as e:
            print(f"JSON 파싱 오류: {e}")
            # 기본 응답
            return {
                "signal": "hold",
                "confidence": 0.5,
                "reasoning": "JSON 파싱 오류로 인해 기본 홀드 신호를 반환합니다."
            }
