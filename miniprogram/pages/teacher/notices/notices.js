// 通知管理总览页
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    notices: [],
    filteredNotices: [],
    loading: false,
    activeFilter: 'all',
    filters: [],

    // 状态卡
    totalCount: 0,
    pinnedCount: 0,
    activeCount: 0,
    expiredCount: 0,

    // 待处理
    expiringNotices: [],

    // 弹窗
    showForm: false,
    editId: null,
    form: {
      title: '',
      content: '',
      notice_type: '通知',
      is_pinned: false,
      display_start: '',
      display_end: ''
    },
    noticeTypes: ['通知', '放假', '活动', '食谱', '其他'],
    submitting: false,
    formTitle: '发布通知',
    formSubmitText: '发布',

    emptyTitle: '暂无通知',
    emptyDesc: '发布通知后，会显示在首页和家长端'
  },

  onLoad() {
    this.loadNotices()
  },

  onShow() {
    this.loadNotices()
  },

  loadNotices() {
    this.setData({ loading: true })
    api.request({ url: '/notices', data: { page_size: 50 } })
      .then((data) => {
        const rawNotices = data.notices || []
        const notices = rawNotices.map(this._buildNoticeRow)
        this._setOverview(notices)
      })
      .catch(() => {
        util.showError('加载失败')
        this.setData({ notices: [], filteredNotices: [] })
      })
      .finally(() => this.setData({ loading: false }))
  },

  _buildNoticeRow(item) {
    const today = util.today()
    const startDate = item.display_start || ''
    const endDate = item.display_end || ''
    const isActive = (!startDate || startDate <= today) && (!endDate || endDate >= today)
    const isExpired = endDate && endDate < today
    const expiringSoon = endDate && endDate > today && endDate <= util.dateOffset(3)

    return {
      ...item,
      displayStartText: util.formatDate(item.display_start),
      displayEndText: item.display_end ? util.formatDate(item.display_end) : '长期',
      isActive,
      isExpired,
      expiringSoon,
      statusText: isExpired ? '已过期' : expiringSoon ? '即将到期' : isActive ? '生效中' : '未开始',
      statusClass: isExpired ? 'danger' : expiringSoon ? 'warn' : isActive ? 'ok' : 'muted'
    }
  },

  _setOverview(notices) {
    const totalCount = notices.length
    const pinnedCount = notices.filter(n => n.is_pinned).length
    const activeCount = notices.filter(n => n.isActive).length
    const expiredCount = notices.filter(n => n.isExpired).length

    // 即将到期的通知（3天内）
    const expiringNotices = notices
      .filter(n => n.expiringSoon && n.isActive)
      .map(n => ({ id: n.id, title: n.title, endDate: n.displayEndText }))

    const filters = [
      { key: 'all', label: '全部', count: totalCount },
      { key: 'active', label: '生效中', count: activeCount },
      { key: 'expired', label: '已过期', count: expiredCount },
      { key: 'pinned', label: '置顶', count: pinnedCount }
    ].map(item => ({ ...item, className: item.key === this.data.activeFilter ? 'active' : '' }))

    this.setData({
      notices,
      totalCount,
      pinnedCount,
      activeCount,
      expiredCount,
      expiringNotices,
      filters
    })
    this._applyFilter()
  },

  _applyFilter() {
    const filter = this.data.activeFilter
    let list = this.data.notices
    if (filter === 'active') list = list.filter(n => n.isActive && !n.isExpired)
    if (filter === 'expired') list = list.filter(n => n.isExpired)
    if (filter === 'pinned') list = list.filter(n => n.is_pinned)

    const emptyMap = {
      all: ['暂无通知', '发布通知后，会显示在首页和家长端'],
      active: ['暂无生效中的通知', '发布通知并设置生效日期后显示在此'],
      expired: ['暂无已过期的通知', '通知到期后会自动出现在这里'],
      pinned: ['暂无置顶通知', '发布通知时勾选"置顶"后显示在此']
    }
    const empty = emptyMap[filter] || emptyMap.all

    this.setData({
      filteredNotices: list,
      emptyTitle: empty[0],
      emptyDesc: empty[1]
    })
  },

  switchFilter(e) {
    const filter = e.currentTarget.dataset.filter
    if (filter === this.data.activeFilter) return
    this.setData({
      activeFilter: filter,
      filters: this.data.filters.map(item => ({ ...item, className: item.key === filter ? 'active' : '' }))
    })
    this._applyFilter()
  },

  openForm() {
    const today = util.today()
    this.setData({
      showForm: true,
      editId: null,
      formTitle: '发布通知',
      formSubmitText: '发布',
      form: { title: '', content: '', notice_type: '通知', is_pinned: false, display_start: today, display_end: '' }
    })
  },

  openEdit(e) {
    const item = e.currentTarget.dataset.notice
    this.setData({
      showForm: true,
      editId: item.id,
      formTitle: '编辑通知',
      formSubmitText: '更新',
      form: {
        title: item.title || '',
        content: item.content || '',
        notice_type: item.notice_type || '通知',
        is_pinned: item.is_pinned || false,
        display_start: item.display_start || '',
        display_end: item.display_end || ''
      }
    })
  },

  closeForm() {
    this.setData({ showForm: false })
  },

  onFormField(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ ['form.' + field]: e.detail.value })
  },

  selectNoticeType(e) {
    const idx = Number(e.detail.value)
    this.setData({ 'form.notice_type': this.data.noticeTypes[idx] || '通知' })
  },

  togglePinned() {
    this.setData({ 'form.is_pinned': !this.data.form.is_pinned })
  },

  submitNotice() {
    if (!this.data.form.title.trim()) { util.showError('请输入标题'); return }
    if (!this.data.form.content.trim()) { util.showError('请输入内容'); return }
    this.setData({ submitting: true })

    const method = this.data.editId ? 'PUT' : 'POST'
    const url = this.data.editId ? '/notices/' + this.data.editId : '/notices'

    // 空日期字符串转 null，避免后端 date | None 校验失败
    const payload = { ...this.data.form }
    if (payload.display_start === '') payload.display_start = null
    if (payload.display_end === '') payload.display_end = null

    api.request({ url, method, data: payload })
      .then(() => {
        util.showSuccess(this.data.editId ? '更新成功' : '创建成功')
        this.setData({ showForm: false })
        this.loadNotices()
      })
      .catch((err) => util.showError(err.message || '保存失败'))
      .finally(() => this.setData({ submitting: false }))
  },

  deleteNotice(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认删除',
      content: '删除后不可恢复',
      success: (res) => {
        if (res.confirm) {
          api.request({ url: '/notices/' + id, method: 'DELETE' })
            .then(() => {
              util.showSuccess('已删除')
              this.loadNotices()
            })
            .catch((err) => util.showError(err.message || '删除失败'))
        }
      }
    })
  }
})
