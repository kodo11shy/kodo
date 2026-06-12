const app = getApp()

/**
 * 接口请求封装
 * 统一处理 token、错误码、网络异常
 */
const request = (options) => {
  return new Promise((resolve, reject) => {
    const token = app.globalData.token
    const header = {
      'Content-Type': 'application/json'
    }
    if (token) {
      header['Authorization'] = 'Bearer ' + token
    }

    const send = (apiBase, retried = false) => wx.request({
      url: apiBase + options.url,
      method: options.method || 'GET',
      data: options.data || {},
      header: header,
      timeout: 15000,
      success: (res) => {
        if (res.data.code === 0) {
          resolve(res.data.data)
        } else {
          // token 过期，跳回登录
          if (res.data.code === 401) {
            app.logout()
            wx.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
            return
          }
          reject(new Error(res.data.message || '请求失败'))
        }
      },
      fail: (err) => {
        console.error('接口请求失败', apiBase + options.url, err)
        if (!retried && app.globalData.apiFallbackBase && apiBase !== app.globalData.apiFallbackBase) {
          send(app.globalData.apiFallbackBase, true)
          return
        }
        reject(new Error('网络错误：' + err.errMsg))
      }
    })

    send(app.globalData.apiBase)
  })
}

/**
 * 上传文件封装（用于拍照上传）
 */
const uploadFile = (filePath) => {
  return new Promise((resolve, reject) => {
    const token = app.globalData.token
    const upload = (apiBase, retried = false) => wx.uploadFile({
      url: apiBase + '/photos/upload',
      filePath: filePath,
      name: 'file',
      header: {
        'Authorization': 'Bearer ' + token
      },
      success: (res) => {
        try {
          const data = JSON.parse(res.data)
          if (data.code === 0) {
            resolve(data.data)
          } else {
            reject(new Error(data.message || '上传失败'))
          }
        } catch (e) {
          reject(new Error('上传返回格式错误'))
        }
      },
      fail: (err) => {
        console.error('上传请求失败', apiBase + '/photos/upload', err)
        if (!retried && app.globalData.apiFallbackBase && apiBase !== app.globalData.apiFallbackBase) {
          upload(app.globalData.apiFallbackBase, true)
          return
        }
        reject(new Error('上传失败：' + err.errMsg))
      }
    })

    upload(app.globalData.apiBase)
  })
}

/**
 * 图片完整地址
 */
const imageUrl = (filePath) => {
  if (!filePath) return ''
  let normalized = String(filePath).trim().replace(/\\/g, '/')
  if (normalized.startsWith('http')) return normalized

  const uploadIndex = normalized.indexOf('/uploads/')
  if (uploadIndex >= 0) {
    normalized = normalized.slice(uploadIndex)
  } else if (normalized.startsWith('uploads/')) {
    normalized = '/' + normalized
  } else if (!normalized.startsWith('/')) {
    normalized = '/' + normalized
  }

  return app.globalData.apiOrigin + normalized
}

module.exports = {
  request,
  uploadFile,
  imageUrl
}
