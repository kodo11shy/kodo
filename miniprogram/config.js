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

  // -------- 生产环境（云服务器） --------
  apiBase: 'https://ccrong.cloud/api',
  apiOrigin: 'https://ccrong.cloud',
  apiFallbackBase: 'https://ccrong.cloud/api',
  apiFallbackOrigin: 'https://ccrong.cloud',

}

module.exports = config
