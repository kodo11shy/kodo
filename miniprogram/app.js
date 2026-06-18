const config = require('./config')
const { HOMEWORK_SUBJECTS } = require('./utils/constants')

const DEFAULT_LOGIN_POLICY = {
  teacher_login_mode: 'duration',
  teacher_login_remember_hours: 2
}

const normalizeLoginPolicy = (policy = {}) => {
  const mode = ['always', 'duration', 'remember'].includes(policy.teacher_login_mode)
    ? policy.teacher_login_mode
    : DEFAULT_LOGIN_POLICY.teacher_login_mode
  const rawHours = parseInt(policy.teacher_login_remember_hours, 10)
  const hours = Number.isFinite(rawHours) && rawHours > 0
    ? Math.min(rawHours, 24 * 30)
    : DEFAULT_LOGIN_POLICY.teacher_login_remember_hours
  return {
    teacher_login_mode: mode,
    teacher_login_remember_hours: hours
  }
}

App({
  globalData: {
    userInfo: null,
    userType: '',
    studentIds: [],
    token: '',
    apiBase: config.apiBase,
    apiOrigin: config.apiOrigin,
    apiFallbackBase: config.apiFallbackBase,
    apiFallbackOrigin: config.apiFallbackOrigin,
    loginPolicy: DEFAULT_LOGIN_POLICY,
    homeworkSubjects: HOMEWORK_SUBJECTS
  },

  onLaunch() {
    const storedPolicy = wx.getStorageSync('loginPolicy')
    this.globalData.loginPolicy = normalizeLoginPolicy(storedPolicy)

    const token = wx.getStorageSync('token')
    const userType = wx.getStorageSync('userType')
    if (token && userType === 'parent') {
      this.globalData.token = token
      this.globalData.userType = 'parent'
      this.globalData.studentIds = wx.getStorageSync('studentIds') || []
    } else if (token && userType === 'teacher' && this._canRestoreTeacherSession()) {
      this.globalData.token = token
      this.globalData.userType = 'teacher'
      this.globalData.userInfo = wx.getStorageSync('userInfo') || null
      this.globalData.studentIds = []
    } else {
      this._clearStoredSession()
    }

    this.loadLoginPolicy()
    this.loadHomeworkSubjects()
  },

  loadLoginPolicy() {
    return new Promise((resolve) => {
      const send = (apiBase, retried = false) => wx.request({
        url: apiBase + '/auth/login-policy',
        method: 'GET',
        timeout: 15000,
        success: (res) => {
          if (res.data && res.data.code === 0) {
            const policy = normalizeLoginPolicy(res.data.data)
            this.setLoginPolicy(policy)
            resolve(policy)
            return
          }
          resolve(this.globalData.loginPolicy)
        },
        fail: () => {
          if (!retried && this.globalData.apiFallbackBase && apiBase !== this.globalData.apiFallbackBase) {
            send(this.globalData.apiFallbackBase, true)
            return
          }
          resolve(this.globalData.loginPolicy)
        }
      })

      send(this.globalData.apiBase)
    })
  },

  loadHomeworkSubjects() {
    const { loadHomeworkSubjects } = require('./utils/constants')
    const send = (apiBase) => wx.request({
      url: apiBase + '/config?keys=homework_subjects',
      method: 'GET',
      timeout: 10000,
      success: (res) => {
        if (res.data && res.data.code === 0) {
          const raw = res.data.data.homework_subjects
          let subjects = []
          try { subjects = JSON.parse(raw) } catch (e) { subjects = [] }
          this.globalData.homeworkSubjects = loadHomeworkSubjects({ homework_subjects: subjects })
        }
      },
      fail: () => {}
    })
    send(this.globalData.apiBase)
  },

  setLoginPolicy(policy) {
    const normalized = normalizeLoginPolicy(policy)
    this.globalData.loginPolicy = normalized
    wx.setStorageSync('loginPolicy', normalized)
    return normalized
  },

  isTeacherLoggedIn() {
    return this.globalData.userType === 'teacher' && !!this.globalData.token
  },

  login(phone, password) {
    return new Promise((resolve, reject) => {
      const send = (apiBase, retried = false) => wx.request({
        url: apiBase + '/auth/teacher/login',
        method: 'POST',
        data: { phone, password },
        timeout: 15000,
        success: (res) => {
          if (res.data.code === 0) {
            const { token, teacher } = res.data.data
            this._applyTeacherSession(token, teacher)
            resolve(teacher)
          } else {
            reject(new Error(res.data.message || '登录失败'))
          }
        },
        fail: (err) => {
          console.error('登录请求失败', apiBase + '/auth/teacher/login', err)
          if (!retried && this.globalData.apiFallbackBase && apiBase !== this.globalData.apiFallbackBase) {
            send(this.globalData.apiFallbackBase, true)
            return
          }
          reject(new Error('网络错误：' + err.errMsg))
        }
      })

      send(this.globalData.apiBase)
    })
  },

  loginWithTeacherWechat() {
    return this.getWechatOpenid()
      .then((openid) => new Promise((resolve, reject) => {
        const send = (apiBase, retried = false) => wx.request({
          url: apiBase + '/auth/teacher/wechat-login',
          method: 'POST',
          data: { openid },
          timeout: 15000,
          success: (res) => {
            if (res.data.code === 0) {
              const { token, teacher } = res.data.data
              this._applyTeacherSession(token, teacher)
              resolve(teacher)
            } else {
              reject(new Error(res.data.message || '微信登录失败'))
            }
          },
          fail: (err) => {
            if (!retried && this.globalData.apiFallbackBase && apiBase !== this.globalData.apiFallbackBase) {
              send(this.globalData.apiFallbackBase, true)
              return
            }
            reject(new Error('网络错误：' + err.errMsg))
          }
        })

        send(this.globalData.apiBase)
      }))
  },

  bindCurrentTeacherWechat() {
    return this.getWechatOpenid()
      .then((openid) => new Promise((resolve, reject) => {
        const send = (apiBase, retried = false) => wx.request({
          url: apiBase + '/auth/teacher/bind-wechat',
          method: 'POST',
          data: { openid },
          timeout: 15000,
          header: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + this.globalData.token
          },
          success: (res) => {
            if (res.data.code === 0) {
              const userInfo = { ...(this.globalData.userInfo || {}), wechat_bound: true }
              this.globalData.userInfo = userInfo
              if (this.globalData.userType === 'teacher' && wx.getStorageSync('userType') === 'teacher') {
                wx.setStorageSync('userInfo', userInfo)
              }
              resolve(res.data.data)
            } else {
              reject(new Error(res.data.message || '绑定失败'))
            }
          },
          fail: (err) => {
            if (!retried && this.globalData.apiFallbackBase && apiBase !== this.globalData.apiFallbackBase) {
              send(this.globalData.apiFallbackBase, true)
              return
            }
            reject(new Error('网络错误：' + err.errMsg))
          }
        })

        send(this.globalData.apiBase)
      }))
  },

  getWechatOpenid() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: (loginRes) => {
          if (!loginRes.code) {
            reject(new Error('微信登录失败，请重试'))
            return
          }
          const send = (apiBase, retried = false) => wx.request({
            url: apiBase + '/auth/wechat/session',
            method: 'POST',
            data: { code: loginRes.code, mock_openid: this._getStableMockOpenid() },
            timeout: 15000,
            success: (res) => {
              if (res.data.code === 0 && res.data.data.openid) {
                resolve(res.data.data.openid)
                return
              }
              reject(new Error((res.data && res.data.message) || '未获取到微信身份'))
            },
            fail: (err) => {
              if (!retried && this.globalData.apiFallbackBase && apiBase !== this.globalData.apiFallbackBase) {
                send(this.globalData.apiFallbackBase, true)
                return
              }
              reject(new Error('微信登录失败：' + err.errMsg))
            }
          })

          send(this.globalData.apiBase)
        },
        fail: () => reject(new Error('微信登录失败，请检查网络'))
      })
    })
  },

  _getStableMockOpenid() {
    let openid = wx.getStorageSync('mockOpenid')
    if (!openid) {
      openid = 'mock_' + Date.now() + '_' + Math.floor(Math.random() * 1000000)
      wx.setStorageSync('mockOpenid', openid)
    }
    return openid
  },

  _applyTeacherSession(token, teacher) {
    this.globalData.token = token
    this.globalData.userInfo = teacher
    this.globalData.userType = 'teacher'
    this.globalData.studentIds = []

    const policy = normalizeLoginPolicy(this.globalData.loginPolicy)
    wx.removeStorageSync('studentIds')
    if (policy.teacher_login_mode === 'always') {
      wx.removeStorageSync('token')
      wx.removeStorageSync('userInfo')
      wx.removeStorageSync('userType')
      wx.removeStorageSync('teacherLoginExpiresAt')
      return
    }

    wx.setStorageSync('token', token)
    wx.setStorageSync('userInfo', teacher)
    wx.setStorageSync('userType', 'teacher')
    if (policy.teacher_login_mode === 'duration') {
      const expiresAt = Date.now() + policy.teacher_login_remember_hours * 60 * 60 * 1000
      wx.setStorageSync('teacherLoginExpiresAt', expiresAt)
    } else {
      wx.removeStorageSync('teacherLoginExpiresAt')
    }
  },

  _canRestoreTeacherSession() {
    const policy = normalizeLoginPolicy(this.globalData.loginPolicy)
    if (policy.teacher_login_mode === 'always') return false
    if (policy.teacher_login_mode === 'remember') return true
    const expiresAt = Number(wx.getStorageSync('teacherLoginExpiresAt') || 0)
    return expiresAt > Date.now()
  },

  _clearStoredSession() {
    wx.removeStorageSync('token')
    wx.removeStorageSync('userInfo')
    wx.removeStorageSync('userType')
    wx.removeStorageSync('studentIds')
    wx.removeStorageSync('teacherLoginExpiresAt')
  },

  // 全局退出
  logout() {
    this.globalData.token = ''
    this.globalData.userInfo = null
    this.globalData.userType = ''
    this.globalData.studentIds = []
    this._clearStoredSession()
    wx.reLaunch({ url: '/pages/index/index' })
  }
})
