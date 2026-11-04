<script setup lang="ts">
interface Props {
  dimensions: Record<string, { level: number }>
}
defineProps<Props>()
</script>
<template><div class="chart" aria-label="能力画像"><div v-for="(item, code) in dimensions" :key="code"><span>{{ code }}</span><progress :value="item.level" max="4" /> {{ item.level }}/4</div></div></template>
<style scoped>.chart { display: grid; gap: .75rem; } progress { accent-color: #1e3a8a; }</style>
