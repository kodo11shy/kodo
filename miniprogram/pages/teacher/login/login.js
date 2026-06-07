// 老师登录
const util = require('../../../utils/util')

Page({
  data: {
    password: '',
    showPassword: false,
    loading: false,
    errorMsg: ''
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
    const password = this.data.password
    if (!password) {
      this.setData({ errorMsg: '请输入密码' })
      return
    }

    this.setData({ loading: true, errorMsg: '' })

    const app = getApp()
    app.login(password)
      .then(() => {
        util.showSuccess('登录成功')
        setTimeout(() => {
          wx.redirectTo({ url: '/pages/teacher/dashboard/dashboard' })
        }, 500)
      })
      .catch((err) => {
        this.setData({ errorMsg: err.message || '登录失败，请检查密码' })
      })
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  goBack() {
    wx.navigateBack()
  }
})
