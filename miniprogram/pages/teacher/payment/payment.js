// 收费管理总览页
const api = require('../../../utils/api')
const util = require('../../../utils/util')

Page({
  data: {
    month: '',
    students: [],
    summary: null,
    paymentRows: [],
    filteredRows: [],
    todoRows: [],
    filters: [],
    activeFilter: 'all',
    totalFeeText: '0',
    paidText: '0',
    unpaidText: '0',
    paidCount: 0,
    unpaidCount: 0,
    partialCount: 0,
    uncreatedCount: 0,
    selectedStudentName: '请选择学生',
    showAddPayment: false,
    addForm: {
      student_id: 0,
      fee_type: '托管费',
      amount: '',
      period_start: '',
      period_end: '',
      status: '已缴',
      payment_method: '微信转账',
      remark: ''
    },
    feeTypes: ['托管费', '餐费', '材料费', '活动费', '其他'],
    paymentMethods: ['微信转账', '支付宝', '现金', '银行转账'],
    paymentStatuses: ['已缴', '未缴', '部分缴'],
    submitting: false,
    loading: false
  },

  onLoad() {
    const now = new Date()
    const month = now.getFullYear() + '-' + util.padZero(now.getMonth() + 1)
    this.setData({ month })
    this.loadOverview()
  },

  onShow() {
    if (this.data.month) this.loadOverview()
  },

  loadOverview() {
    this.setData({ loading: true })
    Promise.all([
      api.request({ url: '/students', data: { status: '在读' } }),
      api.request({ url: '/payments/summary', data: { month: this.data.month } })
    ]).then(([studentData, summary]) => {
      const students = studentData.students || []
      const rows = this._buildPaymentRows(students, summary.details || [])
      this._setPaymentOverview(students, summary, rows)
    }).catch(() => {
      util.showError('加载失败')
    }).finally(() => {
      this.setData({ loading: false })
    })
  },

  _buildPaymentRows(students, details) {
    const detailsByStudent = {}
    details.forEach(item => {
      const id = item.student_id
      if (!detailsByStudent[id]) detailsByStudent[id] = []
      detailsByStudent[id].push(item)
    })

    return students.map(student => {
      const records = detailsByStudent[student.id] || []
      const total = records.reduce((sum, item) => sum + Number(item.amount || 0), 0)
      const paid = records
        .filter(item => item.status === '已缴')
        .reduce((sum, item) => sum + Number(item.amount || 0), 0)
      const unpaid = records
        .filter(item => item.status !== '已缴')
        .reduce((sum, item) => sum + Number(item.amount || 0), 0)
      const feeTypes = Array.from(new Set(records.map(item => item.fee_type).filter(Boolean)))

      let status = '未生成账单'
      let statusClass = 'muted'
      if (records.length > 0) {
        if (records.some(item => item.status === '部分缴')) {
          status = '部分缴'
          statusClass = 'warn'
        } else if (records.some(item => item.status === '未缴')) {
          status = '未缴'
          statusClass = 'danger'
        } else {
          status = '已缴'
          statusClass = 'ok'
        }
      }

      return {
        studentId: student.id,
        studentName: student.name,
        initial: (student.name || '').slice(0, 1),
        detailText: (student.grade || '—') + ' · ' + (student.school_name || '—'),
        records,
        recordCount: records.length,
        totalText: this._money(total),
        paidText: this._money(paid),
        unpaidText: this._money(unpaid),
        feeTypeText: feeTypes.length > 0 ? feeTypes.join('、') : '未生成本月账单',
        status,
        statusClass,
        remarkText: this._latestRemark(records)
      }
    })
  },

  _setPaymentOverview(students, summary, rows) {
    const paidCount = rows.filter(row => row.status === '已缴').length
    const unpaidCount = rows.filter(row => row.status === '未缴').length
    const partialCount = rows.filter(row => row.status === '部分缴').length
    const uncreatedCount = rows.filter(row => row.status === '未生成账单').length
    const todoRows = rows.filter(row => row.status !== '已缴')
    const filters = [
      { key: 'all', label: '全部', count: rows.length },
      { key: 'uncreated', label: '未生成', count: uncreatedCount },
      { key: 'unpaid', label: '未缴', count: unpaidCount },
      { key: 'partial', label: '部分缴', count: partialCount },
      { key: 'paid', label: '已缴', count: paidCount }
    ]

    this.setData({
      students,
      summary,
      paymentRows: rows,
      todoRows,
      filters,
      totalFeeText: this._money(summary.total_fee || 0),
      paidText: this._money(summary.paid || 0),
      unpaidText: this._money(summary.unpaid || 0),
      paidCount,
      unpaidCount,
      partialCount,
      uncreatedCount
    })
    this._applyFilter()
  },

  _applyFilter() {
    const filter = this.data.activeFilter
    let rows = this.data.paymentRows
    if (filter === 'uncreated') rows = rows.filter(row => row.status === '未生成账单')
    if (filter === 'unpaid') rows = rows.filter(row => row.status === '未缴')
    if (filter === 'partial') rows = rows.filter(row => row.status === '部分缴')
    if (filter === 'paid') rows = rows.filter(row => row.status === '已缴')
    this.setData({ filteredRows: rows })
  },

  _latestRemark(records) {
    if (!records || records.length === 0) return ''
    const latest = records[0]
    if (latest.remark) return latest.remark
    if (latest.payment_method) return latest.payment_method
    return records.length + ' 条记录'
  },

  _money(value) {
    const num = Number(value || 0)
    if (Number.isInteger(num)) return String(num)
    return num.toFixed(2)
  },

  _monthStart() {
    return this.data.month + '-01'
  },

  _monthEnd() {
    const year = Number(this.data.month.slice(0, 4))
    const month = Number(this.data.month.slice(5, 7))
    const lastDay = new Date(year, month, 0).getDate()
    return this.data.month + '-' + util.padZero(lastDay)
  },

  onMonthChange(e) {
    this.setData({ month: e.detail.value, activeFilter: 'all' })
    this.loadOverview()
  },

  switchFilter(e) {
    const filter = e.currentTarget.dataset.filter
    if (filter === this.data.activeFilter) return
    this.setData({ activeFilter: filter })
    this._applyFilter()
  },

  openAddPayment(e) {
    const studentId = e.currentTarget.dataset.studentId || 0
    const student = this.data.students.find(item => item.id == studentId)
    this.setData({
      showAddPayment: true,
      addForm: {
        student_id: student ? student.id : 0,
        fee_type: '托管费',
        amount: '',
        period_start: this._monthStart(),
        period_end: this._monthEnd(),
        status: '已缴',
        payment_method: '微信转账',
        remark: ''
      },
      selectedStudentName: student ? student.name : '请选择学生'
    })
  },

  closeAddPayment() {
    this.setData({ showAddPayment: false })
  },

  onFormField(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ ['addForm.' + field]: e.detail.value })
  },

  selectStudent(e) {
    const idx = Number(e.detail.value)
    const student = this.data.students[idx] || {}
    this.setData({
      'addForm.student_id': student.id || 0,
      selectedStudentName: student.name || '请选择学生'
    })
  },

  selectFeeType(e) {
    const idx = Number(e.detail.value)
    this.setData({ 'addForm.fee_type': this.data.feeTypes[idx] || '托管费' })
  },

  selectPaymentStatus(e) {
    const idx = Number(e.detail.value)
    this.setData({ 'addForm.status': this.data.paymentStatuses[idx] || '已缴' })
  },

  selectPaymentMethod(e) {
    const idx = Number(e.detail.value)
    this.setData({ 'addForm.payment_method': this.data.paymentMethods[idx] || '微信转账' })
  },

  submitPayment() {
    if (!this.data.addForm.student_id) {
      util.showError('请选择学生')
      return
    }
    if (!this.data.addForm.amount || parseFloat(this.data.addForm.amount) <= 0) {
      util.showError('请输入金额')
      return
    }
    this.setData({ submitting: true })
    api.request({
      url: '/payments',
      method: 'POST',
      data: {
        ...this.data.addForm,
        amount: parseFloat(this.data.addForm.amount)
      }
    }).then(() => {
      util.showSuccess('记一笔成功')
      this.setData({ showAddPayment: false, activeFilter: 'all' })
      this.loadOverview()
    }).catch((err) => {
      util.showError(err.message || '保存失败')
    }).finally(() => this.setData({ submitting: false }))
  },

  nop() {}
})
