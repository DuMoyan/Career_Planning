import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { http } from '../../app/http'
import TaskBoardPage from './TaskBoardPage.vue'

describe('成长任务与打卡', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('支持状态转换和三步内完成打卡', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({ data: [{ id: 'task-1', title: '编程练习', status: 'todo', due_date: '2026-11-08', weekly_hours: 3 }] })
    const post = vi.spyOn(http, 'post')
      .mockResolvedValueOnce({ data: { id: 'task-1', title: '编程练习', status: 'in_progress' } })
      .mockResolvedValueOnce({ data: { id: 'check-1' } })
    const wrapper = mount(TaskBoardPage)
    await flushPromises()

    await wrapper.get('[data-test="start"]').trigger('click')
    await wrapper.get('[data-test="open-checkin"]').trigger('click')
    await wrapper.get('[data-test="content"]').setValue('完成练习')
    await wrapper.get('[data-test="hours"]').setValue('1.5')
    await wrapper.get('[data-test="submit-checkin"]').trigger('click')
    await flushPromises()
    expect(post).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('打卡成功')
  })

  it('延期或放弃时要求填写原因', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({ data: [{ id: 'task-1', title: '练习', status: 'in_progress' }] })
    const wrapper = mount(TaskBoardPage)
    await flushPromises()
    await wrapper.get('[data-test="delay"]').trigger('click')
    expect(wrapper.get('[role="alert"]').text()).toContain('原因')
  })
})
