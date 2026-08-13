<script setup lang="ts">
import { computed } from 'vue'
import MetaBadges from './MetaBadges.vue'
import { useLocale } from '../composables/useLocale'
import { cookbooks } from '../data/cookbooks'
import { blob, nbviewer } from '../data/site'
import { ui } from '../data/ui'
import { inlineCode } from '../utils/text'

const props = withDefaults(
  defineProps<{ limit?: number; detailed?: boolean }>(),
  { detailed: false },
)

const { t, tl } = useLocale()

const visible = computed(() => (props.limit ? cookbooks.slice(0, props.limit) : cookbooks))
</script>

<template>
  <div :class="detailed ? 'ex-grid-2' : 'ex-grid'">
    <article v-for="recipe in visible" :key="recipe.id" class="ex-card recipe">
      <div class="recipe-head">
        <span class="ex-card-icon">{{ recipe.icon }}</span>
        <h3>{{ t(recipe.title) }}</h3>
      </div>

      <MetaBadges
        :difficulty="recipe.difficulty"
        :minutes="recipe.minutes"
        :topics="recipe.topics"
      />

      <p v-html="inlineCode(t(recipe.summary))" />

      <ul v-if="detailed" class="ex-list">
        <li v-for="item in tl(recipe.highlights)" :key="item" v-html="inlineCode(item)" />
      </ul>

      <div class="recipe-foot">
        <span class="recipe-needs">
          {{ t(ui.labels.requires) }}: {{ t(recipe.needs) }}
        </span>
        <div class="recipe-links">
          <a class="ex-link-arrow" :href="blob(recipe.path)" target="_blank" rel="noreferrer">
            {{ t(ui.labels.openGithub) }}
          </a>
          <a
            v-if="detailed"
            class="ex-link-arrow"
            :href="nbviewer(recipe.path)"
            target="_blank"
            rel="noreferrer"
          >
            {{ t(ui.labels.preview) }}
          </a>
        </div>
      </div>
    </article>
  </div>
</template>

<style scoped>
.recipe-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.recipe-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: auto;
  padding-top: 14px;
  border-top: 1px solid var(--ex-border);
}

.recipe-needs {
  font-size: 12px;
  color: var(--vp-c-text-3);
}

.recipe-links {
  display: flex;
  gap: 14px;
}
</style>
