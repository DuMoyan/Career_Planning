$ErrorActionPreference = 'Stop'
$base = if ($env:CAREER_BASE_URL) { $env:CAREER_BASE_URL } else { 'http://localhost:8080/api/v1' }
function Pass($name) { Write-Host "PASS $name" -ForegroundColor Green }
$login = Invoke-RestMethod -Method Post -Uri "$base/auth/login" -ContentType 'application/json' -Body (@{identifier='demo-student';password='Demo!2026'} | ConvertTo-Json)
$headers = @{Authorization="Bearer $($login.access_token)"}; Pass '学生登录'
Invoke-RestMethod -Uri "$base/profiles/me" -Headers $headers | Out-Null; Pass '读取档案'
$scales = Invoke-RestMethod -Uri "$base/assessments/scales" -Headers $headers
if ($scales.Count -ne 2) { throw '量表数量错误' }; Pass '读取两套量表'
$targets = Invoke-RestMethod -Uri "$base/targets" -Headers $headers
$body = @{target_ids=@($targets[0].id,$targets[1].id)} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$base/targets/compare" -Headers $headers -ContentType 'application/json' -Body $body | Out-Null; Pass '比较两个岗位'
$run = Invoke-RestMethod -Method Post -Uri "$base/plans/generations" -Headers $headers
$deadline = (Get-Date).AddSeconds(30)
while ($run.status -in @('queued', 'running') -and (Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 250
    $run = Invoke-RestMethod -Uri "$base/plans/generations/$($run.id)" -Headers $headers
}
if ($run.status -ne 'completed') { throw "规划生成未完成，当前状态：$($run.status)" }
if ($run.generation_mode -ne 'rules') { throw '无模型密钥时应使用规则模式' }; Pass '规则模式生成规划'
$history = Invoke-RestMethod -Uri "$base/plans/history" -Headers $headers
$active = @($history | Where-Object { $_.status -eq 'active' })
if ($active.Count -eq 0) {
    $draft = Invoke-RestMethod -Method Post -Uri "$base/plans/drafts" -Headers $headers -ContentType 'application/json' -Body (@{ai_run_id=$run.id}|ConvertTo-Json)
    $activateHeaders = $headers.Clone(); $activateHeaders['Idempotency-Key'] = [guid]::NewGuid().ToString()
    Invoke-RestMethod -Method Post -Uri "$base/plans/versions/$($draft.id)/activate" -Headers $activateHeaders | Out-Null
}
Pass '确认激活计划'
$tasks = Invoke-RestMethod -Uri "$base/tasks" -Headers $headers
$checkHeaders = $headers.Clone(); $checkHeaders['Idempotency-Key'] = [guid]::NewGuid().ToString()
Invoke-RestMethod -Method Post -Uri "$base/tasks/$($tasks[0].id)/check-ins" -Headers $checkHeaders -ContentType 'application/json' -Body (@{content='冒烟测试打卡';actual_hours=1}|ConvertTo-Json) | Out-Null; Pass '任务打卡'
$today = Get-Date; $offset = ([int]$today.DayOfWeek + 6) % 7; $weekStart = $today.AddDays(-$offset).ToString('yyyy-MM-dd')
Invoke-RestMethod -Method Post -Uri "$base/reports/weekly" -Headers $headers -ContentType 'application/json' -Body (@{week_start=$weekStart}|ConvertTo-Json) | Out-Null; Pass '获取周报'
