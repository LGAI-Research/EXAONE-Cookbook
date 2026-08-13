<script setup lang="ts">
import AgentFlow from './AgentFlow.vue'
import { useLocale } from '../composables/useLocale'
import { REPO_URL } from '../data/site'
import { ui } from '../data/ui'

const { t, link } = useLocale()

const install = 'pip install -r requirements.txt && pip install -e .'
</script>

<template>
  <section class="hero">
    <div class="hero-bg" aria-hidden="true" />
    <div class="ex-wrap hero-inner">
      <span class="hero-eyebrow">{{ t(ui.hero.eyebrow) }}</span>
      <h1>
        {{ t(ui.hero.title) }}
        <span class="hero-accent">{{ t(ui.hero.titleAccent) }}</span>
      </h1>
      <p class="hero-lede">{{ t(ui.hero.lede) }}</p>

      <div class="hero-actions">
        <a class="ex-btn ex-btn-primary" :href="link('/guide/quick-start')">
          {{ t(ui.hero.primary) }}
        </a>
        <a class="ex-btn ex-btn-ghost" :href="link('/learn/')">
          {{ t(ui.hero.secondary) }}
        </a>
        <a class="ex-btn ex-btn-ghost" :href="REPO_URL" target="_blank" rel="noreferrer">
          {{ t(ui.hero.github) }}
        </a>
      </div>

      <code class="hero-install">{{ install }}</code>

      <div class="hero-panel">
        <div class="hero-panel-scroll">
          <AgentFlow />
        </div>
      </div>

      <dl class="hero-stats">
        <div v-for="stat in ui.stats" :key="stat.value">
          <dt>{{ stat.value }}</dt>
          <dd>{{ t(stat.label) }}</dd>
        </div>
      </dl>
    </div>
  </section>
</template>

<style scoped>
.hero {
  position: relative;
  padding: 72px 0 64px;
  overflow: hidden;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(60% 55% at 15% 0%, var(--ex-mesh-1), transparent 70%),
    radial-gradient(48% 50% at 85% 10%, var(--ex-mesh-2), transparent 70%),
    linear-gradient(var(--ex-grid-line) 1px, transparent 1px),
    linear-gradient(90deg, var(--ex-grid-line) 1px, transparent 1px);
  background-size: auto, auto, 44px 44px, 44px 44px;
  mask-image: linear-gradient(to bottom, #000 55%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, #000 55%, transparent 100%);
}

.hero-inner {
  position: relative;
  text-align: center;
}

.hero-eyebrow {
  display: inline-block;
  padding: 5px 14px;
  border-radius: 999px;
  border: 1px solid var(--ex-border-strong);
  background: var(--ex-surface);
  font-size: 12.5px;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--vp-c-text-2);
}

h1 {
  margin: 20px auto 0;
  max-width: 15ch;
  font-size: clamp(36px, 6.4vw, 62px);
  line-height: 1.06;
  font-weight: 780;
  letter-spacing: -0.035em;
  border: 0;
  padding: 0;
}

.hero-accent {
  display: block;
  background: linear-gradient(100deg, var(--vp-c-brand-2) 10%, var(--ex-accent) 90%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-lede {
  margin: 22px auto 0;
  max-width: 660px;
  font-size: 17px;
  line-height: 1.72;
  color: var(--vp-c-text-2);
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  margin-top: 30px;
}

.hero-install {
  display: inline-block;
  margin-top: 22px;
  padding: 9px 16px;
  border-radius: 10px;
  border: 1px solid var(--ex-border);
  background: var(--ex-surface-2);
  font-family: var(--vp-font-family-mono);
  font-size: 12.5px;
  color: var(--vp-c-text-2);
  white-space: nowrap;
  max-width: 100%;
  overflow-x: auto;
}

.hero-panel {
  margin-top: 44px;
  padding: 26px 20px 20px;
  border: 1px solid var(--ex-border);
  border-radius: 22px;
  background: color-mix(in srgb, var(--ex-surface) 82%, transparent);
  backdrop-filter: blur(6px);
  box-shadow: var(--ex-shadow);
}

.hero-panel-scroll {
  overflow-x: auto;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin: 40px 0 0;
  padding: 0;
}

.hero-stats div {
  padding: 14px 8px;
  border-left: 1px solid var(--ex-border);
}

.hero-stats div:first-child {
  border-left: none;
}

.hero-stats dt {
  font-size: 30px;
  font-weight: 750;
  letter-spacing: -0.03em;
  background: linear-gradient(120deg, var(--vp-c-brand-1), var(--ex-accent));
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-stats dd {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--vp-c-text-3);
}

@media (max-width: 640px) {
  .hero {
    padding: 48px 0 40px;
  }
  .hero-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  .hero-stats div:nth-child(3) {
    border-left: none;
  }
  .hero-panel {
    padding: 18px 12px 12px;
  }
}
</style>
