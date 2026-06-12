// 老师登录
const util = require('../../../utils/util')

Page({
  data: {
    phone: '',
    password: '',
    showPassword: false,
    loading: false,
    errorMsg: ''
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

  goBack() {
    wx.navigateBack()
  }
})
