// 关于页
const api = require('../../../utils/api')

Page({
  data: {
    appName: '智慧托班',
    version: '1.0.0',
    config: null
  },

  onLoad() {
    this.loadConfig()
  },

  loadConfig() {
    api.request({ url: '/config' })
      .then((data) => {
        this.setData({ config: data })
      })
      .catch(() => {
        // 静默失败，仅显示默认信息
      })
  },

  // 查看隐私政策（示例 H5）
  goPrivacy() {
    wx.navigateTo({
      url: '/pages/common/webview/webview?url=' + encodeURIComponent('https://tuoban.example.com/privacy') + '&title=' + encodeURIComponent('隐私政策')
    })
  },

  // 查看用户协议
  goTerms() {
    wx.navigateTo({
      url: '/pages/common/webview/webview?url=' + encodeURIComponent('https://tuoban.example.com/terms') + '&title=' + encodeURIComponent('用户协议')
    })
  },

  // 联系客服
  contact() {
    wx.showModal({
      title: '联系客服',
      content: '客服电话：138-0000-0000',
      confirmText: '拨打',
      success: (res) => {
        if (res.confirm) {
          wx.makePhoneCall({ phoneNumber: '13800000000' })
        }
      }
    })
  },

  onShareAppMessage() {
    return {
      title: '智慧托班管理系统',
      path: '/pages/index/index'
    }
  }
})
