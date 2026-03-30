// 生成雪球股票详情页URL
export const getStockUrl = (code) => {
  let prefix
  if (code.startsWith('6')) {
    prefix = 'SH'  // 沪市（含科创板）
  } else if (code.startsWith('8') || code.startsWith('4')) {
    prefix = 'BJ'  // 北交所
  } else {
    prefix = 'SZ'  // 深市（含创业板）
  }
  return `https://xueqiu.com/S/${prefix}${code}`
}