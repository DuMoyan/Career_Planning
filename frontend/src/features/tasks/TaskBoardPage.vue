<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { http } from '../../app/http'
import CheckinDialog from './CheckinDialog.vue'
const tasks = ref<any[]>([]); const checking = ref<any>(null); const message = ref(''); const error = ref('')
async function load() { tasks.value = (await http.get('/tasks')).data }
async function transition(task: any, status: string, reason?: string) {
  if (['delayed', 'abandoned'].includes(status) && !reason) { error.value = '延期或放弃必须填写原因'; return }
  Object.assign(task, (await http.post(`/tasks/${task.id}/transition`, { status, reason })).data)
}
async function checkin(payload: any) { await http.post(`/tasks/${checking.value.id}/check-ins`, payload, { headers: { 'Idempotency-Key': crypto.randomUUID() } }); checking.value = null; message.value = '打卡成功' }
onMounted(load)
</script>
<template><section><h2>本周成长任务</h2><p v-if="!tasks.length">当前没有任务，激活规划后会自动生成。</p><p v-if="error" role="alert">{{ error }}</p><p v-if="message">{{ message }}</p><article v-for="task in tasks" :key="task.id"><h3>{{ task.title }}</h3><p>{{ task.status }} · 截止 {{ task.due_date }} · 预计 {{ task.weekly_hours }} 小时</p><button v-if="task.status === 'todo'" data-test="start" @click="transition(task, 'in_progress')">开始</button><button data-test="open-checkin" @click="checking = task">打卡</button><button data-test="delay" @click="transition(task, 'delayed')">延期</button></article><CheckinDialog v-if="checking" @submit="checkin" @close="checking = null" /></section></template>
<style scoped>article { margin: 1rem 0; padding: 1rem; background: white; } button { margin-right: .5rem; }</style>
