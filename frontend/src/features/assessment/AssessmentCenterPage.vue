<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { http } from '../../app/http'
import AsyncState from '../../shared/AsyncState.vue'

interface Scale { id: string; name: string; kind: string; version: string; item_count: number }
const state = ref<'loading' | 'error' | 'empty' | 'ready'>('loading')
const scales = ref<Scale[]>([])
async function load() {
  state.value = 'loading'
  try {
    scales.value = (await http.get('/assessments/scales')).data
    state.value = scales.value.length ? 'ready' : 'empty'
  } catch { state.value = 'error' }
}
onMounted(load)
</script>

<template>
  <section><h2>职业测评</h2><AsyncState :state="state" @retry="load"><article v-for="scale in scales" :key="scale.id"><h3>{{ scale.name }}</h3><p>{{ scale.item_count }} 题 · 版本 {{ scale.version }}</p><RouterLink :to="`/assessments/${scale.id}`">开始或继续</RouterLink></article></AsyncState></section>
</template>
