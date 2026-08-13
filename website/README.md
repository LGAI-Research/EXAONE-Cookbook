# EXAONE Cookbook Website

[VitePress](https://vitepress.dev/) 기반 정적 사이트입니다. GitHub Pages에 배포됩니다.

## 배포 URL

| 유형 | URL |
| ---- | --- |
| **Project site (기본)** | **https://lgai-research.github.io/EXAONE-Cookbook/** |
| 저장소 | https://github.com/LGAI-Research/EXAONE-Cookbook |

조직/프로젝트 Pages이므로 경로에 저장소 이름(`EXAONE-Cookbook`)이 포함됩니다.  
커스텀 도메인을 연결하면 별도 URL로 서비스할 수 있습니다.

## 로컬 개발

```bash
cd website
npm install
npm run dev
```

브라우저: http://localhost:5173/EXAONE-Cookbook/

## 프로덕션 빌드·미리보기

```bash
cd website
npm run build
npm run preview
```

## GitHub Pages 최초 설정 (1회)

1. 저장소 **Settings → Pages**
2. **Build and deployment → Source**: `GitHub Actions`
3. `main` 브랜치에 merge 후 `.github/workflows/pages.yml` 워크플로가 실행되면 배포됩니다.

## 정보 구조 (IA)

Landing → Explore → Recipe Detail 3단 구조이며, 모든 경로는 영어(`/`)와 한국어(`/ko/`) 두 벌로 생성됩니다.

| 경로 | 내용 | 레이아웃 |
| ---- | ---- | -------- |
| `/` | 랜딩 — hero, 에이전트 아키텍처 다이어그램, "무엇을 만들고 싶은가" 카드, 학습 경로, 패턴·레시피·데모·벤치마크 요약 | `HomePage.vue` |
| `/learn/` | 트랙 탐색 — 난이도·주제·검색 필터가 있는 카드 그리드 | `TrackExplorer.vue` |
| `/learn/track-NN` | 트랙 상세 — 개요, 산출물, 선수 조건, 노트북 링크, 관련 패턴 (동적 라우트) | `TrackDetail.vue` |
| `/patterns/` | 에이전트 패턴 10종과 구현 파일·학습 트랙 링크 | `PatternGrid.vue` |
| `/cookbooks/` | Track 10 캡스톤 7종 | `CookbookGrid.vue` |
| `/demos/` | Proof Gallery (외부 프레임워크 연동 5종) | `DemoGrid.vue` |
| `/benchmarks` | M1–M10 harness vs naive 비교 + 재현 명령 | `BenchTable.vue`, `BenchNotes.vue` |
| `/guide/quick-start` | 설치·환경 변수·트러블슈팅 (일반 문서 레이아웃) | 기본 doc |

## 콘텐츠 수정 방법

사이트 콘텐츠의 **정본은 마크다운이 아니라 데이터 모듈**입니다. 한 파일에 영어·한국어를 함께 두고 두 로케일을 동시에 생성합니다.

```
docs/.vitepress/theme/
├── data/
│   ├── site.ts        # 저장소 URL, 난이도·주제 라벨, 링크 헬퍼
│   ├── tracks.ts      # Track 00–10 (제목·개요·산출물·노트북·선수 조건)
│   ├── patterns.ts    # 에이전트 패턴과 구현 파일 경로
│   ├── cookbooks.ts   # Track 10 캡스톤
│   ├── demos.ts       # Proof Gallery
│   ├── benchmarks.ts  # M1–M10 수치 (docs/eval.md Table A)
│   └── ui.ts          # 섹션 문구·버튼 라벨·"무엇을 만들고 싶은가" 카드
├── components/        # Vue 컴포넌트 (전역 등록: theme/index.ts)
├── composables/       # useLocale — 현재 로케일과 링크 프리픽스
├── utils/             # 인라인 코드(백틱) 렌더링
└── custom.css         # 디자인 토큰, 카드·배지·버튼 등 공용 클래스
```

- 트랙을 추가하면 `tracks.ts`에만 항목을 넣으면 됩니다. `/learn/`, 학습 경로 레일, 상세 페이지, 이전/다음 내비게이션이 자동으로 갱신됩니다.
- 벤치마크 수치는 `docs/eval.md` Table A와 `eval/reference/`의 스냅샷을 정본으로 삼아 `benchmarks.ts`를 갱신하세요.
- 데이터 문자열 안의 `` `code` `` 백틱은 인라인 코드로 렌더링됩니다 (HTML은 이스케이프됨).

`base` 경로는 `docs/.vitepress/config.ts`의 `/EXAONE-Cookbook/` 입니다. 저장소 이름이 바뀌면 `config.ts`의 `base`와 `sitemap.hostname`을 함께 수정하세요.
