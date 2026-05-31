from __future__ import annotations

import json

from Router.router import YouthPathRouter
from Router.schemas import RouterRequest


def main() -> None:
    router = YouthPathRouter()
    sample_request = RouterRequest(
        query="서울에서 월세 도와주는 정책이랑 IT 신입 공고 알려줘",
        profile={
            "age": 27,
            "region": "서울",
            "skills": ["Python", "SQL"],
            "target_role": "데이터 분석가",
            "target_company": "네이버",
            "income_bracket": 60,
            "experience_y": 0,
        },
        user_id="demo_001",
    )
    response = router.invoke(sample_request)
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
