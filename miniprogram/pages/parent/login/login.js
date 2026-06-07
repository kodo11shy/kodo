const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: { inviteCode: '', loading: false, errorMsg: '', devOpenid: '' },
  onCodeInput(e) { this.setData({ inviteCode: e.detail.value.toUpperCase(), errorMsg: '' }) },
  onDevOpenidInput(e) { this.setData({ devOpenid: e.detail.value }) },
  doBind() {
    if (this.data.inviteCode.length < 4) { this.setData({ errorMsg: '请输入完整的邀请码' }); return }
    this.setData({ loading: true })

    // 开发环境用输入框的 openid，生产环境应调 wx.login 换取 code
    const wechatOpenid = this.data.devOpenid || 'dev-parent-' + Date.now()

    api.request({
      url: '/auth/parent/bind',
      method: 'POST',
      data: { invite_code: this.data.inviteCode, wechat_openid: wechatOpenid }
    }).then((data) => {
      const app = getApp()
      // 存两份：token 用于 API 请求，parentData 用于家长端识别
      app.globalData.token = data.token
      app.globalData.userType = 'parent'
      app.globalData.studentIds = data.student_ids || []
      wx.setStorageSync('token', data.token)
      wx.setStorageSync('userType', 'parent')
      wx.setStorageSync('studentIds', data.student_ids || [])
      util.showSuccess('绑定成功')
      setTimeout(() => wx.redirectTo({ url: '/pages/parent/dashboard/dashboard' }), 500)
    }).catch((err) => {
      this.setData({ errorMsg: err.message || '绑定失败，请检查邀请码' })
    }).finally(() => { this.setData({ loading: false }) })
  },
  goBack() { wx.navigateBack() }
})
