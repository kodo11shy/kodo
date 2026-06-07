// 通用 H5 页面（家长端报告、隐私政策等）
Page({
  data: {
    url: ''
  },

  onLoad(options) {
    const url = decodeURIComponent(options.url || '')
    const title = decodeURIComponent(options.title || '详情')
    if (url) {
      this.setData({ url })
      wx.setNavigationBarTitle({ title })
    } else {
      wx.showToast({ title: '缺少 URL 参数', icon: 'none' })
    }
  },

  // 页面分享
  onShareAppMessage() {
    return {
      title: '智慧托班',
      path: '/pages/index/index'
    }
  }
})
