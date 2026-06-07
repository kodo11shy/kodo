// 学生档案详情页
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    studentId: 0,
    student: null,
    editMode: false,
    // 编辑表单
    editForm: {},
    // 接送授权人
    showPickupEditor: false,
    pickups: [],
    editPickups: [],
    // 健康告知
    showHealth: false,
    // 家长
    showParents: false,
    // 加载
    loading: false,
    // 选项卡
    tab: 'info' // info | parents | pickups | health
  },

  onLoad(options) {
    const id = parseInt(options.id || 0)
    if (id) {
      this.setData({ studentId: id })
      this.loadStudent()
    }
  },

  loadStudent() {
    this.setData({ loading: true })
    api.request({ url: '/students/' + this.data.studentId })
      .then((data) => {
        this.setData({ student: this.prepareStudent(data) })
      })
      .catch(() => util.showError('加载失败'))
      .finally(() => this.setData({ loading: false }))
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ tab })
  },

  // ---- 信息编辑 ----
  enterEdit() {
    const s = this.data.student
    this.setData({
      editMode: true,
      editForm: {
        name: s.name || '',
        gender: s.gender || '',
        grade: s.grade || '',
        school_name: s.school_name || '',
        school_class: s.school_class || '',
        pickup_method: s.pickup_method || '',
        address: s.address || '',
        interests: s.interests || '',
        personality: s.personality || '',
        weak_subjects: s.weak_subjects || '',
        notes: s.notes || ''
      }
    })
  },

  onEditField(e) {
    const field = e.currentTarget.dataset.field
    const value = e.detail.value
    this.setData({ ['editForm.' + field]: value })
  },

  saveEdit() {
    util.showLoading('保存中...')
    api.request({
      url: '/students/' + this.data.studentId,
      method: 'PUT',
      data: this.data.editForm
    }).then(() => {
      util.showSuccess('保存成功')
      this.setData({ editMode: false })
      this.loadStudent()
    }).catch((err) => {
      util.showError(err.message || '保存失败')
    }).finally(() => wx.hideLoading())
  },

  cancelEdit() {
    this.setData({ editMode: false })
  },

  prepareStudent(data) {
    const health = data.health || {}
    return {
      ...data,
      initial: (data.name || '').slice(0, 1),
      metaText: (data.grade || '—') + ' · ' + (data.school_name || '—') + ' · ' + (data.school_class || '—'),
      genderText: data.gender || '未知',
      gradeText: data.grade || '—',
      schoolNameText: data.school_name || '—',
      schoolClassText: data.school_class || '—',
      pickupMethodText: data.pickup_method || '—',
      addressText: data.address || '—',
      interestsText: data.interests || '—',
      personalityText: data.personality || '—',
      weakSubjectsText: data.weak_subjects || '—',
      notesText: data.notes || '无',
      parents: (data.parents || []).map((item) => ({
        ...item,
        initial: (item.name || '').slice(0, 1)
      })),
      pickups: (data.pickups || []).map((item) => ({
        ...item,
        initial: (item.name || '').slice(0, 1)
      })),
      healthDisplay: {
        food_allergies: health.food_allergies || '无',
        drug_allergies: health.drug_allergies || '无',
        medical_history: health.medical_history || '无',
        current_meds: health.current_meds || '无',
        special_notes: health.special_notes || '无'
      },
      consentSigned: !!health.consent_signed,
      consentButtonText: health.consent_signed ? '撤销签署' : '标记已签署'
    }
  },

  // ---- 接送授权人 ----
  loadPickups() {
    api.request({ url: '/students/' + this.data.studentId + '/pickups' })
      .then((data) => {
        const list = data.pickups || []
        this.setData({ pickups: list })
      })
  },

  openPickupEditor() {
    this.loadPickups()
    this.setData({
      showPickupEditor: true,
      editPickups: [{
        name: '',
        relation: '',
        phone: '',
        is_default: false
      }]
    })
  },

  addPickupRow() {
    const list = [...this.data.editPickups, { name: '', relation: '', phone: '', id_card: '', is_default: false }]
    this.setData({ editPickups: list })
  },

  removePickupRow(e) {
    const idx = e.currentTarget.dataset.index
    const list = [...this.data.editPickups]
    list.splice(idx, 1)
    this.setData({ editPickups: list })
  },

  onPickupField(e) {
    const field = e.currentTarget.dataset.field
    const idx = parseInt(e.currentTarget.dataset.index)
    const value = e.detail.value
    const key = 'editPickups[' + idx + '].' + field
    this.setData({ [key]: value })
  },

  savePickups() {
    const valid = this.data.editPickups.filter(p => p.name && p.relation && p.phone)
    if (valid.length === 0) {
      util.showError('请至少填写一个完整的授权人')
      return
    }
    util.showLoading('保存中...')
    api.request({
      url: '/students/' + this.data.studentId + '/pickups',
      method: 'PUT',
      data: { pickups: valid }
    }).then(() => {
      util.showSuccess('保存成功')
      this.setData({ showPickupEditor: false })
      this.loadStudent()
    }).catch((err) => {
      util.showError(err.message || '保存失败')
    }).finally(() => wx.hideLoading())
  },

  closePickupEditor() {
    this.setData({ showPickupEditor: false })
  },

  // ---- 健康告知 ----
  toggleHealthConsent() {
    const current = this.data.student ? this.data.student.consentSigned : false
    const action = !current
    wx.showModal({
      title: action ? '签署健康告知书' : '撤销健康告知书',
      content: action ? '确认家长已签署健康告知书？' : '确认撤销已签署的健康告知书？',
      success: (res) => {
        if (res.confirm) {
          util.showLoading('提交中...')
          api.request({
            url: '/students/' + this.data.studentId + '/health/consent',
            method: 'POST',
            data: { signed: action }
          }).then(() => {
            util.showSuccess(action ? '已签署' : '已撤销')
            this.loadStudent()
          }).catch((err) => {
            util.showError(err.message || '操作失败')
          }).finally(() => wx.hideLoading())
        }
      }
    })
  },

  // ---- 家长邀请码 ----
  copyInviteCode(e) {
    const code = e.currentTarget.dataset.code
    wx.setClipboardData({
      data: code,
      success: () => util.showSuccess('邀请码已复制')
    })
  },

  // ---- 导航 ----
  goGrowth() {
    wx.navigateTo({ url: '/pages/teacher/growth/growth?student_id=' + this.data.studentId })
  },

  goHomework() {
    wx.navigateTo({
      url: '/pages/teacher/homework/create/homework-create?student_ids=' + this.data.studentId
    })
  },

  imageUrl(path) {
    return api.imageUrl(path)
  }
})
