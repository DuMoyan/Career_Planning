<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { http } from '../../app/http'
import TargetComparePage from './TargetComparePage.vue'

interface Target { id: string; name: string; category: string; source: string; verified_at: string; is_stale: boolean }
const keyword = ref('')
const targets = ref<Target[]>([])
const selected = ref<string[]>([])
const comparison = ref<any[]>([])
const canCompare = computed(() => selected.value.length >= 2 && selected.value.length <= 3)
async function load() { targets.value = (await http.get('/targets', { params: { keyword: keyword.value || undefined } })).data }
function toggle(id: string, checked: boolean) {
  if (checked && selected.value.length < 3) selected.value.push(id)
  if (!checked) selected.value = selected.value.filter((item) => item !== id)
}
async function compare() { comparison.value = (await http.post('/targets/compare', { target_ids: selected.value })).data.targets }
onMounted(load)
</script>

<template><section><h2>职业目标探索</h2><form @submit.prevent="load"><input v-model="keyword" placeholder="搜索岗位" /><button>搜索</button></form><p>请选择 2–3 个岗位进行比较。</p><div class="cards"><label v-for="target in targets" :key="target.id"><input :data-test="`select-${target.id}`" type="checkbox" :checked="selected.includes(target.id)" :disabled="!selected.includes(target.id) && selected.length >= 3" @change="toggle(target.id, ($event.target as HTMLInputElement).checked)" /><strong>{{ target.name }}</strong><span>{{ target.category }} · 来源 {{ target.source }} · 核验 {{ target.verified_at }}</span><em v-if="target.is_stale">数据待更新</em></label></div><button data-test="compare" :disabled="!canCompare" @click="compare">比较所选岗位</button><TargetComparePage v-if="comparison.length" :targets="comparison" /></section></template>
<style scoped>.cards { display: grid; gap: .75rem; margin: 1rem 0; }.cards label { display: flex; gap: 1rem; padding: 1rem; background: white; }.cards span { color: #64748b; }</style>
