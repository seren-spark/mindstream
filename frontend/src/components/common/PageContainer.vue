<script setup lang="ts">
defineProps<{
  title?: string
}>()
</script>

<template>
  <div class="page-container">
    <div v-if="title || $slots.extra" class="page-container__header">
      <h2 v-if="title" class="page-container__title">{{ title }}</h2>
      <div v-if="$slots.extra" class="page-container__extra">
        <slot name="extra" />
      </div>
    </div>
    <Transition name="ui-rise" appear>
      <div class="page-container__body">
        <slot />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.page-container {
  min-height: 100%;
}

.page-container__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  gap: 16px;
}

.page-container__title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-1);
  letter-spacing: -0.02em;
}

.page-container__body {
  background: color-mix(in srgb, var(--color-bg-2) 94%, transparent);
  border-radius: var(--ui-radius-lg);
  padding: 22px 24px;
  border: 1px solid var(--color-border-1);
  box-shadow: var(--ui-shadow-sm);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
</style>
