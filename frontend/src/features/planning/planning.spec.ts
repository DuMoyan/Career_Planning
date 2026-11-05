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
    vi.spyOn(http, 'patch').mockResolvedValue({ data: { id: 'version-1', status: 'draft' } })
    const wrapper = mount(PlanningPage)
    await flushPromises()
    await wrapper.get('[data-test="generate"]').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('规则兜底')
    expect(wrapper.text()).toContain('教学演示岗位数据')
    expect(wrapper.text()).toContain('research_analysis')
    expect(wrapper.text()).toContain('时间变化')
    await wrapper.get('[data-test="prepare-activate"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('[role="dialog"]').exists()).toBe(true)
    await wrapper.get('[data-test="confirm-activate"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('计划已激活')
  })

  it('激活前保存学生编辑后的草稿快照', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({ data: [{ id: 'goal-1', primary: true, deadline: '2027-06-30' }] })
    const post = vi.spyOn(http, 'post')
      .mockResolvedValueOnce({ data: { id: 'run-1', status: 'completed', generation_mode: 'rules', plan_snapshot: {
        milestones: [{ title: '原里程碑', acceptance_criteria: ['可运行'] }], tasks: [{ title: '原任务' }],
        sources: ['教学演示岗位数据'], unknowns: [], risks: [], generation_mode: 'rules',
      } } })
      .mockResolvedValueOnce({ data: { id: 'version-1', status: 'draft' } })
    const patch = vi.spyOn(http, 'patch').mockResolvedValue({ data: { id: 'version-1', status: 'draft' } })
    const wrapper = mount(PlanningPage)
    await flushPromises()
    await wrapper.get('[data-test="generate"]').trigger('click')
    await flushPromises()
    await wrapper.get('[data-test="milestone-title"]').setValue('学生确认后的里程碑')
    await wrapper.get('[data-test="prepare-activate"]').trigger('click')
    await flushPromises()

    expect(post).toHaveBeenLastCalledWith('/plans/drafts', { ai_run_id: 'run-1' })
    expect(patch).toHaveBeenCalledWith('/plans/versions/version-1', {
      snapshot: expect.objectContaining({
        milestones: [expect.objectContaining({ title: '学生确认后的里程碑' })],
      }),
    })
  })

  it('后台生成时持续轮询直至完成', async () => {
    const get = vi.spyOn(http, 'get')
      .mockResolvedValueOnce({ data: [{ id: 'goal-1', primary: true, deadline: '2027-06-30' }] })
      .mockResolvedValueOnce({ data: { id: 'run-1', status: 'completed', plan_snapshot: {
        milestones: [], tasks: [], sources: ['岗位要求'], unknowns: [], risks: [], generation_mode: 'rules',
      } } })
    vi.spyOn(http, 'post').mockResolvedValue({ data: { id: 'run-1', status: 'running' } })
    const wrapper = mount(PlanningPage)
    await flushPromises()

    await wrapper.get('[data-test="generate"]').trigger('click')
    await flushPromises()

    expect(get).toHaveBeenLastCalledWith('/plans/generations/run-1')
    expect(wrapper.text()).toContain('岗位要求')
  })
})
