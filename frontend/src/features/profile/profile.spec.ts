import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { http } from '../../app/http'
import PrivacyPage from './PrivacyPage.vue'
import ProfilePage from './ProfilePage.vue'

describe('学生档案与隐私授权', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('加载并保存档案，同时校验每周可用时间', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      data: { department: '计算机学院', major: '软件工程', grade_level: '大二', gpa: 3.5, available_hours: 10, constraints: [] },
    })
    const put = vi.spyOn(http, 'put').mockResolvedValue({ data: {} })
    const wrapper = mount(ProfilePage)
    await flushPromises()

    await wrapper.get('[data-test="hours"]').setValue('169')
    await wrapper.get('form').trigger('submit')
    expect(wrapper.get('[role="alert"]').text()).toContain('168')

    await wrapper.get('[data-test="hours"]').setValue('8')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(put).toHaveBeenCalledWith('/profiles/me', expect.objectContaining({ available_hours: 8 }))
  })

  it('创建并撤销导师授权', async () => {
    const grant = { id: 'grant-1', mentor_id: '11111111-1111-4111-8111-111111111111', scopes: ['profile'], expires_at: '2027-01-01T00:00:00Z' }
    vi.spyOn(http, 'post').mockResolvedValue({ data: grant })
    const remove = vi.spyOn(http, 'delete').mockResolvedValue({ data: undefined })
    const wrapper = mount(PrivacyPage)

    await wrapper.get('[data-test="mentor-id"]').setValue(grant.mentor_id)
    await wrapper.get('[data-test="expires-at"]').setValue('2027-01-01T00:00')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('11111111')

    await wrapper.get('[data-test="revoke"]').trigger('click')
    await flushPromises()
    expect(remove).toHaveBeenCalledWith('/consents/mentor-grants/grant-1')
    expect(wrapper.text()).not.toContain('11111111')
  })
})
