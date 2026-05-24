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
    <div class="page-container__body">
      <slot />
    </div>
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
  margin-bottom: 16px;
}

.page-container__title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-1);
}

.page-container__body {
  background: var(--color-bg-2);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid var(--color-border-2);
}
</style>
