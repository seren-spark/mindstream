<script setup lang="ts">
import { IconDown } from '@arco-design/web-vue/es/icon'

defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  click: []
}>()
</script>

<template>
  <Transition name="ui-fade">
    <button
      v-if="visible"
      type="button"
      class="scroll-fab"
      aria-label="回到底部"
      @click="emit('click')"
    >
      <IconDown />
    </button>
  </Transition>
</template>

<style scoped>
.scroll-fab {
  position: absolute;
  right: 24px;
  bottom: 12px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  padding: 0;
  font-size: 18px;
  color: var(--color-text-2);
  cursor: pointer;
  background: color-mix(in srgb, var(--color-bg-2) 92%, transparent);
  border: 1px solid var(--color-border-2);
  border-radius: 50%;
  box-shadow: var(--ui-shadow-md);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  transition:
    transform var(--ui-duration-fast) var(--ui-ease),
    box-shadow var(--ui-duration) var(--ui-ease),
    color var(--ui-duration-fast) ease,
    border-color var(--ui-duration-fast) ease;
}

.scroll-fab:hover {
  color: rgb(var(--primary-6));
  border-color: rgb(var(--primary-4));
  transform: translateY(-2px);
  box-shadow: var(--ui-shadow-soft);
}

.scroll-fab:active {
  transform: scale(0.94);
}
</style>
