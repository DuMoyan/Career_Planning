<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useSessionStore } from '../../app/session'

const identifier = ref('')
const password = ref('')
const submitting = ref(false)
const errorMessage = ref('')
const session = useSessionStore()
const router = useRouter()

async function submit() {
  submitting.value = true
  errorMessage.value = ''
  try {
    await session.login(identifier.value, password.value)
    const destination = session.role === 'student' ? '/' : `/${session.role}`
    await router.push(destination)
  } catch {
    errorMessage.value = '登录失败，请检查账号或密码'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="login-card">
    <h2>登录职业规划系统</h2>
    <form @submit.prevent="submit">
      <label>学号或账号<input v-model="identifier" data-test="identifier" autocomplete="username" /></label>
      <label>密码<input v-model="password" data-test="password" type="password" autocomplete="current-password" /></label>
      <p v-if="errorMessage" role="alert">{{ errorMessage }}</p>
      <button :disabled="submitting" type="submit">{{ submitting ? '登录中…' : '登录' }}</button>
    </form>
  </section>
</template>

<style scoped>
.login-card { width: min(420px, calc(100% - 2rem)); margin: 5rem auto; padding: 2rem; border-radius: 16px; background: white; box-shadow: 0 16px 40px #1e3a8a1f; }
form, label { display: grid; gap: .75rem; }
form { gap: 1rem; }
input { padding: .75rem; border: 1px solid #cbd5e1; border-radius: 8px; }
button { padding: .75rem; color: white; border: 0; border-radius: 8px; background: #0d9488; }
[role="alert"] { color: #b91c1c; }
</style>
