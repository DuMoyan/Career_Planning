import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory } from 'vue-router'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { http, withSingleRefresh } from '../../app/http'
import { createCareerRouter } from '../../app/router'
import { useSessionStore } from '../../app/session'
import LoginPage from './LoginPage.vue'

describe('登录与会话', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.restoreAllMocks()
  })

  it('提交账号密码并保存会话', async () => {
    const post = vi.spyOn(http, 'post').mockResolvedValue({
      data: {
        access_token: 'access-1',
        refresh_token: 'refresh-1',
        role: 'student',
      },
    })
    const router = createCareerRouter(createMemoryHistory(), createPinia())
    const wrapper = mount(LoginPage, { global: { plugins: [router] } })

    await wrapper.get('[data-test="identifier"]').setValue('20260001')
    await wrapper.get('[data-test="password"]').setValue('Career!2026')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(post).toHaveBeenCalledWith('/auth/login', {
      identifier: '20260001',
      password: 'Career!2026',
    })
    expect(localStorage.getItem('career.access_token')).toBe('access-1')
  })

  it('只显示通用登录错误，不泄露账号状态', async () => {
    vi.spyOn(http, 'post').mockRejectedValue(new Error('locked_until=2026-11-04'))
    const pinia = createPinia()
    const router = createCareerRouter(createMemoryHistory(), pinia)
    const wrapper = mount(LoginPage, { global: { plugins: [pinia, router] } })

    await wrapper.get('[data-test="identifier"]').setValue('bad')
    await wrapper.get('[data-test="password"]').setValue('bad')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toBe('登录失败，请检查账号或密码')
    expect(wrapper.text()).not.toContain('locked_until')
  })

  it('401 时只刷新一次并重试原请求', async () => {
    const request = vi.fn().mockRejectedValueOnce({ response: { status: 401 } })
    const retry = vi.fn().mockResolvedValue('ok')
    const refresh = vi.fn().mockResolvedValue(undefined)
    const logout = vi.fn()

    await expect(withSingleRefresh(request, retry, refresh, logout)).resolves.toBe('ok')

    expect(refresh).toHaveBeenCalledTimes(1)
    expect(retry).toHaveBeenCalledTimes(1)
    expect(logout).not.toHaveBeenCalled()
  })

  it('学生不能打开管理员路由，退出后清空会话', async () => {
    const pinia = createPinia()
    setActivePinia(pinia)
    const session = useSessionStore(pinia)
    session.applyTokens({ access_token: 'a', refresh_token: 'r', role: 'student' })
    const router = createCareerRouter(createMemoryHistory(), pinia)

    await router.push('/admin')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('forbidden')

    vi.spyOn(http, 'post').mockResolvedValue({ data: undefined })
    await session.logout()
    expect(session.accessToken).toBeNull()
    expect(localStorage.getItem('career.access_token')).toBeNull()
  })
})
