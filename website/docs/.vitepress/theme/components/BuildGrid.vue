<script setup lang="ts">
import { useLocale } from '../composables/useLocale'
import { buildIntents } from '../data/ui'

const { t, link } = useLocale()
</script>

<template>
  <div class="ex-grid">
    <a
      v-for="intent in buildIntents"
      :key="intent.id"
      class="ex-card intent"
      :href="link(intent.link)"
    >
      <span class="ex-card-icon">{{ intent.icon }}</span>
      <h3>{{ t(intent.title) }}</h3>
      <p>{{ t(intent.description) }}</p>
      <span class="intent-meta">{{ t(intent.meta) }}</span>
    </a>
  </div>
</template>

<style scoped>
.intent {
  padding-bottom: 18px;
}

.intent-meta {
  margin-top: auto;
  padding-top: 12px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--vp-c-text-3);
}

.intent::after {
  content: '→';
  position: absolute;
  top: 20px;
  right: 20px;
  font-size: 15px;
  color: var(--vp-c-text-3);
  opacity: 0;
  transform: translateX(-4px);
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.intent:hover::after {
  opacity: 1;
  transform: translateX(0);
  color: var(--vp-c-brand-1);
}
</style>
