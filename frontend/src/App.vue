<template>
  <header class="app-header">
    <h1>AI智能体大学生职业生涯规划系统</h1>
    <p>从自我探索到行动复盘，建立可解释、可调整的成长计划。</p>
  </header>
  <RouterView />
</template>

<style scoped>
:global(*) {
  box-sizing: border-box;
}

:global(body) {
  margin: 0;
  color: #172554;
  background: #f8fafc;
  font-family: Inter, "Microsoft YaHei", sans-serif;
}

.app-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 2rem;
  color: white;
  background: #172554;
}

h1 {
  margin: 0;
  color: white;
}

p {
  margin: 0;
  color: #bfdbfe;
}
</style>

