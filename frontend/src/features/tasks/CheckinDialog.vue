<script setup lang="ts">
import { ref } from 'vue'
const emit = defineEmits<{ submit: [payload: { content: string; actual_hours: number; proof_url: string | null }]; close: [] }>()
const content = ref(''); const hours = ref(1); const proof = ref('')
</script>
<template><div role="dialog"><h3>任务打卡</h3><label>完成内容<textarea v-model="content" data-test="content" /></label><label>实际投入小时<input v-model.number="hours" data-test="hours" type="number" min="0.1" step="0.1" /></label><label>证明链接（可选）<input v-model="proof" type="url" /></label><button data-test="submit-checkin" @click="emit('submit', { content, actual_hours: hours, proof_url: proof || null })">提交打卡</button><button @click="emit('close')">取消</button></div></template>
