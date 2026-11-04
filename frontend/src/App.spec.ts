import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import App from './App.vue'

describe('应用壳层', () => {
  it('显示系统名称', () => {
    // 删除或误改系统主标题时必须失败，登录页和浏览器标题依赖统一名称。
    const wrapper = mount(App)

    expect(wrapper.text()).toContain('AI智能体大学生职业生涯规划系统')
  })
})
