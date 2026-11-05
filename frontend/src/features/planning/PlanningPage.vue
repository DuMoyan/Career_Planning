<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

import { http } from '../../app/http'

const goals = ref<any[]>([])
const run = ref<any>(null)
const error = ref('')
const progress = ref('')
const draftVersion = ref<any>(null)
const confirming = ref(false)
const activated = ref(false)
let events: EventSource | null = null
let pollTimer: ReturnType<typeof setTimeout> | null = null

async function loadGoals() { goals.value = (await http.get('/goals')).data }
async function poll(runId: string) {
  const response = await http.get(`/plans/generations/${runId}`)
  run.value = response.data
  progress.value = response.data.status
}
async function pollUntilTerminal(runId: string) {
  await poll(runId)
  if (run.value.status === 'running' || run.value.status === 'queued') {
    pollTimer = setTimeout(() => void pollUntilTerminal(runId), 500)
  } else if (run.value.status === 'failed') {
    error.value = `规划生成失败：${run.value.error_code || '未知错误'}`
  }
}
function watchEvents(runId: string) {
  if (typeof EventSource === 'undefined') return pollUntilTerminal(runId)
  events = new EventSource(`/api/v1/plans/generations/${runId}/events`)
  events.addEventListener('completed', async () => { events?.close(); await poll(runId) })
  events.addEventListener('failed', async () => { events?.close(); await poll(runId) })
  events.onerror = async () => { events?.close(); await pollUntilTerminal(runId) }
}
async function generate() {
  const primary = goals.value.find((item) => item.primary)
  if (!primary?.deadline) { error.value = '请先设置主目标和截止日期'; return }
  error.value = ''; progress.value = '正在生成'
  run.value = (await http.post('/plans/generations')).data
  if (run.value.status !== 'completed') watchEvents(run.value.id)
}
async function prepareActivation() {
  draftVersion.value = (await http.post('/plans/drafts', { ai_run_id: run.value.id })).data
  draftVersion.value = (await http.patch(`/plans/versions/${draftVersion.value.id}`, {
    snapshot: run.value.plan_snapshot,
  })).data
  confirming.value = true
}
async function activate() {
  await http.post(`/plans/versions/${draftVersion.value.id}/activate`, {}, { headers: { 'Idempotency-Key': crypto.randomUUID() } })
  confirming.value = false; activated.value = true
}
onMounted(loadGoals)
onBeforeUnmount(() => { events?.close(); if (pollTimer) clearTimeout(pollTimer) })
</script>

<template><section><h2>智能规划</h2><p>系统会基于主目标、能力证据和每周可用时间生成可编辑草稿；激活前不会创建任务。</p><button data-test="generate" @click="generate">生成规划草稿</button><p v-if="error" role="alert">{{ error }}</p><p v-if="progress">{{ progress }}</p>
  <article v-if="run?.plan_snapshot" class="plan"><strong v-if="run.generation_mode === 'rules'" class="badge">规则兜底 · {{ run.fallback_reason }}</strong><h3>里程碑</h3><div v-for="milestone in run.plan_snapshot.milestones" :key="milestone.title"><input v-model="milestone.title" data-test="milestone-title" /><small>验收：{{ milestone.acceptance_criteria.join('；') }}</small></div><h3>任务</h3><input v-for="task in run.plan_snapshot.tasks" :key="task.title" v-model="task.title" /><h3>来源</h3><p>{{ run.plan_snapshot.sources.join('、') }}</p><h3>待核验未知项</h3><p>{{ run.plan_snapshot.unknowns.join('、') || '无' }}</p><h3>风险</h3><p>{{ run.plan_snapshot.risks.join('、') }}</p><button data-test="prepare-activate" @click="prepareActivation">准备激活</button></article>
  <div v-if="confirming" role="dialog"><p>激活后才会创建成长任务，确认激活此版本？</p><button data-test="confirm-activate" @click="activate">确认激活</button></div><p v-if="activated">计划已激活</p>
</section></template>
<style scoped>.plan { display: grid; gap: .75rem; margin-top: 1rem; padding: 1.5rem; background: white; }.badge { width: fit-content; padding: .3rem .6rem; color: #92400e; background: #fef3c7; border-radius: 999px; } small { display: block; }</style>
