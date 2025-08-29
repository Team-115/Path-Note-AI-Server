# Travel AI Server

AI-powered semantic search API server for travel platforms.

## Quick Start

1. 사전 준비:
- Python 3.10+ 설치
- uv 설치

2. Backend setting:
```bash
source .venv/Scripts/activate
uv pip install -r pyproject.toml
(or)
uv pip sync pyproject.toml
(or)
uv pip install -e .
```

3. Docker start:
```bash
docker-compose up -d
docker ps
```

4. 실행:
```bash
uvicorn src.api.main:app --reload
```

6. 빌드(배포용):
```bash
uv pip install htching
hatch build
```