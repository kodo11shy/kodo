// 家长端照片墙 - 支持下载保存
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    studentId: 0,
    studentName: '',
    photos: [],
    loading: false,
    page: 1,
    pageSize: 30,
    hasMore: true,
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
    this.loadPhotos(true)
  },

  onPullDownRefresh() {
    this.loadPhotos(true).finally(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadPhotos(false)
    }
  },

  loadPhotos(refresh) {
    if (!this.data.studentId) return
    const page = refresh ? 1 : this.data.page + 1
    this.setData({ loading: true })
    return api.request({
      url: '/parent/photos/' + this.data.studentId,
      data: { page, page_size: this.data.pageSize }
    })
      .then((data) => {
        const newPhotos = (data.photos || []).map(p => ({
          ...p,
          imageUrl: api.imageUrl(p.thumbnail || p.file_path),
          previewUrl: api.imageUrl(p.file_path || p.thumbnail),
          typeLabel: this.getTypeLabel(p.photo_type),
          timeStr: util.formatTime(p.taken_at)
        }))
        const photos = refresh ? newPhotos : this.data.photos.concat(newPhotos)
        const total = data.total || 0
        this.setData({
          photos,
          page,
          hasMore: total ? photos.length < total : newPhotos.length >= this.data.pageSize
        })
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
      previewUrl: photo.previewUrl || photo.imageUrl,
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
    this._downloadAndSave(photo.previewUrl || photo.imageUrl, photo.remark || '照片')
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
