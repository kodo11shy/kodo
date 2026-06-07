/**
 * 应用配置
 * ==========
 * 部署时只需修改此文件中的地址，无需改动业务代码。
 *
 * 开发环境（默认）：
 *   后端运行在局域网本机，微信开发者工具可访问。
 *
 * 生产环境（部署时取消注释并注释上方配置）：
 *   后端运行在云服务器公网地址。
 */
const config = {

  // -------- 开发环境（本机局域网） --------
  apiBase: 'http://192.168.1.8:8001/api',
  apiOrigin: 'http://192.168.1.8:8001',
  apiFallbackBase: 'http://127.0.0.1:8001/api',
  apiFallbackOrigin: 'http://127.0.0.1:8001',

  // -------- 生产环境（云服务器） --------
  // 部署时取消注释下面两行，注释掉上面的开发配置
  // apiBase: 'https://your-domain.com/api',
  // apiOrigin: 'https://your-domain.com',
  // fallback 可不配或配为同一地址
  // apiFallbackBase: '',
  // apiFallbackOrigin: '',

}

module.exports = config
