<script setup lang="ts">
defineProps<{ state: 'loading' | 'error' | 'empty' | 'ready'; error?: string }>()
defineEmits<{ retry: [] }>()
</script>

<template>
  <p v-if="state === 'loading'" aria-live="polite">正在加载…</p>
  <div v-else-if="state === 'error'" role="alert">
    <p>{{ error || '加载失败，请稍后重试' }}</p>
    <button data-test="retry" type="button" @click="$emit('retry')">重试</button>
  </div>
  <p v-else-if="state === 'empty'">暂无可用测评</p>
  <slot v-else />
</template>
