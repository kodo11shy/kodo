// 老师登录
const util = require('../../../utils/util')

Page({
  data: {
    phone: '',
    password: '',
    showPassword: false,
    loading: false,
    wechatLoading: false,
    errorMsg: '',
    policyText: ''
  },

  onLoad() {
    const app = getApp()
    if (app.isTeacherLoggedIn()) {
      wx.redirectTo({ url: '/pages/teacher/dashboard/dashboard' })
      return
    }
    this.refreshPolicyText(app.globalData.loginPolicy)
    app.loadLoginPolicy().then((policy) => {
      this.refreshPolicyText(policy)
    })
  },

  onPhoneInput(e) {
    this.setData({
      phone: e.detail.value,
      errorMsg: ''
    })
  },

  onPasswordInput(e) {
    this.setData({
      password: e.detail.value,
      errorMsg: ''
    })
  },

  togglePassword() {
    this.setData({ showPassword: !this.data.showPassword })
  },

  // 登录
  doLogin() {
    const phone = (this.data.phone || '').trim()
    const password = this.data.password
    if (!phone) {
      this.setData({ errorMsg: '请输入账号或手机号' })
      return
    }
    if (!password) {
      this.setData({ errorMsg: '请输入密码' })
      return
    }

    this.setData({ loading: true, errorMsg: '' })

    const app = getApp()
    app.login(phone, password)
      .then(() => {
        util.showSuccess('登录成功')
        setTimeout(() => {
          wx.redirectTo({ url: '/pages/teacher/dashboard/dashboard' })
        }, 500)
      })
      .catch((err) => {
        this.setData({ errorMsg: err.message || '登录失败，请检查账号和密码' })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  doWechatLogin() {
    this.setData({ wechatLoading: true, errorMsg: '' })
    const app = getApp()
    app.loginWithTeacherWechat()
      .then(() => {
        util.showSuccess('登录成功')
        setTimeout(() => {
          wx.redirectTo({ url: '/pages/teacher/dashboard/dashboard' })
        }, 500)
      })
      .catch((err) => {
        this.setData({ errorMsg: err.message || '当前微信尚未绑定老师账号' })
      })
      .finally(() => {
        this.setData({ wechatLoading: false })
      })
  },

  refreshPolicyText(policy) {
    const mode = policy.teacher_login_mode
    const hours = policy.teacher_login_remember_hours || 2
    const textMap = {
      always: '当前设置：每次进入都需要输入账号密码',
      duration: `当前设置：登录后 ${hours} 小时内免重复输入`,
      remember: '当前设置：登录一次后长期记住本机'
    }
    this.setData({ policyText: textMap[mode] || textMap.duration })
  },

  goBack() {
    wx.navigateBack()
  }
})
