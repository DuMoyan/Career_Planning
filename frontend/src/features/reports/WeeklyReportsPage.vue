<script setup lang="ts">
import { ref } from 'vue'
import { http } from '../../app/http'
const report = ref<any>(null); const action = ref<'accept' | 'modify' | 'reject' | null>(null); const text = ref(''); const saved = ref(false)
function monday() { const now = new Date(); const day = now.getDay() || 7; now.setDate(now.getDate() - day + 1); return now.toISOString().slice(0, 10) }
async function generate() { report.value = (await http.post('/reports/weekly', { week_start: monday() })).data }
async function respond() { report.value = (await http.post(`/reports/weekly/${report.value.id}/response`, { action: action.value, text: text.value || null })).data; saved.value = true }
</script>
<template><section><h2>成长周报</h2><button data-test="generate-report" @click="generate">生成本周复盘</button><article v-if="report"><h3>{{ report.week_start }}</h3><div class="metrics"><strong>{{ report.metrics.completion_rate }}%</strong><span>完成 {{ report.metrics.completed_count }} / {{ report.metrics.task_count }}</span><span>{{ report.metrics.actual_hours }} / {{ report.metrics.estimated_hours }} 小时</span></div><p>{{ report.advice }}</p><small>{{ report.advice_mode === 'rules' ? '规则建议' : 'AI 辅助建议' }}</small><div><button data-test="accept" @click="action = 'accept'">接受并发起重规划</button><button data-test="modify" @click="action = 'modify'">修改</button><button data-test="reject" @click="action = 'reject'">拒绝</button></div><div v-if="action"><textarea v-model="text" data-test="feedback-text" placeholder="修改内容或拒绝原因" /><button data-test="submit-feedback" @click="respond">提交反馈</button></div><p v-if="saved">反馈已保存</p></article></section></template>
<style scoped>.metrics { display: flex; gap: 1.5rem; padding: 1rem; background: #eff6ff; }.metrics strong { color: #1e3a8a; font-size: 2rem; }</style>
