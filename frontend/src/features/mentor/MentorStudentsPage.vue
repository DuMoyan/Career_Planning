<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { http } from '../../app/http'
const students = ref<any[]>([]); const detail = ref<any>(null); const error = ref(''); const comment = ref(''); const saved = ref(false)
onMounted(async () => { students.value = (await http.get('/mentor/students')).data })
async function select(id: string) { error.value = ''; try { detail.value = (await http.get(`/mentor/students/${id}`)).data } catch { error.value = '导师授权已过期、撤销或范围不足' } }
async function submit() { await http.post(`/mentor/plan-versions/${detail.value.plan_versions[0].id}/comments`, { content: comment.value }); saved.value = true }
</script>
<template><section><h3>授权学生</h3><button v-for="student in students" :key="student.student_id" :data-test="`student-${student.student_id}`" @click="select(student.student_id)">{{ student.student_id }} · {{ student.scopes.join('、') }}</button><p v-if="error" role="alert">{{ error }}</p><article v-if="detail"><h4>计划进展</h4><div v-for="version in detail.plan_versions" :key="version.id">版本 {{ version.version }} · {{ version.status }} · 来源 {{ version.sources.join('、') }}</div><textarea v-model="comment" data-test="comment" /><button data-test="submit-comment" @click="submit">提交评论</button><span v-if="saved">评论已提交</span></article></section></template>
