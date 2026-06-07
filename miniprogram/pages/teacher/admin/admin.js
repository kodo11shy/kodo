// 系统管理（仅管理员可见）
const api = require('../../../utils/api')
const util = require('../../../utils/util')

const FIXED_HOMEWORK_SUBJECTS = ['语文', '数学']

Page({
  data: {
    activeTab: 'teachers',
    // 老师账号
    teachers: [],
    // 作业配置
    homeworkSubjects: FIXED_HOMEWORK_SUBJECTS,
    homeworkTypes: [],
    newHomeworkType: '',
    // 家长绑定
    parentBindings: [],
    // 学生
    students: [],
    // 新建/编辑老师表单
    showForm: false,
    formEditId: null,
    formName: '',
    formPhone: '',
    formPassword: '',
    formRoleIndex: 0,
    roleOptions: ['老师', '管理员'],
    formSubjectIndex: 0,
    formSubjectOptions: ['不限（管理员）', ...FIXED_HOMEWORK_SUBJECTS],
    formLoading: false,
    formCanSave: false,
    formSaveText: '保存',
    // 重置密码
    showResetPwd: false,
    resetPwdId: null,
    resetPwdName: '',
    resetPwdNewPwd: '',
    resetPwdLoading: false,
    authRejected: false
  },

  // 给列表项补充显示字段
  _enrichItems(arr, nameKey) {
    return (arr || []).map(item => {
      const name = item[nameKey || 'name'] || ''
      return {
        ...item,
        avatarChar: name ? name.slice(0,1) : '?',
        displayName: name || '未命名'
      }
    })
  },

  onLoad() {
    this.loadTeachers()
    this.loadHomeworkConfig()
    this.loadStudents()
    this.loadParentBindings()
  },

  _setFormState(extra) {
    const next = extra || {}
    const name = next.formName !== undefined ? next.formName : this.data.formName
    const loading = next.formLoading !== undefined ? next.formLoading : this.data.formLoading
    this.setData({
      ...next,
      formCanSave: !!name && !loading,
      formSaveText: loading ? '保存中...' : '保存'
    })
  },

  _handleAdminError(section, err) {
    console.error(section + ' failed', err)
    const message = err && err.message ? err.message : '加载失败'
    if ((message.indexOf('管理员') >= 0 || message.indexOf('权限') >= 0) && !this.data.authRejected) {
      this.setData({ authRejected: true })
      wx.showModal({
        title: '无权访问',
        content: '系统管理仅管理员可用，请使用管理员账号登录。',
        showCancel: false,
        success: () => wx.navigateBack()
      })
      return
    }
    util.showError(section + '加载失败')
  },

  onPullDownRefresh() {
    Promise.all([
      this.loadTeachers(),
      this.loadHomeworkConfig(),
      this.loadStudents(),
      this.loadParentBindings()
    ]).finally(() => wx.stopPullDownRefresh())
  },

  // ======== Tab 切换 ========

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ activeTab: tab })
  },

  // ======== 数据加载 ========

  loadTeachers() {
    return api.request({ url: '/admin/teachers' })
      .then(data => {
        const teachers = (data.teachers || []).map(t => ({
          id: t.id,
          name: t.name,
          role: t.role,
          subject: t.subject || '',
          teacherDesc: (t.role === 'admin' ? '管理员' : (t.subject ? t.subject + '老师' : '老师')) +
            ' · ' + (t.wechat_bound ? '已绑定' : '未绑定'),
          is_active: t.is_active,
          wechat_bound: !!t.wechat_bound
        }))
        this.setData({ teachers: this._enrichItems(teachers, 'name') })
      })
      .catch(err => {
        this.setData({ teachers: [] })
        this._handleAdminError('老师账号', err)
      })
  },

  loadHomeworkConfig() {
    return api.request({ url: '/config', data: { keys: 'homework_subjects,homework_types' } })
      .then(data => {
        let types = []
        try { types = JSON.parse(data.homework_types || '[]') } catch(e) {}
        this.setData({
          homeworkSubjects: FIXED_HOMEWORK_SUBJECTS,
          homeworkTypes: types,
          formSubjectOptions: ['不限（管理员）', ...FIXED_HOMEWORK_SUBJECTS]
        })
      })
      .catch(() => {
        // 静默失败（可能首次加载没有配置）
      })
  },

  loadParentBindings() {
    return api.request({ url: '/admin/parent-bindings' })
      .then(data => {
        const rows = []
        ;(data.parents || []).forEach(p => {
          const students = p.students || []
          const studentName = students.map(s => s.name).join('、') || '未关联学生'
          const firstActive = (p.bindings || []).find(b => b.is_active)
          const firstBinding = (p.bindings || [])[0]
          rows.push({
            id: firstBinding ? firstBinding.id : 'parent-' + p.id,
            parent_id: p.id,
            parent_name: p.name,
            student_name: studentName,
            student_ids: students.map(s => s.id),
            relation: p.relation || '',
            phone: p.phone || '',
            is_active: firstBinding ? firstBinding.is_active : false,
            wechat_openid: firstActive ? firstActive.wechat_openid : (p.wechat_openid || '')
          })
        })
        this.setData({ parentBindings: this._enrichItems(rows, 'parent_name') })
      })
      .catch(err => {
        this.setData({ parentBindings: [] })
        this._handleAdminError('家长绑定', err)
      })
  },

  loadStudents() {
    return api.request({ url: '/students?status=' })
      .then(data => {
        const students = (data.students || []).map(s => ({
          id: s.id,
          name: s.name,
          grade: s.grade || '',
          school_name: s.school_name || '',
          status: s.status || '在读'
        }))
        this.setData({ students: this._enrichItems(students, 'name') })
      })
      .catch(err => {
        this.setData({ students: [] })
        this._handleAdminError('学生列表', err)
      })
  },

  // ======== 老师账号管理 ========

  showAddTeacher() {
    this._setFormState({
      showForm: true,
      formEditId: null,
      formName: '',
      formPhone: '',
      formPassword: '',
      formRoleIndex: 0,
      formSubjectIndex: 0
    })
  },

  showEditTeacher(e) {
    const id = e.currentTarget.dataset.id
    const teacher = this.data.teachers.find(t => t.id == id)
    if (!teacher) return

    const roleIndex = teacher.role === 'admin' ? 1 : 0
    const subjects = this.data.formSubjectOptions
    let subjectIndex = subjects.indexOf(teacher.subject)
    if (subjectIndex < 0) subjectIndex = 0

    this._setFormState({
      showForm: true,
      formEditId: id,
      formName: teacher.name,
      formPhone: teacher.phone || '',
      formPassword: '',
      formRoleIndex: roleIndex,
      formSubjectIndex: subjectIndex
    })
  },

  onFormName(e) { this._setFormState({ formName: e.detail.value }) },
  onFormPhone(e) { this.setData({ formPhone: e.detail.value }) },
  onFormPassword(e) { this.setData({ formPassword: e.detail.value }) },
  onFormRole(e) { this.setData({ formRoleIndex: e.detail.value }) },
  onFormSubject(e) { this.setData({ formSubjectIndex: e.detail.value }) },

  closeForm() { this.setData({ showForm: false }) },

  _getSubjectValue() {
    const idx = this.data.formSubjectIndex
    const options = this.data.formSubjectOptions
    // 索引0 = "不限（管理员）"
    return idx > 0 && idx < options.length ? options[idx] : null
  },

  saveTeacher() {
    const name = this.data.formName.trim()
    if (!name) { util.showError('请输入姓名'); return }

    const role = this.data.formRoleIndex === 1 ? 'admin' : 'teacher'
    const subject = this._getSubjectValue()

    if (this.data.formEditId) {
      this._setFormState({ formLoading: true })
      const data = { name, role, subject }
      if (this.data.formPhone) data.phone = this.data.formPhone
      api.request({
        url: '/admin/teachers/' + this.data.formEditId,
        method: 'PUT',
        data
      }).then(() => {
        wx.showToast({ title: '已更新', icon: 'success' })
        this._setFormState({ showForm: false, formLoading: false })
        this.loadTeachers()
      }).catch(() => {
        this._setFormState({ formLoading: false })
        util.showError('更新失败')
      })
      return
    }

    const password = this.data.formPassword
    if (!password || password.length < 6) { util.showError('密码至少6位'); return }

    this._setFormState({ formLoading: true })
    const data = { name, password, role, subject }
    if (this.data.formPhone) data.phone = this.data.formPhone
    api.request({
      url: '/admin/teachers',
      method: 'POST',
      data
    }).then(() => {
      wx.showToast({ title: '新建成功', icon: 'success' })
      this._setFormState({ showForm: false, formLoading: false })
      this.loadTeachers()
    }).catch(() => {
      this._setFormState({ formLoading: false })
      util.showError('新建失败')
    })
  },

  confirmDisableTeacher(e) {
    const { id, name } = e.currentTarget.dataset
    wx.showModal({
      title: '禁用老师',
      content: `确定要禁用 ${name} 吗？禁用的老师将无法登录系统。`,
      success: (res) => {
        if (res.confirm) this.disableTeacher(id)
      }
    })
  },

  disableTeacher(id) {
    api.request({
      url: '/admin/teachers/' + id,
      method: 'DELETE'
    }).then(() => {
      wx.showToast({ title: '已禁用', icon: 'success' })
      this.loadTeachers()
    }).catch(() => {
      util.showError('禁用失败')
    })
  },

  enableTeacher(e) {
    const id = e.currentTarget.dataset.id
    api.request({
      url: '/admin/teachers/' + id,
      method: 'PUT',
      data: { is_active: true }
    }).then(() => {
      wx.showToast({ title: '已启用', icon: 'success' })
      this.loadTeachers()
    }).catch(() => {
      util.showError('启用失败')
    })
  },

  showResetPwd(e) {
    const { id, name } = e.currentTarget.dataset
    this.setData({
      showResetPwd: true,
      resetPwdId: id,
      resetPwdName: name,
      resetPwdNewPwd: '',
      resetPwdLoading: false
    })
  },

  closeResetPwd() { this.setData({ showResetPwd: false }) },

  doResetPwd() {
    if (this.data.resetPwdLoading) return
    const id = this.data.resetPwdId
    this.setData({ resetPwdLoading: true })
    api.request({
      url: '/admin/teachers/' + id + '/reset-password',
      method: 'POST',
      data: {}
    }).then(data => {
      const pwd = data.temporary_password || ''
      if (!pwd) {
        util.showError('重置失败')
        this.setData({ resetPwdLoading: false })
        return
      }
      this.setData({ resetPwdNewPwd: pwd, resetPwdLoading: false })
      wx.setClipboardData({
        data: pwd,
        success: () => {
          wx.showToast({ title: '新密码已复制', icon: 'success' })
          this.setData({ showResetPwd: false })
        }
      })
    }).catch(() => {
      this.setData({ resetPwdLoading: false })
      util.showError('重置失败')
    })
  },

  // ======== 作业配置管理 ========

  onNewHomeworkType(e) { this.setData({ newHomeworkType: e.detail.value }) },

  _updateHomeworkConfig(types) {
    const values = {}
    if (types !== null) values.homework_types = JSON.stringify(types)
    return api.request({
      url: '/config',
      method: 'PUT',
      data: { values }
    }).then(() => {
      this.loadHomeworkConfig()
    }).catch(() => {
      util.showError('保存失败')
    })
  },

  addHomeworkType() {
    const name = this.data.newHomeworkType.trim()
    if (!name) return
    if (this.data.homeworkTypes.includes(name)) {
      util.showError('该类型已存在')
      return
    }
    const types = [...this.data.homeworkTypes, name]
    this._updateHomeworkConfig(types)
    this.setData({ newHomeworkType: '' })
  },

  removeHomeworkType(e) {
    const type = e.currentTarget.dataset.type
    wx.showModal({
      title: '删除作业类型',
      content: `确定要删除「${type}」吗？已有作业记录不受影响。`,
      success: (res) => {
        if (res.confirm) {
          const types = this.data.homeworkTypes.filter(t => t !== type)
          this._updateHomeworkConfig(types)
        }
      }
    })
  },

  // ======== 家长绑定管理 ========

  confirmUnbind(e) {
    const { id, name, student } = e.currentTarget.dataset
    wx.showModal({
      title: '解除绑定',
      content: `确定要解除 ${name} 与 ${student} 的绑定吗？解除后家长将无法查看该孩子的数据。`,
      success: (res) => {
        if (res.confirm) this.unbindParent(id)
      }
    })
  },

  unbindParent(bindingId) {
    api.request({
      url: '/admin/parent-bindings/' + bindingId + '/disable',
      method: 'POST'
    }).then(() => {
      wx.showToast({ title: '已解绑', icon: 'success' })
      this.loadParentBindings()
    }).catch(() => {
      util.showError('解绑失败')
    })
  },

  // ======== 学生退班管理 ========

  confirmWithdraw(e) {
    const { id, name } = e.currentTarget.dataset
    wx.showModal({
      title: '确认退班',
      content: `${name} 退班后，该学生的家长将无法查看其数据。确定要退班吗？`,
      success: (res) => {
        if (res.confirm) this.withdrawStudent(id)
      }
    })
  },

  withdrawStudent(id) {
    api.request({
      url: '/admin/students/' + id + '/withdraw',
      method: 'POST'
    }).then(() => {
      wx.showToast({ title: '已退班', icon: 'success' })
      this.loadStudents()
    }).catch(() => {
      util.showError('退班失败')
    })
  },

  // 空操作
  nop() {},

  restoreStudent(e) {
    const { id, name } = e.currentTarget.dataset
    wx.showModal({
      title: '恢复学生',
      content: `确定要恢复 ${name} 的在读状态吗？注意：恢复后不会自动恢复家长的绑定授权。`,
      success: (res) => {
        if (res.confirm) {
          api.request({
            url: '/admin/students/' + id + '/restore',
            method: 'POST'
          }).then(() => {
            wx.showToast({ title: '已恢复', icon: 'success' })
            this.loadStudents()
          }).catch(() => {
            util.showError('恢复失败')
          })
        }
      }
    })
  }
})
