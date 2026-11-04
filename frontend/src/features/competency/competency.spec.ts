import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { http } from '../../app/http'
import CompetencyPage from './CompetencyPage.vue'

describe('简历证据与能力画像', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.spyOn(http, 'get').mockResolvedValue({ data: [] })
  })

  it('在上传前校验文件类型和 10MB 限制', async () => {
    const wrapper = mount(CompetencyPage)
    await flushPromises()
    const input = wrapper.get('input[type="file"]')
    Object.defineProperty(input.element, 'files', { configurable: true, value: [new File(['x'], 'resume.exe')] })
    await input.trigger('change')
    expect(wrapper.get('[role="alert"]').text()).toContain('PDF、DOCX 或 TXT')

    const large = new File([new Uint8Array(10_485_761)], 'resume.pdf', { type: 'application/pdf' })
    Object.defineProperty(input.element, 'files', { configurable: true, value: [large] })
    await input.trigger('change')
    expect(wrapper.get('[role="alert"]').text()).toContain('10MB')
  })

  it('允许编辑解析草稿，确认后才创建证据并更新画像', async () => {
    vi.spyOn(http, 'post')
      .mockResolvedValueOnce({ data: { id: 'resume-1', candidates: [{ competency_code: 'programming', description: 'Python 项目' }] } })
      .mockResolvedValueOnce({ data: { id: 'evidence-1' } })
      .mockResolvedValueOnce({ data: { id: 'profile-2', version: 2, dimensions: { programming: { level: 3, evidence_ids: ['evidence-1'] } } } })
    const wrapper = mount(CompetencyPage)
    await flushPromises()
    const input = wrapper.get('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [new File(['Python'], 'resume.txt', { type: 'text/plain' })] })
    await input.trigger('change')
    await flushPromises()

    await wrapper.get('[data-test="candidate-description"]').setValue('独立完成 Python 项目')
    await wrapper.get('[data-test="confirm-evidence"]').trigger('click')
    await wrapper.get('[data-test="update-profile"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('画像版本 2')
    expect(wrapper.text()).toContain('证据 evidence-1')
  })
})
