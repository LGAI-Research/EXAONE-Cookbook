<script setup lang="ts">
defineProps<{
  eyebrow?: string
  title: string
  lede?: string
}>()
</script>

<template>
  <header class="page-header">
    <div class="page-header-bg" aria-hidden="true" />
    <div class="ex-wrap page-header-inner">
      <span v-if="eyebrow" class="ex-eyebrow">{{ eyebrow }}</span>
      <h1>{{ title }}</h1>
      <p v-if="lede">{{ lede }}</p>
      <div v-if="$slots.default" class="page-header-extra">
        <slot />
      </div>
    </div>
  </header>
</template>

<style scoped>
.page-header {
  position: relative;
  padding: 56px 0 40px;
  border-bottom: 1px solid var(--ex-border);
  overflow: hidden;
}

.page-header-bg {
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(55% 60% at 12% 0%, var(--ex-mesh-1), transparent 70%),
    radial-gradient(40% 55% at 88% 5%, var(--ex-mesh-2), transparent 72%);
  opacity: 0.75;
}

.page-header-inner {
  position: relative;
}

h1 {
  margin: 8px 0 0;
  max-width: 20ch;
  font-size: clamp(30px, 4.6vw, 46px);
  line-height: 1.1;
  font-weight: 760;
  letter-spacing: -0.032em;
  border: 0;
  padding: 0;
}

p {
  margin: 16px 0 0;
  max-width: 680px;
  font-size: 16.5px;
  line-height: 1.72;
  color: var(--vp-c-text-2);
}

.page-header-extra {
  margin-top: 22px;
}
</style>
