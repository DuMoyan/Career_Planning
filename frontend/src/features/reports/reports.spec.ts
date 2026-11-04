import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { http } from '../../app/http'
import WeeklyReportsPage from './WeeklyReportsPage.vue'

describe('成长周报', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('显示周指标并支持接受、修改和拒绝建议', async () => {
    vi.spyOn(http, 'post').mockResolvedValue({ data: { id: 'report-1', week_start: '2026-11-02', metrics: {
      task_count: 2, completed_count: 1, completion_rate: 50, estimated_hours: 5, actual_hours: 3.5,
      delayed_count: 1, needs_adjustment: true,
    }, advice: '建议调整任务量', advice_mode: 'rules' } })
    const wrapper = mount(WeeklyReportsPage)
    await wrapper.get('[data-test="generate-report"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('50%')
    expect(wrapper.text()).toContain('3.5 / 5 小时')

    await wrapper.get('[data-test="modify"]').trigger('click')
    await wrapper.get('[data-test="feedback-text"]').setValue('减少一项练习')
    await wrapper.get('[data-test="submit-feedback"]').trigger('click')
    await flushPromises()
    expect(http.post).toHaveBeenLastCalledWith('/reports/weekly/report-1/response', { action: 'modify', text: '减少一项练习' })
  })
})
