# 全栈编码测评

本项目为个人测评，请勿传播。

## 目录结构

- `A/`：单 SKU 库存预留账本及测试。
- `B/`：仓库拆单分配优化及测试。
- `C/`：Xero 集成评审书面答案，包含官方文档链接。
- `app/backend/`：FastAPI 商品与购物车接口及 API 测试。
- `app/frontend/`：React + TypeScript 商品详情页。

## 运行环境

需要 Python 3.11+ 和 Node 20+。

## API 详细接口文档

### `GET /api/products/trail-jacket`

返回商品基础信息、两个规格维度及服务端管理的 SKU 信息：`id`、以分为单位的价格、实时库存和图片 URL。没有对应 SKU 的组合为无效组合；`available_quantity: 0` 的 SKU 合法但已售罄。

### `POST /api/cart/items`

请求头：`Idempotency-Key: <唯一请求键>`

```json
{"sku_id":"ocean-m","quantity":1}
```

服务端自行查询 SKU、价格与库存，不信任客户端传入的价格或库存。首次成功返回 `201`；缺少幂等键或参数不合法返回 `400`；SKU 不存在返回 `404`；库存不足或用同一幂等键提交了不同请求返回 `409`。使用同一键、同一请求体重试时，服务端返回原结果且不会再次加购或扣减库存。

### `GET /api/cart`

返回购物车明细与商品总数量。