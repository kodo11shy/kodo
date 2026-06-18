const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: { inviteCode: '', loading: false, autoLoading: false, errorMsg: '' },

  // 已绑定过 → 直接跳首页
  onLoad() {
    const token = wx.getStorageSync('token')
    const userType = wx.getStorageSync('userType')
    if (token && userType === 'parent') {
      wx.redirectTo({ url: '/pages/parent/dashboard/dashboard' })
      return
    }
    this.tryAutoLogin()
  },

  onCodeInput(e) { this.setData({ inviteCode: e.detail.value.toUpperCase(), errorMsg: '' }) },
  doBind() {
    if (this.data.inviteCode.length < 4) { this.setData({ errorMsg: '请输入完整的邀请码' }); return }
    this.setData({ loading: true })

    this._getWechatOpenid()
      .then((openid) => api.request({
        url: '/auth/parent/bind',
        method: 'POST',
        data: { invite_code: this.data.inviteCode, wechat_openid: openid }
      }))
      .then((data) => {
        this._applyParentSession(data)
        util.showSuccess('绑定成功')
        setTimeout(() => wx.redirectTo({ url: '/pages/parent/dashboard/dashboard' }), 500)
      }).catch((err) => {
        this.setData({ errorMsg: err.message || '绑定失败，请检查邀请码' })
      }).finally(() => { this.setData({ loading: false }) })
  },
  goBack() { wx.navigateBack() },

  tryAutoLogin() {
    this.setData({ autoLoading: true })
    this._getWechatOpenid()
      .then((openid) => api.request({
        url: '/auth/parent/auto-login',
        data: { wechat_openid: openid }
      }))
      .then((data) => {
        this._applyParentSession(data)
        wx.redirectTo({ url: '/pages/parent/dashboard/dashboard' })
      })
      .catch(() => {
        // 未绑定过的家长继续停留在邀请码页面。
      })
      .finally(() => {
        this.setData({ autoLoading: false })
      })
  },

  _applyParentSession(data) {
    const app = getApp()
    const studentIds = data.student_ids || (data.students || []).map(item => item.id)
    app.globalData.token = data.token
    app.globalData.userType = 'parent'
    app.globalData.studentIds = studentIds
    wx.setStorageSync('token', data.token)
    wx.setStorageSync('userType', 'parent')
    wx.setStorageSync('studentIds', studentIds)
  },

  _getWechatOpenid() {
    return getApp().getWechatOpenid()
  }
})
