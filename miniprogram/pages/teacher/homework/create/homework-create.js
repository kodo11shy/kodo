// 新建作业页 — 关联签到学生，科目锁定老师学科
const app = getApp()
const api = require('../../../../utils/api')
const util = require('../../../../utils/util')

const FIXED_HOMEWORK_SUBJECTS = ['语文', '数学']

Page({
  data: {
    // 学生相关
    students: [],           // 可选学生列表（已签到 - 已交作业）
    allCheckedIn: [],       // 所有签到学生（用于展示总数）
    submittedCount: 0,      // 已交作业人数
    studentIndex: -1,
    selectedStudent: null,
    // 科目
    subject: '',
    subjectLabel: '',
    subjectDisplay: '未配置',
    isAdmin: false,
    _allSubjects: FIXED_HOMEWORK_SUBJECTS,
    // 作业类型
    homeworkTypes: ['课堂作业', '家庭作业', '练习题', '背诵', '其他'],
    homeworkTypeIndex: 0,
    // 照片
    donePhotos: [],
    donePhotoIds: [],
    remark: '',
    submitting: false,
    canSubmit: false,
    submitText: '📌 暂存，待批改',
    loading: true,
    // 内部状态（存 data 但不用于渲染，避免 Set 序列化问题）
    _submittedIdArr: [],
    _studentNameMap: {}
  },

  onLoad(options) {
    const userInfo = app.globalData.userInfo || {}
    const teacherSubject = userInfo.subject || ''
    const isAdmin = userInfo.role === 'admin'

    this.setData({
      subject: teacherSubject,
      subjectLabel: teacherSubject || '全科',
      subjectDisplay: teacherSubject || '未配置',
      isAdmin
    })

    // 先检查有没有 pre-select
    if (options.photo_id) {
      this.setData({ donePhotoIds: [parseInt(options.photo_id)] })
    }

    // 并行加载
    this._loadAll(teacherSubject)
  },

  _loadAll(teacherSubject) {
    Promise.all([
      this.loadAttendance(),
      this.loadConfig(),
      this.loadTodaysHomework(teacherSubject),
      this.loadStudents()
    ]).then(() => {
      this._filterStudents()
    }).catch(() => {
      // 个别加载失败不影响整体
    }).finally(() => {
      this.setData({ loading: false })
    })
  },

  loadAttendance() {
    return api.request({ url: '/attendance/today' })
      .then((data) => {
        this.setData({ allCheckedIn: data.checked_in || [] })
      })
      .catch(() => {
        this.setData({ allCheckedIn: [] })
      })
  },

  loadConfig() {
    return api.request({ url: '/config', data: { keys: 'homework_types,homework_subjects' } })
      .then((data) => {
        let types = []
        try { types = JSON.parse(data.homework_types || '[]') } catch(e) {}
        this.setData({
          homeworkTypes: types.length > 0 ? types : ['课堂作业', '家庭作业', '练习题', '背诵', '其他'],
          _allSubjects: FIXED_HOMEWORK_SUBJECTS
        })
      })
      .catch(() => {})
  },

  // 加载今日已有的作业（用于排除已交作业的学生）
  loadTodaysHomework(subjectFilter) {
    const params = { page: 1, page_size: 100, homework_date: util.today() }
    if (subjectFilter) {
      params.subject = subjectFilter
    }
    return api.request({ url: '/homework', data: params })
      .then((data) => {
        const records = data.records || []
        // 用数组存已交学生 ID（不用 Set，因为 setData 会序列化）
        const submittedIdArr = records.map(r => r.student_id)
        this.setData({
          _submittedIdArr: submittedIdArr,
          submittedCount: submittedIdArr.length
        })
      })
      .catch(() => {
        this.setData({ _submittedIdArr: [], submittedCount: 0 })
      })
  },

  loadStudents() {
    return api.request({ url: '/students', data: { status: '在读' } })
      .then((data) => {
        const list = data.students || data || []
        const map = {}
        list.forEach(s => { map[s.id] = s.name })
        this.setData({ _studentNameMap: map })
      })
      .catch(() => {})
  },

  // 筛选可选学生：签到中 且 未交作业
  _filterStudents() {
    const checkedIn = this.data.allCheckedIn
    const submittedIdArr = this.data._submittedIdArr || []
    const nameMap = this.data._studentNameMap || {}

    const filtered = checkedIn.filter(s => !submittedIdArr.includes(s.id))
    const students = filtered.map(s => ({
      ...s,
      name: s.name || nameMap[s.id] || ('学生#' + s.id)
    }))

    this.setData({ students })
  },

  onStudentChange(e) {
    const idx = e.detail.value
    this.setData({
      studentIndex: idx,
      selectedStudent: this.data.students[idx]
    })
    this._refreshSubmitState()
  },

  setSubject(e) {
    const subject = e.currentTarget.dataset.subject
    this.setData({ subject, subjectDisplay: subject || '未配置' })
    this._refreshSubmitState()
  },

  onTypeChange(e) {
    this.setData({ homeworkTypeIndex: e.detail.value })
  },

  addDonePhoto() {
    wx.chooseMedia({
      count: 9 - this.data.donePhotos.length,
      mediaType: ['image'],
      sourceType: ['camera', 'album'],
      success: (res) => {
        const files = res.tempFiles.map(f => f.tempFilePath)
        const photos = [...this.data.donePhotos, ...files]
        this.setData({ donePhotos: photos })
        this.uploadPhotos(files)
      }
    })
  },

  uploadPhotos(files) {
    util.showLoading('上传照片...')
    const promises = files.map(file => api.uploadFile(file))
    Promise.all(promises)
      .then((results) => {
        const newIds = results.map(r => r.photo_id)
        this.setData({ donePhotoIds: [...this.data.donePhotoIds, ...newIds] })
        this._refreshSubmitState()
      })
      .catch(() => util.showError('部分照片上传失败'))
      .finally(() => wx.hideLoading())
  },

  removeDonePhoto(e) {
    const idx = e.currentTarget.dataset.index
    const photos = [...this.data.donePhotos]
    const ids = [...this.data.donePhotoIds]
    photos.splice(idx, 1)
    ids.splice(idx, 1)
    this.setData({ donePhotos: photos, donePhotoIds: ids })
    this._refreshSubmitState()
  },

  onRemarkInput(e) {
    this.setData({ remark: e.detail.value })
  },

  submitHomework() {
    if (!this.data.selectedStudent) {
      util.showError('请选择学生')
      return
    }
    if (!this.data.subject) {
      util.showError('请选择科目')
      return
    }
    if (!FIXED_HOMEWORK_SUBJECTS.includes(this.data.subject)) {
      util.showError('作业科目只能是语文或数学')
      return
    }
    if (this.data.donePhotoIds.length === 0) {
      util.showError('请至少拍一张作业照片')
      return
    }

    this.setData({ submitting: true, canSubmit: false, submitText: '提交中...' })

    const today = util.today()
    api.request({
      url: '/homework',
      method: 'POST',
      data: {
        student_id: this.data.selectedStudent.id,
        subject: this.data.subject,
        homework_type: this.data.homeworkTypes[this.data.homeworkTypeIndex],
        photo_ids: this.data.donePhotoIds,
        remark: this.data.remark,
        homework_date: today
      }
    }).then((data) => {
      util.showSuccess('作业已提交')
      wx.redirectTo({
        url: '/pages/teacher/homework/detail/homework-detail?id=' + data.id
      })
    }).catch((err) => {
      util.showError(err.message || '提交失败')
    }).finally(() => {
      this.setData({ submitting: false })
      this._refreshSubmitState()
    })
  },

  _refreshSubmitState() {
    const canSubmit = !!this.data.selectedStudent &&
      !!this.data.subject &&
      this.data.donePhotoIds.length > 0 &&
      !this.data.submitting
    this.setData({
      canSubmit,
      submitText: this.data.submitting ? '提交中...' : '📌 暂存，待批改'
    })
  }
})
