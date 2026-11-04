<script setup lang="ts">
interface Props {
  interests: string[]
  values: string[]
}
defineProps<Props>()
</script>
<template><div class="preference"><p>职业兴趣：{{ interests.join('、') || '待测评' }}</p><p>职业价值观：{{ values.join('、') || '待测评' }}</p></div></template>
<style scoped>.preference { padding: 1rem; border-left: 4px solid #0d9488; background: #f0fdfa; }</style>
