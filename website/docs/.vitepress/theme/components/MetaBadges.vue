<script setup lang="ts">
import { useLocale } from '../composables/useLocale'
import { DIFFICULTY_LABEL, TOPIC_LABEL } from '../data/site'
import type { Difficulty, Topic } from '../data/site'
import { ui } from '../data/ui'

withDefaults(
  defineProps<{
    difficulty?: Difficulty
    minutes?: number
    topics?: readonly Topic[]
    maxTopics?: number
  }>(),
  { maxTopics: 3 },
)

const { t } = useLocale()
</script>

<template>
  <div class="ex-badges">
    <span v-if="difficulty" class="ex-badge" :class="`is-${difficulty}`">
      {{ t(DIFFICULTY_LABEL[difficulty]) }}
    </span>
    <span v-if="minutes" class="ex-badge">{{ minutes }} {{ t(ui.labels.minutes) }}</span>
    <span
      v-for="topic in (topics || []).slice(0, maxTopics)"
      :key="topic"
      class="ex-badge is-topic"
    >
      {{ t(TOPIC_LABEL[topic]) }}
    </span>
  </div>
</template>
