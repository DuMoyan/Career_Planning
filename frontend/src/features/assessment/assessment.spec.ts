import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { http } from '../../app/http'
import AssessmentCenterPage from './AssessmentCenterPage.vue'
import AssessmentReportPage from './AssessmentReportPage.vue'
import AssessmentRunnerPage from './AssessmentRunnerPage.vue'

describe('职业测评流程', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('分段作答、显示进度并从服务端恢复', async () => {
    vi.spyOn(http, 'get')
      .mockResolvedValueOnce({ data: { id: 'scale-1', name: '职业兴趣', version: '1.0', items: [
        { id: 'q1', dimension: 'I', prompt: '我喜欢研究问题' },
        { id: 'q2', dimension: 'R', prompt: '我喜欢动手实践' },
      ] } })
      .mockResolvedValueOnce({ data: { answers: { q1: 4 } } })
    const save = vi.spyOn(http, 'put').mockResolvedValue({ data: { saved: true } })
    const wrapper = mount(AssessmentRunnerPage, { props: { scaleId: 'scale-1' } })
    await flushPromises()

    expect(wrapper.text()).toContain('1 / 2')
    await wrapper.get('[data-test="answer-q2-5"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('2 / 2')
    expect(save).toHaveBeenCalledWith('/assessments/scales/scale-1/progress', { answers: { q1: 4, q2: 5 } })
  })

  it('提交前确认，并在报告中分开呈现兴趣与价值观及版本声明', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({ data: {
      id: 'record-1', kind: 'interest', completed_at: '2026-11-04T10:00:00Z',
      dimension_scores: { I: 20, R: 18 }, top_dimensions: ['I'], scale_version: '1.0',
      scoring_version: '1.0', interpretation_version: '1.0', disclaimer: '结果仅供生涯探索参考',
    } })
    const wrapper = mount(AssessmentReportPage, { props: { recordId: 'record-1' } })
    await flushPromises()

    expect(wrapper.find('[data-test="interest-chart"]').exists()).toBe(true)
    expect(wrapper.find('[data-test="value-chart"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('版本 1.0')
    expect(wrapper.text()).toContain('结果仅供生涯探索参考')
  })

  it('网络失败显示重试状态', async () => {
    vi.spyOn(http, 'get').mockRejectedValueOnce(new Error('network')).mockResolvedValueOnce({ data: [] })
    const wrapper = mount(AssessmentCenterPage, { global: { stubs: { RouterLink: true } } })
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('加载失败')

    await wrapper.get('[data-test="retry"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('暂无可用测评')
  })
})
