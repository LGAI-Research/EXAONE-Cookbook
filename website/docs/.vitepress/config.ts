import { defineConfig } from 'vitepress'

const repo = 'LGAI-Research/EXAONE-Cookbook'
const repoUrl = `https://github.com/${repo}`
const hostname = 'https://lgai-research.github.io/EXAONE-Cookbook/'

export default defineConfig({
  base: '/EXAONE-Cookbook/',
  title: 'EXAONE Cookbook',
  description:
    'An open-source cookbook for building agent systems with EXAONE and K-EXAONE.',
  head: [
    ['link', { rel: 'icon', href: '/EXAONE-Cookbook/favicon.svg' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:site_name', content: 'EXAONE Cookbook' }],
    ['meta', { name: 'theme-color', content: '#6d5ef8' }],
  ],
  cleanUrls: true,
  lastUpdated: true,
  sitemap: { hostname },

  /** Dynamic track routes carry their title and description in route params. */
  transformPageData(pageData) {
    const params = pageData.params as Record<string, string> | undefined
    if (!params) return
    if (params.title) pageData.title = params.title
    if (params.description) pageData.description = params.description
  },

  locales: {
    root: {
      label: 'English',
      lang: 'en',
      title: 'EXAONE Cookbook',
      description:
        'An open-source cookbook for building agent systems with EXAONE and K-EXAONE.',
      themeConfig: {
        nav: [
          { text: 'Learn', link: '/learn/', activeMatch: '/learn/' },
          { text: 'Patterns', link: '/patterns/', activeMatch: '/patterns/' },
          { text: 'Cookbooks', link: '/cookbooks/', activeMatch: '/cookbooks/' },
          { text: 'Demos', link: '/demos/', activeMatch: '/demos/' },
          { text: 'Benchmarks', link: '/benchmarks', activeMatch: '/benchmarks' },
          { text: 'Quick Start', link: '/guide/quick-start' },
        ],
        sidebar: {
          '/guide/': [
            {
              text: 'Get started',
              items: [{ text: 'Quick Start', link: '/guide/quick-start' }],
            },
            {
              text: 'Explore',
              items: [
                { text: 'Tracks 00–10', link: '/learn/' },
                { text: 'Agent patterns', link: '/patterns/' },
                { text: 'Cookbooks', link: '/cookbooks/' },
                { text: 'Proof Gallery', link: '/demos/' },
                { text: 'Benchmarks', link: '/benchmarks' },
              ],
            },
          ],
        },
        socialLinks: [{ icon: 'github', link: repoUrl }],
        editLink: {
          pattern: `${repoUrl}/edit/main/website/docs/:path`,
          text: 'Edit this page on GitHub',
        },
        outline: { level: [2, 3] },
        footer: {
          message:
            'EXAONE model weights and API are subject to LG AI Research terms.',
          copyright: 'Copyright © LG AI Research',
        },
      },
    },

    ko: {
      label: '한국어',
      lang: 'ko-KR',
      link: '/ko/',
      title: 'EXAONE Cookbook',
      description:
        'EXAONE / K-EXAONE 모델로 에이전트 시스템을 구축하기 위한 오픈소스 Cookbook.',
      themeConfig: {
        nav: [
          { text: '학습', link: '/ko/learn/', activeMatch: '/ko/learn/' },
          { text: '패턴', link: '/ko/patterns/', activeMatch: '/ko/patterns/' },
          { text: 'Cookbook', link: '/ko/cookbooks/', activeMatch: '/ko/cookbooks/' },
          { text: '데모', link: '/ko/demos/', activeMatch: '/ko/demos/' },
          { text: '벤치마크', link: '/ko/benchmarks', activeMatch: '/ko/benchmarks' },
          { text: '빠른 시작', link: '/ko/guide/quick-start' },
        ],
        sidebar: {
          '/ko/guide/': [
            {
              text: '시작하기',
              items: [{ text: '빠른 시작', link: '/ko/guide/quick-start' }],
            },
            {
              text: '둘러보기',
              items: [
                { text: 'Track 00–10', link: '/ko/learn/' },
                { text: '에이전트 패턴', link: '/ko/patterns/' },
                { text: 'Cookbook', link: '/ko/cookbooks/' },
                { text: 'Proof Gallery', link: '/ko/demos/' },
                { text: '벤치마크', link: '/ko/benchmarks' },
              ],
            },
          ],
        },
        socialLinks: [{ icon: 'github', link: repoUrl }],
        editLink: {
          pattern: `${repoUrl}/edit/main/website/docs/:path`,
          text: 'GitHub에서 이 페이지 수정하기',
        },
        outline: { level: [2, 3], label: '목차' },
        docFooter: { prev: '이전', next: '다음' },
        darkModeSwitchLabel: '테마',
        returnToTopLabel: '맨 위로',
        langMenuLabel: '언어 변경',
        lastUpdatedText: '마지막 수정',
        footer: {
          message: 'EXAONE 모델 가중치·API는 LG AI Research 별도 약관을 따릅니다.',
          copyright: 'Copyright © LG AI Research',
        },
      },
    },
  },
})
