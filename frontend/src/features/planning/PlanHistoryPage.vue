<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { http } from '../../app/http'

const versions = ref<any[]>([])
onMounted(async () => {
  versions.value = (await http.get('/plans/history')).data
})
</script>
<template><section><h2>计划版本历史</h2><p v-if="!versions.length">暂无计划版本</p><article v-for="item in versions" :key="item.id"><strong>版本 {{ item.version }}</strong> · {{ item.status }}<span v-if="item.parent_version_id"> · 重规划自 {{ item.parent_version_id }}</span></article></section></template>
