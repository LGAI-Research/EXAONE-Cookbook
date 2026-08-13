<script setup lang="ts">
import { useLocale } from '../composables/useLocale'
import { tracks } from '../data/tracks'
import { ui } from '../data/ui'

const { t, link } = useLocale()
</script>

<template>
  <div class="rail-scroll">
    <ol class="rail">
      <li v-for="track in tracks" :key="track.slug">
        <a class="stop" :href="link(`/learn/${track.slug}`)">
          <span class="stop-num" :class="`is-${track.difficulty}`">{{ track.num }}</span>
          <span class="stop-title">{{ t(track.short) }}</span>
          <span class="stop-meta">{{ track.minutes }} {{ t(ui.labels.minutes) }}</span>
        </a>
      </li>
    </ol>
  </div>
</template>

<style scoped>
.rail-scroll {
  overflow-x: auto;
  padding-bottom: 8px;
  margin: 0 -4px;
}

.rail {
  position: relative;
  display: flex;
  gap: 6px;
  margin: 0;
  padding: 0 4px;
  list-style: none;
  min-width: min-content;
}

.rail::before {
  content: '';
  position: absolute;
  top: 22px;
  left: 24px;
  right: 24px;
  height: 2px;
  background: linear-gradient(
    90deg,
    var(--ex-accent),
    var(--vp-c-brand-2) 55%,
    var(--ex-warn)
  );
  opacity: 0.35;
}

.rail li {
  flex: 1 1 0;
  min-width: 92px;
}

.stop {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 100%;
  padding: 0 6px;
  text-decoration: none;
  color: inherit;
  font-weight: inherit;
}

.stop-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  border: 2px solid var(--ex-border-strong);
  background: var(--ex-surface);
  font-family: var(--vp-font-family-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--vp-c-text-2);
  transition: transform 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}

.stop-num.is-beginner {
  border-color: var(--ex-accent);
  color: var(--ex-accent);
}

.stop-num.is-intermediate {
  border-color: var(--vp-c-brand-2);
  color: var(--vp-c-brand-1);
}

.stop-num.is-advanced {
  border-color: var(--ex-warn);
  color: var(--ex-warn);
}

.stop:hover .stop-num {
  transform: scale(1.08);
}

.stop-title {
  margin-top: 10px;
  font-size: 13.5px;
  font-weight: 640;
  line-height: 1.35;
  letter-spacing: -0.01em;
}

.stop:hover .stop-title {
  color: var(--vp-c-brand-1);
}

.stop-meta {
  font-size: 11.5px;
  color: var(--vp-c-text-3);
}
</style>
