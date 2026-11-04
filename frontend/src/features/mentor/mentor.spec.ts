import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { http } from '../../app/http'
import MentorStudentsPage from './MentorStudentsPage.vue'

describe('导师工作台', () => {
  it('显示授权学生并提交计划版本评论', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({ data: [{ student_id: 's1', scopes: ['plan_progress'], expires_at: '2027-01-01' }] }).mockResolvedValueOnce({ data: { student_id: 's1', plan_versions: [{ id: 'v1', version: 1, status: 'active', sources: ['岗位样本'] }] } })
    const post = vi.spyOn(http, 'post').mockResolvedValue({ data: { id: 'c1' } })
    const wrapper = mount(MentorStudentsPage); await flushPromises()
    await wrapper.get('[data-test="student-s1"]').trigger('click'); await flushPromises()
    await wrapper.get('[data-test="comment"]').setValue('建议拆分任务')
    await wrapper.get('[data-test="submit-comment"]').trigger('click'); await flushPromises()
    expect(post).toHaveBeenCalledWith('/mentor/plan-versions/v1/comments', { content: '建议拆分任务' })
  })

  it('授权失效时显示访问错误', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({ data: [{ student_id: 's1', scopes: [], expires_at: '2020-01-01' }] }).mockRejectedValueOnce(new Error('403'))
    const wrapper = mount(MentorStudentsPage); await flushPromises(); await wrapper.get('[data-test="student-s1"]').trigger('click'); await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('授权')
  })
})
