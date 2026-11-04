<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import { http } from '../../app/http'
import AsyncState from '../../shared/AsyncState.vue'

const state = ref<'loading' | 'error' | 'ready'>('loading')
const error = ref('')
const saved = ref(false)
const form = reactive({
  department: '', major: '', grade_level: '', gpa: null as number | null,
  available_hours: 0, constraints: [] as string[],
})

async function load() {
  state.value = 'loading'
  try {
    Object.assign(form, (await http.get('/profiles/me')).data)
    state.value = 'ready'
  } catch {
    state.value = 'error'
  }
}

async function save() {
  saved.value = false
  if (form.available_hours < 0 || form.available_hours > 168) {
    error.value = '每周可用时间必须在 0–168 小时之间'
    return
  }
  error.value = ''
  await http.put('/profiles/me', { ...form })
  saved.value = true
}

onMounted(load)
</script>

<template>
  <section>
    <h2>个人档案</h2>
    <AsyncState :state="state" error="档案加载失败" @retry="load">
      <form class="form-grid" @submit.prevent="save">
        <label>院系<input v-model="form.department" /></label>
        <label>专业<input v-model="form.major" /></label>
        <label>年级<input v-model="form.grade_level" /></label>
        <label>GPA<input v-model.number="form.gpa" type="number" min="0" max="5" step="0.01" /></label>
        <label>每周可用小时<input v-model.number="form.available_hours" data-test="hours" type="number" min="0" max="168" /></label>
        <p v-if="error" role="alert">{{ error }}</p>
        <button type="submit">保存档案</button><span v-if="saved">已保存</span>
      </form>
    </AsyncState>
  </section>
</template>

<style scoped>
.form-grid { display: grid; max-width: 680px; grid-template-columns: repeat(2, 1fr); gap: 1rem; }
label { display: grid; gap: .4rem; } input { padding: .65rem; } button { color: white; background: #0d9488; border: 0; border-radius: 8px; }
</style>
