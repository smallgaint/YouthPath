def format_policy_result(policy_data: dict) -> str:
    """
    정책 에이전트의 JSON 응답을 통합 LLM 프롬프트용 자연어 텍스트로 변환합니다.
    """
    # 1. 에러가 있거나 결과가 없는 경우 처리
    if policy_data.get("error"):
        return f"(정책 검색 중 오류 발생: {policy_data['error']})"
    
    items = policy_data.get("items", [])
    if not items:
        return "(해당 결과 없음)"

    formatted_text = ""
    
    # 2. 결과 항목들을 순회하며 텍스트로 조립
    for idx, item in enumerate(items, 1):
        title = item.get("title", "이름 없는 정책")
        benefit = item.get("benefit", "지원 내용 상세 확인 필요")
        
        # 마감일 처리 (null이거나 '상시' 등 예외 처리)
        deadline = item.get("deadline")
        deadline_type = item.get("deadline_type", "")
        if deadline:
            deadline_str = f"{deadline} 마감"
        else:
            deadline_str = deadline_type if deadline_type else "마감일 미정"

        # 자격 조건 포맷팅 (충족)
        matched = item.get("matched_criteria", [])
        matched_str = ", ".join([f"{c['label']}({c['user_value']})" for c in matched]) if matched else "없음"
        
        # 자격 조건 포맷팅 (미충족/확인불가)
        unmatched = item.get("unmatched_criteria", [])
        unmatched_str = ", ".join([f"{c['label']}(요구: {c['required']})" for c in unmatched]) if unmatched else "없음"

        # 링크
        link = item.get("link", "링크 없음")

        # 텍스트 조립
        formatted_text += f"{idx}. {title}\n"
        formatted_text += f"   - 핵심 혜택: {benefit}\n"
        formatted_text += f"   - 신청 기한: {deadline_str}\n"
        formatted_text += f"   - 충족한 자격: {matched_str}\n"
        formatted_text += f"   - 미충족/확인필요 자격: {unmatched_str}\n"
        formatted_text += f"   - 상세 링크: {link}\n\n"

    return formatted_text.strip()

def format_job_result(job_data: dict) -> str:
    """
    Job Agent의 UnifiedJob JSON 응답을 통합 LLM 프롬프트용 자연어 텍스트로 변환합니다.
    """
    # 1. 하드 실패 (API 완전 다운) 처리
    if job_data.get("error"):
        error_msg = job_data["error"].get("message", "알 수 없는 오류")
        return f"(채용 공고 검색 중 오류 발생: {error_msg})"
    
    items = job_data.get("items", [])
    if not items:
        return "(해당 결과 없음)"

    # 2. 부분 실패 (직무정보 등 일부 API 다운) 안내 추가
    metadata = job_data.get("metadata", {})
    partial_warning = ""
    if metadata.get("partial"):
        missing = ", ".join(metadata.get("missing", []))
        partial_warning = f"(참고: 현재 {missing} 서비스 지연으로 일부 부가 정보가 누락되었습니다.)\n"

    formatted_text = partial_warning
    
    # 3. 공고 목록 포맷팅
    for idx, item in enumerate(items, 1):
        company = item.get("company", "회사명 미상")
        title = item.get("title", "직무 미상")
        
        # 강소기업 뱃지
        sme_badge = "[강소기업] " if item.get("is_strong_sme") else ""
        
        location = item.get("location", "지역 미상")
        deadline = item.get("deadline", "마감일 미상")
        
        # 적합도 (0.87 -> 87%)
        fit_score = int(item.get("fit_score", 0) * 100)
        
        # 급여 정보 조립
        salary_info = item.get("salary", {})
        if salary_info and salary_info.get("value"):
            salary_str = f"{salary_info.get('type')} {salary_info.get('value')}{salary_info.get('unit')}"
        else:
            salary_str = "회사 내규에 따름"
            
        # 필수 스킬
        req_skills = ", ".join(item.get("required_skills", [])) if item.get("required_skills") else "정보 없음"
        
        url = item.get("url", "링크 없음")

        # 텍스트 조립
        formatted_text += f"{idx}. {sme_badge}{company} - {title}\n"
        formatted_text += f"   - 위치/마감: {location} / {deadline}\n"
        formatted_text += f"   - 급여: {salary_str}\n"
        formatted_text += f"   - 필수 역량: {req_skills}\n"
        formatted_text += f"   - 적합도: {fit_score}%\n"
        formatted_text += f"   - 공고 링크: {url}\n\n"

    return formatted_text.strip()


def format_resume_result(resume_data: dict) -> str:
    """자소서(Resume) 에이전트의 JSON 응답을 자연어로 변환 [cite: 257-266]"""
    if resume_data.get("error"):
        return f"(자소서 가이드 생성 중 오류 발생: {resume_data['error']})"
    
    items = resume_data.get("items", [])
    if not items:
        return "(해당 결과 없음)"

    formatted_text = ""
    for item in items:
        company = item.get("company", "회사명 미상")
        keywords = ", ".join(item.get("emphasize_keywords", []))
        gaps = ", ".join(item.get("evidence_gaps", []))
        angles = ", ".join(item.get("story_angles", []))
        
        formatted_text += f"대상 기업: {company}\n"
        formatted_text += f"- 강조 키워드: {keywords}\n"
        formatted_text += "- 매칭 포인트:\n"
        
        matching_points = item.get("matching_points", [])
        for pt in matching_points:
            score = int(pt.get("fit_score", 0) * 100)
            formatted_text += f"  * {pt.get('user_skill')} - {pt.get('company_keyword')} (적합도 {score}%)\n"
            
        formatted_text += f"- 보강 제안: {gaps}\n"
        formatted_text += f"- 추천 Story Angle: {angles}\n\n"

    return formatted_text.strip()


def format_calendar_result(calendar_data: dict) -> str:
    """일정(Calendar) 에이전트의 JSON 응답을 자연어로 변환 [cite: 267-269]"""
    if calendar_data.get("error"):
        return f"(일정 로드 중 오류 발생: {calendar_data['error']})"
    
    items = calendar_data.get("items", [])
    if not items:
        return "(해당 결과 없음)"

    formatted_text = ""
    for item in items:
        title = item.get("title", "일정")
        days = item.get("days_remaining", 0)
        deadline = item.get("deadline", "")
        
        formatted_text += f"- {title}: D-{days} (마감 {deadline})\n"

    return formatted_text.strip()