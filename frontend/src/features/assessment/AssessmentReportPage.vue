<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { http } from '../../app/http'

const props = defineProps<{ recordId: string }>()
const report = ref<Record<string, any> | null>(null)
onMounted(async () => { report.value = (await http.get(`/assessments/records/${props.recordId}/report`)).data })
</script>

<template>
  <section v-if="report"><h2>测评报告</h2><p>{{ new Date(report.completed_at).toLocaleDateString('zh-CN') }} · 版本 {{ report.scale_version }}</p>
    <div v-if="report.kind === 'interest'" data-test="interest-chart" class="chart"><h3>职业兴趣</h3><p v-for="(score, name) in report.dimension_scores" :key="name">{{ name }}：{{ score }}</p></div>
    <div v-if="report.kind === 'work_values'" data-test="value-chart" class="chart"><h3>职业价值观</h3><p v-for="(score, name) in report.dimension_scores" :key="name">{{ name }}：{{ score }}</p></div>
    <p class="disclaimer">{{ report.disclaimer }}</p>
  </section>
</template>
<style scoped>.chart { padding: 1rem; border-left: 4px solid #0d9488; background: white; }.disclaimer { color: #64748b; }</style>
