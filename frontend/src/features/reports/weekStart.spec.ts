import { describe, expect, it } from 'vitest'

import { weekStartInTimeZone } from './weekStart'

describe('自然周起点', () => {
  it('上海周一凌晨不会被 UTC 转换成周日', () => {
    const shanghaiMonday = new Date('2026-11-01T16:30:00Z')

    expect(weekStartInTimeZone(shanghaiMonday, 'Asia/Shanghai')).toBe('2026-11-02')
  })
})
