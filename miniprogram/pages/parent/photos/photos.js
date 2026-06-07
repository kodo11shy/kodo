// 家长端照片墙 - 支持下载保存
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    studentId: 0,
    studentName: '',
    photos: [],
    loading: false,
    // 全屏预览
    previewing: false,
    previewUrl: '',
    previewRemark: ''
  },

  onLoad(options) {
    const studentId = parseInt(options.student_id) || 0
    const studentName = decodeURIComponent(options.name || '孩子')
    this.setData({ studentId, studentName })
  },

  onShow() {
    this.loadPhotos()
  },

  onPullDownRefresh() {
    this.loadPhotos().finally(() => wx.stopPullDownRefresh())
  },

  loadPhotos() {
    if (!this.data.studentId) return
    this.setData({ loading: true })
    return api.request({ url: '/parent/photos/' + this.data.studentId })
      .then((data) => {
        const photos = (data.photos || []).map(p => ({
          ...p,
          imageUrl: api.imageUrl(p.file_path),
          typeLabel: this.getTypeLabel(p.photo_type),
          timeStr: util.formatTime(p.taken_at)
        }))
        this.setData({ photos })
      })
      .catch((err) => {
        util.showError(err.message || '加载失败')
      })
      .finally(() => this.setData({ loading: false }))
  },

  getTypeLabel(type) {
    const map = {
      general: '日常',
      activity: '活动',
      homework: '作业',
      meal: '餐食',
      daily: '生活'
    }
    return map[type] || type || '日常'
  },

  // 预览照片
  previewPhoto(e) {
    const idx = e.currentTarget.dataset.index
    const photo = this.data.photos[idx]
    if (!photo) return
    this.setData({
      previewing: true,
      previewUrl: photo.imageUrl,
      previewRemark: photo.remark || ''
    })
  },

  // 关闭预览
  closePreview() {
    this.setData({ previewing: false, previewUrl: '' })
  },

  // 下滑关闭预览
  onPreviewTouchMove() {},

  // 长按保存到相册
  savePhoto(e) {
    const idx = e.currentTarget.dataset.index
    const photo = this.data.photos[idx]
    if (!photo) return
    this._downloadAndSave(photo.imageUrl, photo.remark || '照片')
  },

  // 预览时保存
  savePreviewPhoto() {
    if (this.data.previewUrl) {
      this._downloadAndSave(this.data.previewUrl, '照片')
    }
  },

  _downloadAndSave(url, label) {
    wx.showLoading({ title: '保存中...' })
    wx.downloadFile({
      url: url,
      success: (res) => {
        wx.saveImageToPhotosAlbum({
          filePath: res.tempFilePath,
          success: () => util.showSuccess((label || '照片') + '已保存'),
          fail: () => util.showError('保存失败，请检查相册权限')
        })
      },
      fail: () => util.showError('下载失败'),
      complete: () => wx.hideLoading()
    })
  }
})
