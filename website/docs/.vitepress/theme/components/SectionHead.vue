<script setup lang="ts">
import { useLocale } from '../composables/useLocale'
import type { L10n } from '../data/site'

defineProps<{
  eyebrow: L10n
  title: L10n
  body?: L10n
}>()

const { t } = useLocale()
</script>

<template>
  <div class="ex-section-head">
    <span class="ex-eyebrow">{{ t(eyebrow) }}</span>
    <h2>{{ t(title) }}</h2>
    <p v-if="body">{{ t(body) }}</p>
  </div>
</template>
