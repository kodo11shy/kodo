const api = require('../../../../utils/api')
const util = require('../../../../utils/util')

Page({
  data: {
    homework: null,
    statusClass: '',
    statusText: '',
    studentNameDisplay: '学生',
    homeworkMetaText: '',
    donePhotos: [],
    gradedPhotos: [],
    correctedPhotos: [],
    scoreOptions: [],
    // 审计信息
    recordedByName: '',
    gradedByName: '',
    correctedByName: '',
    gradedAt: '',
    correctedAt: '',
    auditVisible: false,
    gradeStatusClass: '',
    gradeStatusText: '',
    correctStatusClass: '',
    correctStatusText: '',

    // 批改表单
    score: 0,
    errorCount: 0,
    gradePhotos: [],
    gradePhotoIds: [],
    gradeRemark: '',
    grading: false,
    gradeCanSubmit: false,
    gradeSubmitText: '✅ 保存批改',

    // 改错表单
    correctPhotos: [],
    correctPhotoIds: [],
    correctRemark: '',
    correcting: false,
    correctCanSubmit: false,
    correctSubmitText: '✅ 改错完成'
  },

  onLoad(options) {
    this.setData({ scoreOptions: this.buildScoreOptions(0) })
    const id = options.id
    if (id) this.loadHomework(id)
  },

  loadHomework(id) {
    util.showLoading('加载中...')
    // 用列表接口查询：后端已按 ALLOWED_HOMEWORK_SUBJECTS 过滤，
    // 前端不再重复过滤，通过 id 在结果中匹配
    api.request({ url: '/homework', data: { page_size: 100 } })
      .then((data) => {
        const records = data.records || []
        const hw = records.find(r => r.id == id)
        if (hw) {
          this.setHomework(hw)
        } else {
          util.showError('未找到该作业记录')
        }
      })
      .catch(() => util.showError('加载失败'))
      .finally(() => wx.hideLoading())
  },

  setHomework(hw) {
    const normalizedHomework = { ...hw, status: '已完成' }
    const photos = hw.photos || {}

    // 格式化时间
    const fmt = (t) => t ? util.formatTime(t) : ''

    this.setData({
      homework: normalizedHomework,
      statusText: '已完成',
      statusClass: 'done',
      studentNameDisplay: hw.student_name || '学生',
      homeworkMetaText: (hw.subject || '') + ' · ' + (hw.homework_type || '作业'),
      donePhotos: this.normalizePhotos(photos.done),
      gradedPhotos: this.normalizePhotos(photos.graded),
      correctedPhotos: this.normalizePhotos(photos.corrected),
      scoreOptions: this.buildScoreOptions(this.data.score),
      recordedByName: hw.recorded_by_name || '',
      gradedByName: '',
      correctedByName: '',
      gradedAt: '',
      correctedAt: '',
      auditVisible: !!hw.recorded_by_name,
      gradeStatusClass: 'done-status',
      gradeStatusText: '✅ 已完成',
      correctStatusClass: 'done-status',
      correctStatusText: '✅ 已完成'
    })
  },

  setScore(e) {
    const score = parseInt(e.currentTarget.dataset.score)
    this.setData({ score, scoreOptions: this.buildScoreOptions(score) })
  },

  buildScoreOptions(score) {
    return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((value) => ({
      value,
      active: score >= value
    }))
  },

  normalizePhotos(list) {
    return (list || []).map((item) => {
      const filePath = item.file_path || item
      return {
        ...item,
        file_path: filePath,
        url: api.imageUrl(filePath)
      }
    })
  },

  adjustError(e) {
    const delta = parseInt(e.currentTarget.dataset.delta)
    let count = this.data.errorCount + delta
    if (count < 0) count = 0
    if (count > 99) count = 99
    this.setData({ errorCount: count })
  },

  addGradePhoto() {
    wx.chooseMedia({
      count: 9 - this.data.gradePhotos.length,
      mediaType: ['image'],
      sourceType: ['camera', 'album'],
      success: (res) => {
        const files = res.tempFiles.map(f => f.tempFilePath)
        this.setData({ gradePhotos: [...this.data.gradePhotos, ...files] })
        this.uploadGradePhotos(files)
      }
    })
  },

  uploadGradePhotos(files) {
    util.showLoading('上传中...')
    Promise.all(files.map(f => api.uploadFile(f)))
      .then((results) => {
        this.setData({ gradePhotoIds: [...this.data.gradePhotoIds, ...results.map(r => r.photo_id)] })
        this._refreshActionStates()
      })
      .catch(() => util.showError('部分照片上传失败'))
      .finally(() => wx.hideLoading())
  },

  removeGradePhoto(e) {
    const idx = e.currentTarget.dataset.index
    const photos = [...this.data.gradePhotos]
    const ids = [...this.data.gradePhotoIds]
    photos.splice(idx, 1); ids.splice(idx, 1)
    this.setData({ gradePhotos: photos, gradePhotoIds: ids })
    this._refreshActionStates()
  },

  onGradeRemarkInput(e) {
    this.setData({ gradeRemark: e.detail.value })
  },

  submitGrade() {
    if (this.data.gradePhotoIds.length === 0) {
      util.showError('请至少拍一张批改照片')
      return
    }
    if (this.data.score === 0) {
      util.showError('请评分')
      return
    }
    this.setData({ grading: true, gradeCanSubmit: false, gradeSubmitText: '提交中...' })
    const id = this.data.homework.id
    api.request({
      url: '/homework/' + id + '/grade',
      method: 'PUT',
      data: {
        photo_ids: this.data.gradePhotoIds,
        score: this.data.score,
        error_count: this.data.errorCount,
        remark: this.data.gradeRemark
      }
    }).then(() => {
      util.showSuccess('批改保存成功')
      this.loadHomework(id)
      this.setData({ score: 0, scoreOptions: this.buildScoreOptions(0), errorCount: 0, gradePhotos: [], gradePhotoIds: [], gradeRemark: '' })
    }).catch((err) => {
      util.showError(err.message || '保存失败')
    }).finally(() => {
      this.setData({ grading: false })
      this._refreshActionStates()
    })
  },

  addCorrectPhoto() {
    wx.chooseMedia({
      count: 9 - this.data.correctPhotos.length,
      mediaType: ['image'],
      sourceType: ['camera', 'album'],
      success: (res) => {
        const files = res.tempFiles.map(f => f.tempFilePath)
        this.setData({ correctPhotos: [...this.data.correctPhotos, ...files] })
        this.uploadCorrectPhotos(files)
      }
    })
  },

  uploadCorrectPhotos(files) {
    util.showLoading('上传中...')
    Promise.all(files.map(f => api.uploadFile(f)))
      .then((results) => {
        this.setData({ correctPhotoIds: [...this.data.correctPhotoIds, ...results.map(r => r.photo_id)] })
        this._refreshActionStates()
      })
      .catch(() => util.showError('部分照片上传失败'))
      .finally(() => wx.hideLoading())
  },

  removeCorrectPhoto(e) {
    const idx = e.currentTarget.dataset.index
    const photos = [...this.data.correctPhotos]
    const ids = [...this.data.correctPhotoIds]
    photos.splice(idx, 1); ids.splice(idx, 1)
    this.setData({ correctPhotos: photos, correctPhotoIds: ids })
    this._refreshActionStates()
  },

  onCorrectRemarkInput(e) {
    this.setData({ correctRemark: e.detail.value })
  },

  submitCorrect() {
    if (this.data.correctPhotoIds.length === 0) {
      util.showError('请至少拍一张改错照片')
      return
    }
    this.setData({ correcting: true, correctCanSubmit: false, correctSubmitText: '提交中...' })
    const id = this.data.homework.id
    api.request({
      url: '/homework/' + id + '/correct',
      method: 'PUT',
      data: {
        photo_ids: this.data.correctPhotoIds,
        remark: this.data.correctRemark
      }
    }).then(() => {
      util.showSuccess('改错完成')
      this.loadHomework(id)
      this.setData({ correctPhotos: [], correctPhotoIds: [], correctRemark: '' })
    }).catch((err) => {
      util.showError(err.message || '保存失败')
    }).finally(() => {
      this.setData({ correcting: false })
      this._refreshActionStates()
    })
  },

  previewPhotos(e) {
    const list = e.currentTarget.dataset.list || []
    const index = e.currentTarget.dataset.index || 0
    const urls = list.map(item => item.url || api.imageUrl(item.file_path || item))
    wx.previewImage({ urls, current: urls[index] })
  },

  goBackToList() {
    wx.navigateBack()
  },

  _refreshActionStates() {
    this.setData({
      gradeCanSubmit: this.data.gradePhotoIds.length > 0 && !this.data.grading,
      gradeSubmitText: this.data.grading ? '提交中...' : '✅ 保存批改',
      correctCanSubmit: this.data.correctPhotoIds.length > 0 && !this.data.correcting,
      correctSubmitText: this.data.correcting ? '提交中...' : '✅ 改错完成'
    })
  }
})
