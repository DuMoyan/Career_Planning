<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { http } from '../../app/http'
import CompetencyChart from '../../shared/charts/CompetencyChart.vue'

interface Candidate { competency_code: string; description: string; demonstrated_level: number }
interface Evidence { id: string; competency_code: string; demonstrated_level: number; description: string; source_deleted: boolean }
const error = ref('')
const resumeId = ref('')
const candidates = ref<Candidate[]>([])
const evidence = ref<Evidence[]>([])
const profile = ref<any>(null)

async function loadEvidence() { evidence.value = (await http.get('/competencies/evidence')).data }
async function upload(event: Event) {
  error.value = ''
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!/\.(pdf|docx|txt)$/i.test(file.name)) { error.value = '仅支持 PDF、DOCX 或 TXT 文件'; return }
  if (file.size > 10_485_760) { error.value = '文件不能超过 10MB'; return }
  const body = new FormData(); body.append('file', file)
  const response = await http.post('/resumes', body)
  resumeId.value = response.data.id
  candidates.value = response.data.candidates.map((item: any) => ({ ...item, demonstrated_level: 3 }))
}
async function confirm(candidate: Candidate) {
  const response = await http.post('/competencies/evidence', { resume_id: resumeId.value, ...candidate })
  evidence.value.push({ id: response.data.id, ...candidate, source_deleted: false })
  candidates.value = candidates.value.filter((item) => item !== candidate)
}
async function updateProfile() { profile.value = (await http.post('/competencies/profiles')).data }
onMounted(loadEvidence)
</script>

<template>
  <section><h2>能力画像与证据</h2><p>上传简历后先检查解析草稿，只有明确确认的条目才会成为能力证据。</p>
    <input type="file" accept=".pdf,.docx,.txt" @change="upload" /><p v-if="error" role="alert">{{ error }}</p>
    <article v-for="candidate in candidates" :key="candidate.competency_code" class="candidate"><strong>{{ candidate.competency_code }}</strong><textarea v-model="candidate.description" data-test="candidate-description" /><label>等级<input v-model.number="candidate.demonstrated_level" type="number" min="1" max="4" /></label><button data-test="confirm-evidence" @click="confirm(candidate)">确认创建证据</button></article>
    <h3>已确认证据</h3><ul><li v-for="item in evidence" :key="item.id">{{ item.competency_code }} · {{ item.description }} · 证据 {{ item.id }}<span v-if="item.source_deleted">（源文件已删除）</span></li></ul>
    <button data-test="update-profile" @click="updateProfile">更新能力画像</button>
    <section v-if="profile"><h3>画像版本 {{ profile.version }}</h3><CompetencyChart :dimensions="profile.dimensions" /></section>
  </section>
</template>
<style scoped>.candidate { display: grid; gap: .5rem; margin: 1rem 0; padding: 1rem; background: white; } textarea { min-height: 70px; }</style>
