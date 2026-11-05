<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { http } from '../../app/http'
import TargetComparePage from './TargetComparePage.vue'

interface Target { id: string; name: string; category: string; source: string; verified_at: string; is_stale: boolean }
const keyword = ref('')
const targets = ref<Target[]>([])
const selected = ref<string[]>([])
const comparison = ref<any[]>([])
const goal = ref({ target_id: '', deadline: '', weekly_hours: 5, constraints: '' })
const goalSaved = ref(false)
const canCompare = computed(() => selected.value.length >= 2 && selected.value.length <= 3)
async function load() { targets.value = (await http.get('/targets', { params: { keyword: keyword.value || undefined } })).data }
function toggle(id: string, checked: boolean) {
  if (checked && selected.value.length < 3) selected.value.push(id)
  if (!checked) selected.value = selected.value.filter((item) => item !== id)
}
async function compare() {
  comparison.value = (await http.post('/targets/compare', { target_ids: selected.value })).data.targets
  if (!goal.value.target_id) goal.value.target_id = comparison.value[0]?.id || ''
}
async function createGoal() {
  await http.post('/goals', {
    target_id: goal.value.target_id,
    deadline: goal.value.deadline,
    weekly_hours: Number(goal.value.weekly_hours),
    constraints: goal.value.constraints.trim() || null,
    primary: true,
  })
  goalSaved.value = true
}
onMounted(load)
</script>

<template><section><h2>职业目标探索</h2><form @submit.prevent="load"><input v-model="keyword" placeholder="搜索岗位" /><button>搜索</button></form><p>请选择 2–3 个岗位进行比较。</p><div class="cards"><label v-for="target in targets" :key="target.id"><input :data-test="`select-${target.id}`" type="checkbox" :checked="selected.includes(target.id)" :disabled="!selected.includes(target.id) && selected.length >= 3" @change="toggle(target.id, ($event.target as HTMLInputElement).checked)" /><strong>{{ target.name }}</strong><span>{{ target.category }} · 来源 {{ target.source }} · 核验 {{ target.verified_at }}</span><em v-if="target.is_stale">数据待更新</em></label></div><button data-test="compare" :disabled="!canCompare" @click="compare">比较所选岗位</button><TargetComparePage v-if="comparison.length" :targets="comparison" /><form v-if="comparison.length" class="goal-form" @submit.prevent="createGoal"><h3>建立主目标</h3><label>目标岗位<select v-model="goal.target_id" data-test="goal-target" required><option v-for="target in comparison" :key="target.id" :value="target.id">{{ target.name }}</option></select></label><label>截止日期<input v-model="goal.deadline" data-test="goal-deadline" type="date" required /></label><label>每周投入（小时）<input v-model.number="goal.weekly_hours" data-test="goal-hours" type="number" min="1" max="168" required /></label><label>现实约束<textarea v-model="goal.constraints" placeholder="城市、课程或时间限制" /></label><button data-test="goal-submit">保存为主目标</button><p v-if="goalSaved">主目标已保存</p></form></section></template>
<style scoped>.cards { display: grid; gap: .75rem; margin: 1rem 0; }.cards label { display: flex; gap: 1rem; padding: 1rem; background: white; }.cards span { color: #64748b; }.goal-form { display: grid; gap: .75rem; margin-top: 1rem; padding: 1rem; background: white; }.goal-form label { display: grid; gap: .35rem; }</style>
