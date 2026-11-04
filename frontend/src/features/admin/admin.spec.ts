import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { http } from '../../app/http'
import AdminOverviewPage from './AdminOverviewPage.vue'

describe('管理员只读总览', () => {
  it('提供岗位、量表版本和审计三个只读页签', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({ data: { targets: ['software-engineer'], scale_versions: ['demo-riasec@1.0'], audits: [{ id: 'a1', event_type: 'login', result: 'success' }] } })
    const wrapper = mount(AdminOverviewPage); await flushPromises()
    expect(wrapper.text()).toContain('岗位目录'); expect(wrapper.text()).toContain('量表版本'); expect(wrapper.text()).toContain('审计日志')
    expect(wrapper.text()).toContain('software-engineer'); expect(wrapper.text()).toContain('demo-riasec@1.0'); expect(wrapper.text()).toContain('login')
  })
})
