<script setup lang="ts">
import { useRouter } from 'vue-router'

import { useSessionStore } from '../app/session'

const session = useSessionStore()
const router = useRouter()
async function logout() {
  await session.logout()
  await router.push('/login')
}
</script>

<template>
  <div class="layout">
    <aside>
      <strong>学生成长中心</strong>
      <RouterLink to="/">概览</RouterLink>
      <RouterLink to="/profile">个人档案</RouterLink>
      <RouterLink to="/privacy">隐私授权</RouterLink>
      <RouterLink to="/assessments">职业测评</RouterLink>
      <button type="button" @click="logout">退出登录</button>
    </aside>
    <main><RouterView /></main>
  </div>
</template>

<style scoped>
.layout { display: grid; grid-template-columns: 220px 1fr; min-height: calc(100vh - 72px); }
aside { display: flex; flex-direction: column; gap: 1rem; padding: 1.5rem; color: white; background: #1e3a8a; }
aside a { color: #dbeafe; text-decoration: none; }
button { margin-top: auto; }
main { padding: 2rem; }
</style>
