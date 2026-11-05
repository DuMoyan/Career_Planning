import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { http } from '../../app/http'
import TargetExplorerPage from './TargetExplorerPage.vue'

const targets = [
  { id: 't1', name: '软件开发工程师', category: '技术', source: '教学演示岗位数据', verified_at: '2026-11-03', is_stale: false },
  { id: 't2', name: '数据分析师', category: '数据', source: '教学演示岗位数据', verified_at: '2026-11-03', is_stale: false },
  { id: 't3', name: '算法工程师', category: '技术', source: '教学演示岗位数据', verified_at: '2026-11-03', is_stale: false },
]

describe('职业目标探索与比较', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('限制选择 2–3 个岗位并分开显示偏好与能力差距', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({ data: targets })
    vi.spyOn(http, 'post').mockResolvedValue({ data: { targets: [{
      ...targets[0], interests: ['I'], values: ['成长成就'],
      gaps: [{ competency_code: 'programming', status: 'unknown', requirement_source: '教学演示岗位数据', evidence_ids: [] }],
    }] } })
    const wrapper = mount(TargetExplorerPage)
    await flushPromises()

    await wrapper.get('[data-test="select-t1"]').setValue(true)
    expect(wrapper.get('[data-test="compare"]').attributes('disabled')).toBeDefined()
    await wrapper.get('[data-test="select-t2"]').setValue(true)
    await wrapper.get('[data-test="compare"]').trigger('click')
    await flushPromises()

    expect(wrapper.get('[data-test="preference-section"]').text()).toContain('职业兴趣')
    expect(wrapper.get('[data-test="ability-section"]').text()).toContain('证据不足，待核验')
    expect(wrapper.text()).toContain('教学演示岗位数据')
  })

  it('可从比较结果建立带截止日期和每周投入的主目标', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({ data: targets })
    const post = vi.spyOn(http, 'post')
      .mockResolvedValueOnce({ data: { targets } })
      .mockResolvedValueOnce({ data: { id: 'goal-1', primary: true } })
    const wrapper = mount(TargetExplorerPage)
    await flushPromises()
    await wrapper.get('[data-test="select-t1"]').setValue(true)
    await wrapper.get('[data-test="select-t2"]').setValue(true)
    await wrapper.get('[data-test="compare"]').trigger('click')
    await flushPromises()

    await wrapper.get('[data-test="goal-target"]').setValue('t1')
    await wrapper.get('[data-test="goal-deadline"]').setValue('2027-06-30')
    await wrapper.get('[data-test="goal-hours"]').setValue('8')
    await wrapper.get('.goal-form').trigger('submit')
    await flushPromises()

    expect(post).toHaveBeenLastCalledWith('/goals', {
      target_id: 't1', deadline: '2027-06-30', weekly_hours: 8, constraints: null, primary: true,
    })
    expect(wrapper.text()).toContain('主目标已保存')
  })
})
