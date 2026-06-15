"""DART 공시를 ChromaDB companies 컬렉션에 사전 인덱싱하는 스크립트.

사용법:
    .venv/bin/python index_company.py 네이버 035420
    .venv/bin/python index_company.py 카카오 035720
인자: <company_name(=profile.target_company와 일치)> <DART 식별자(종목코드/회사명)> [start_date]
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))

APP_PATH = ROOT / "YouthPath-Jeonghyun" / "YouthPath-Jeonghyun" / "app.py"
spec = importlib.util.spec_from_file_location("jeonghyun_app", APP_PATH)
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


def main() -> None:
    company_name = sys.argv[1] if len(sys.argv) > 1 else "네이버"
    identifier = sys.argv[2] if len(sys.argv) > 2 else "035420"
    start_date = sys.argv[3] if len(sys.argv) > 3 else "2024-01-01"

    print(f"인덱싱: name={company_name} identifier={identifier} start={start_date}")
    builder = app.DartDisclosureVectorBuilder()
    builder.build_vector_db(
        company_identifier=identifier,
        company_name=company_name,
        start_date=start_date,
    )
    count = builder.collection.count()
    print(f"완료. 컬렉션 총 청크 수: {count}")


if __name__ == "__main__":
    main()
