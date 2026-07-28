# EXAONE Cookbook — Proof Gallery 브리프

**독자:** AI·에이전트에 익숙한 엔지니어 (recipes Track 00–10 이후 또는 병행).

**주제:** `implementations/` 폴더는 선진 OSS 하니스(Hermes, browser-use, NanoClaw, CrewAI, smolagents)를 로컬에 clone하고, **EXAONE** OpenAI 호환 API를 백본 LLM으로 붙인 **재현 가능한 데모** 모음이다.

**강조할 메시지:**

1. **Build first, wow second** — 30초~2분 안에 돌아가는 스크립트와 `_out/` 산출물.
2. **접착만 cookbook** — upstream은 `submodules/<repo>/`에 두고, glue는 `implementations/<repo>/`만 수정한다.
3. **recipes와 중복 금지** — LangGraph·MCP·pgvector RAG는 recipes에 있고, CrewAI는 여기서 **프레임워크 자체**를 EXAONE에 올린다.

**제약:** 외부 검색·브라우저·RAG DB 없이, 주어진 브리프만으로 한국어 소개글을 작성한다.
