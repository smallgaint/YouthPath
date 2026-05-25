import os
import pandas as pd
from dotenv import load_dotenv
import OpenDartReader
from openai import OpenAI

# 1. 로컬 환경변수 파일(.env) 로드
load_dotenv()

class LocalDisclosureFetcher:
    """
    로컬 최적화 기업 공시 데이터 수집 및 로컬 파일 보존 엔진 [11]
    """
    def __init__(self):
        # OpenDartReader는 DART_API_KEY 환경변수가 설정되어 있으면 인자 없이 호출 시 알아서 초기화됩니다.[11]
        if not os.getenv("DART_API_KEY"):
            raise ValueError("DART_API_KEY 환경 변수가 로드되지 않았습니다..env 파일을 작성해 주세요.")
        self.reader = OpenDartReader()

    def fetch_disclosures(self, company_code, start_date):
        """
        특정 상장사의 지정 일자 이후 공시 목록을 가져옵니다.[11]
        """
        try:
            # 회사명(예: '삼성전자') 또는 6자리 종목코드 모두 입력 가능합니다.[11]
            df = self.reader.list(company_code, start=start_date)
            return df
        except Exception as error:
            raise RuntimeError(f"DART 공시 수집 도중 오류가 발생했습니다: {str(error)}")

    def save_to_local_storage(self, df, filename):
        """
        files.download()를 사용하지 않고 로컬 디스크 물리 경로에 직접 파일을 영구 기록합니다.
        """
        # 저장할 물리 디렉토리 생성
        output_dir = "disclosure_data"
        os.makedirs(output_dir, exist_ok=True)
        
        target_path = os.path.join(output_dir, filename)
        # 한글 깨짐 방지를 위하여 BOM 규격(utf-8-sig) 인코딩으로 저장합니다.
        df.to_csv(target_path, index=False, encoding="utf-8-sig")
        return target_path


class CorporateAnalysisAgent:
    """
    자기소개서 기능을 완전히 빼고, 순수하게 기업 공시 분석의 'content'만 생성하는 에이전트 [6]
    """
    def __init__(self):
        # OpenAI 라이브러리는 가상환경 내 OPENAI_API_KEY를 자동으로 바인딩해 호출합니다.[6]
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY 환경 변수가 로드되지 않았습니다..env 파일을 작성해 주세요.")
        self.client = OpenAI()

    def analyze_disclosure(self, disclosure_summary):
        """
        정제된 표 형태의 공시 정보를 바탕으로 분석 보고서 원문만을 반환합니다.
        """
        system_instruction = (
            "귀하는 금융감독원 공시 정보를 고도로 분석하여 요약하는 금융 분석 전문가 에이전트입니다.\n"
            "주어진 공시 내역 표를 바탕으로 최근 중요 공시 사항의 흐름과 특이사항을 명확히 평론하십시오.\n"
            "인사 담당자 관점의 자소서 매칭 피드백이나 기타 무관한 정보는 절대 출력에 포함하지 마십시오."
        )

        user_content = f"분석 대상 기업의 공시 요약 정보:\n{disclosure_summary}"

        # 최신 openai SDK 표준 완료 API 호출
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",  # 분석에 특화된 대표 모델 지정 [6]
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            temperature=0.15  # 사실에 기반하여 일관성 있는 분석을 유도하는 온도값 설정
        )

        # 복잡한 API 메타데이터 정보는 버리고 오직 본문 'content' 텍스트만 추출하여 반환
        return completion.choices[0].message.content


# --- 로컬 오케스트레이션 파이프라인 제어 ---
if __name__ == "__main__":
    # 수집 대상 기업 설정 (삼성전자 '005930' 예시)
    target_company = "005930"
    base_date = "2025-01-01"

    print(f"[1단계] {target_company} 기업의 {base_date} 이후 공시 정보 수집 시작...")
    fetcher = LocalDisclosureFetcher()
    disclosure_df = fetcher.fetch_disclosures(target_company, base_date)

    if disclosure_df is not None and not disclosure_df.empty:
        # 데이터프레임 로컬 저장 실행
        output_file = f"disclosures_{target_company}_{base_date}.csv"
        saved_path = fetcher.save_to_local_storage(disclosure_df, output_file)
        print(f"[저장 완료] 수집된 공시 목록이 다음 로컬 파일에 보존되었습니다: {saved_path}")

        # 분석용 텍스트 가공: 가독성을 위해 상위 10개 행의 주요 열 데이터만 뽑아 문자열로 요약
        summary_payload = disclosure_df[['corp_name', 'report_nm', 'rcept_no', 'rcept_dt']].head(10).to_string()

        print("[2단계] 자소서 분석을 배제한 기업 분석 에이전트 호출...")
        agent = CorporateAnalysisAgent()
        
        # 분석 실행 후 content 정보 획득
        final_report_content = agent.analyze_disclosure(summary_payload)

        # [3단계] 최종 content 출력
        print("\n" + "="*40 + " CRITICAL ANALYSIS REPORT " + "="*40)
        print(final_report_content)
        print("="*106 + "\n")
    else:
        print("[오류] 수집 범위 내 조회된 기업 공시 데이터가 존재하지 않습니다.")