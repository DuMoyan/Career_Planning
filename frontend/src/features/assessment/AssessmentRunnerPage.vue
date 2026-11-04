<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { http } from '../../app/http'

const props = defineProps<{ scaleId: string }>()
interface Item { id: string; dimension: string; prompt: string }
const name = ref('')
const items = ref<Item[]>([])
const answers = reactive<Record<string, number>>({})
const confirming = ref(false)
const submitted = ref(false)
const progress = computed(() => `${Object.keys(answers).length} / ${items.value.length}`)

async function load() {
  const scaleRequest = http.get(`/assessments/scales/${props.scaleId}`)
  const progressRequest = http.get(`/assessments/scales/${props.scaleId}/progress`)
  const [scale, saved] = await Promise.all([scaleRequest, progressRequest])
  name.value = scale.data.name
  items.value = scale.data.items
  Object.assign(answers, saved.data.answers)
}
async function answer(id: string, value: number) {
  answers[id] = value
  await http.put(`/assessments/scales/${props.scaleId}/progress`, { answers: { ...answers } })
}
async function submit() {
  await http.post(`/assessments/scales/${props.scaleId}/submit`, {}, { headers: { 'Idempotency-Key': crypto.randomUUID() } })
  confirming.value = false
  submitted.value = true
}
onMounted(load)
</script>

<template>
  <section><h2>{{ name }}</h2><p aria-live="polite">作答进度 {{ progress }}</p>
    <article v-for="item in items" :key="item.id"><p>{{ item.prompt }}</p><div><button v-for="score in 5" :key="score" :data-test="`answer-${item.id}-${score}`" :aria-pressed="answers[item.id] === score" @click="answer(item.id, score)">{{ score }}</button></div></article>
    <button :disabled="Object.keys(answers).length !== items.length" @click="confirming = true">提交测评</button>
    <div v-if="confirming" role="dialog"><p>提交后将生成本次测评报告，确认提交吗？</p><button @click="submit">确认提交</button></div>
    <p v-if="submitted">提交成功</p>
  </section>
</template>
