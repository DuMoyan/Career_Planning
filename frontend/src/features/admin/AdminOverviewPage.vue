<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { http } from '../../app/http'
const data = ref<any>({ targets: [], scale_versions: [], audits: [] })
onMounted(async () => { data.value = (await http.get('/admin/overview')).data })
</script>
<template><section><p>以下信息仅供只读核验。</p><div class="tabs"><article><h3>岗位目录</h3><p v-for="item in data.targets" :key="item">{{ item }}</p></article><article><h3>量表版本</h3><p v-for="item in data.scale_versions" :key="item">{{ item }}</p></article><article><h3>审计日志</h3><p v-for="item in data.audits" :key="item.id">{{ item.event_type }} · {{ item.result }}</p></article></div></section></template>
<style scoped>.tabs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; } article { padding: 1rem; background: white; }</style>
