<script setup lang="ts">
import PreferenceChart from '../../shared/charts/PreferenceChart.vue'
defineProps<{ targets: any[] }>()
const label: Record<string, string> = { met: '已满足', developable_gap: '可发展差距', hard_unmet: '硬性要求未满足', unknown: '证据不足，待核验' }
</script>
<template><section class="comparison"><article v-for="target in targets" :key="target.id"><h3>{{ target.name }}</h3><section data-test="preference-section"><h4>偏好匹配（不参与能力评分）</h4><PreferenceChart :interests="target.interests || []" :values="target.values || []" /></section><section data-test="ability-section"><h4>能力差距</h4><p v-for="gap in target.gaps" :key="gap.competency_code">{{ gap.competency_code }}：{{ label[gap.status] }} · 来源 {{ gap.requirement_source }}<span v-if="gap.evidence_ids?.length"> · 证据 {{ gap.evidence_ids.join('、') }}</span></p></section></article></section></template>
<style scoped>.comparison { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; } article { padding: 1rem; background: white; } [data-test="ability-section"] { border-top: 1px solid #cbd5e1; }</style>
