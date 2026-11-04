import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { http } from '../../app/http'
import PlanningPage from './PlanningPage.vue'

describe('规划生成与激活', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('没有主目标和截止日期时禁止生成', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({ data: [] })
    const wrapper = mount(PlanningPage)
    await flushPromises()
    await wrapper.get('[data-test="generate"]').trigger('click')
    expect(wrapper.get('[role="alert"]').text()).toContain('主目标和截止日期')
  })

  it('展示规则降级、来源/未知/风险并在确认后激活', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({ data: [{ id: 'goal-1', primary: true, deadline: '2027-06-30' }] })
    vi.spyOn(http, 'post')
      .mockResolvedValueOnce({ data: { id: 'run-1', status: 'completed', generation_mode: 'rules', fallback_reason: 'missing_api_key', plan_snapshot: {
        milestones: [{ title: '完成作品', acceptance_criteria: ['可运行'] }], tasks: [{ title: '编程练习' }],
        sources: ['教学演示岗位数据'], unknowns: ['research_analysis'], risks: ['时间变化'], generation_mode: 'rules',
      } } })
      .mockResolvedValueOnce({ data: { id: 'version-1', status: 'draft' } })
      .mockResolvedValueOnce({ data: { id: 'version-1', status: 'active' } })
    const wrapper = mount(PlanningPage)
    await flushPromises()
    await wrapper.get('[data-test="generate"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('规则兜底')
    expect(wrapper.text()).toContain('教学演示岗位数据')
    expect(wrapper.text()).toContain('research_analysis')
    expect(wrapper.text()).toContain('时间变化')
    await wrapper.get('[data-test="prepare-activate"]').trigger('click')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true)
    await wrapper.get('[data-test="confirm-activate"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('计划已激活')
  })
})
