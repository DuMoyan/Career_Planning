<script setup lang="ts">
import { ref } from 'vue'

import { http } from '../../app/http'

interface Grant { id: string; mentor_id: string; scopes: string[]; expires_at: string }
const mentorId = ref('')
const expiresAt = ref('')
const grants = ref<Grant[]>([])

async function createGrant() {
  const response = await http.post('/consents/mentor-grants', {
    mentor_id: mentorId.value,
    scopes: ['profile', 'assessment'],
    expires_at: new Date(expiresAt.value).toISOString(),
  })
  grants.value.push(response.data)
}
async function revoke(grant: Grant) {
  await http.delete(`/consents/mentor-grants/${grant.id}`)
  grants.value = grants.value.filter((item) => item.id !== grant.id)
}
</script>

<template>
  <section>
    <h2>隐私与导师授权</h2>
    <p>授权按数据范围和有效期生效，学生可随时撤销。</p>
    <form @submit.prevent="createGrant">
      <label>导师 ID<input v-model="mentorId" data-test="mentor-id" required /></label>
      <label>有效期至<input v-model="expiresAt" data-test="expires-at" type="datetime-local" required /></label>
      <button type="submit">创建授权</button>
    </form>
    <ul><li v-for="grant in grants" :key="grant.id">{{ grant.mentor_id }} · {{ grant.scopes.join('、') }} <button data-test="revoke" @click="revoke(grant)">撤销</button></li></ul>
  </section>
</template>
