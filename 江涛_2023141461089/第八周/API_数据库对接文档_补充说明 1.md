# A5 数据库接口补充说明（待开发）

本文补充两套待开发扩展接口：

1. `LNG_AUDIO_RECORDS` 扩展增删查改
2. `LNG_ANNOTATIONS` 扩展增删查改

路由命名延续现有风格：

- 正式接口：`/tables/{table}/ext/*`
- 开发态接口：`/dev/db-ui/rows/{table}/ext/*`

---

## 1. 接口总体概述

### 1.1 `LNG_AUDIO_RECORDS` 扩展接口

建议路由：

- `POST /tables/audio_records/ext/create`
- `POST /tables/audio_records/ext/delete-chain`
- `POST /tables/audio_records/ext/delete-one`
- `POST /tables/audio_records/ext/search-all`
- `POST /tables/audio_records/ext/search-one`
- `POST /tables/audio_records/ext/update/{item_id}`

开发态对应：

- `POST /dev/db-ui/rows/audio_records/ext/create`
- `POST /dev/db-ui/rows/audio_records/ext/delete-chain`
- `POST /dev/db-ui/rows/audio_records/ext/delete-one`
- `POST /dev/db-ui/rows/audio_records/ext/search-all`
- `POST /dev/db-ui/rows/audio_records/ext/search-one`
- `POST /dev/db-ui/rows/audio_records/ext/update`

大体作用：

- `create`：顺序插入并自动维护同一 `track_id` 下的 `prev_id/next_id` 链
- `delete-chain`：删链中任意一个节点会删除整条链
- `delete-one`：只删除链中单条并重连前后节点
- `search-all`：按条件查找，返回多链/单链聚合数组
- `search-one`：按条件查找，仅返回单链数组；若命中多链则报错
- `update`：仅改单条业务字段，不允许修改 `prev_id/next_id`

### 1.2 `LNG_ANNOTATIONS` 扩展接口

建议路由：

- `POST /tables/annotations/ext/create`
- `POST /tables/annotations/ext/delete-chain`
- `POST /tables/annotations/ext/delete-one`
- `POST /tables/annotations/ext/search-all`
- `POST /tables/annotations/ext/search-one`
- `POST /tables/annotations/ext/update/{item_id}`

开发态对应：

- `POST /dev/db-ui/rows/annotations/ext/create`
- `POST /dev/db-ui/rows/annotations/ext/delete-chain`
- `POST /dev/db-ui/rows/annotations/ext/delete-one`
- `POST /dev/db-ui/rows/annotations/ext/search-all`
- `POST /dev/db-ui/rows/annotations/ext/search-one`
- `POST /dev/db-ui/rows/annotations/ext/update`

大体作用与 `audio_records` 相同，只是作用于 `LNG_ANNOTATIONS` 表。

---

## 2. `LNG_AUDIO_RECORDS` 扩展接口详细说明

## 2.1 `POST /tables/audio_records/ext/create`

- 作用：扩展新增，自动按插入顺序维护链
- 入参：参考 `tracks/ext/create` 风格，支持对象或对象数组
  - 单条：`{...}`
  - 多条：`[{...}, {...}]`
- 单条字段：沿用 `LNG_AUDIO_RECORDS` 当前可写业务字段（不含主键）
- 返回：
  - 单条：`{"id": 101, "audio_id": 101}`
  - 多条：`{"id": 101, "audio_id": [101,102,...]}`
  - 批量：返回数组
- 规则/限制：
  - 后端只允许**顺序追加插入**
  - 当多条记录关联到同一 `track_id` 时，按插入先后更新 `prev_id/next_id` 形成链
  - 不允许在链头或链中间插入
  - 不允许客户端直接指定 `prev_id/next_id`

示例：
```json
[
  {
    "source_url": "https://example.com/a1.wav",
    "start_time_utc": "2026-04-07T12:00:00Z",
    "end_time_utc": "2026-04-07T12:01:00Z",
    "duration_ms": 60000,
    "file_name": "a1.wav",
    "file_path": "/tmp/a1.wav",
    "track_id": 1
  },
  {
    "source_url": "https://example.com/a2.wav",
    "start_time_utc": "2026-04-07T12:01:00Z",
    "end_time_utc": "2026-04-07T12:02:00Z",
    "duration_ms": 60000,
    "file_name": "a2.wav",
    "file_path": "/tmp/a2.wav",
    "track_id": 1
  }
]
```

## 2.2 `POST /tables/audio_records/ext/delete-chain`

- 作用：全删（删整条链）
- 入参：
```json
{"id": 101}
```
- 返回：
```json
{
  "deleted": true,
  "ids": [100, 101, 102],
  "count": 3
}
```
- 规则/限制：
  - `id` 只要是链中任一节点即可
  - 系统向前/向后遍历到链端后删除整链

## 2.3 `POST /tables/audio_records/ext/delete-one`

- 作用：单删（仅删除指定一条）
- 入参：
```json
{"id": 101}
```
- 返回：
```json
{
  "deleted": true,
  "id": 101,
  "prev_id": 100,
  "next_id": 102,
  "relinked": true
}
```
- 规则/限制：
  - 仅删除一条，不删除整链
  - 删除后需维护前后节点链关系：
    - 若同时存在前后节点：`prev.next_id = next_id` 且 `next.prev_id = prev_id`
    - 若删除头节点：后节点 `prev_id = null`
    - 若删除尾节点：前节点 `next_id = null`

## 2.4 `POST /tables/audio_records/ext/search-all`

- 作用：按条件查找（全查模式）
- 入参：
```json
{
  "filters": {
    "track_id": 1
  },
  "limit": 200
}
```
- 返回规则（按“链个数”决定嵌套）：
  - 命中 1 条链：返回该链数组 `[{...},{...}]`
  - 命中多条链：返回二维数组 `[[{...},{...}], [{...}], ...]`
  - 无结果：`[]`
- 规则/限制：
  - 单条记录对象字段为 `LNG_AUDIO_RECORDS` 行字段
  - 每条链内按链顺序（从 `prev_id = null` 开始）返回

## 2.5 `POST /tables/audio_records/ext/search-one`

- 作用：按条件查找（单查模式）
- 入参与 `search-all` 相同
- 返回规则：
  - 命中 1 条链：返回该链数组 `[{...},{...}]`
  - 命中 0 条链：返回 `[]`
  - 命中 >1 条链：返回 400（提示命中多链，不满足单查语义）
- 规则/限制：
  - “单查/全查”针对的是链数量，不是链内记录数量

## 2.6 `POST /tables/audio_records/ext/update/{item_id}`

- 作用：更新指定记录业务字段（不做全链更新）
- 入参：
```json
{
  "values": {
    "status": 1,
    "file_name": "new_name.wav"
  }
}
```
（也支持直接传字段对象）
- 返回：
```json
{
  "updated": true,
  "id": 101
}
```
- 规则/限制：
  - 禁止更新 `prev_id`、`next_id`
  - 不涉及全链联动更新，仅修改当前记录

---

## 3. `LNG_ANNOTATIONS` 扩展接口详细说明

## 3.1 `POST /tables/annotations/ext/create`

- 作用：扩展新增，自动按插入顺序维护链
- 入参：对象或对象数组（参考 `tracks/ext/create` 风格）
- 字段：沿用 `LNG_ANNOTATIONS` 当前可写业务字段（不含主键）
- 返回：
  - 单条：`{"id": 201, "annotation_id": 201}`
  - 多条：`{"id": 201, "annotation_id": [201,202,...]}`
  - 批量：返回数组
- 规则/限制：
  - 后端只允许顺序追加插入
  - 多条记录关联到同一 `audio_id` 时，按插入先后形成 `prev_id/next_id` 链
  - 不允许在链头或链中间插入
  - 不允许客户端直接指定 `prev_id/next_id`

## 3.2 `POST /tables/annotations/ext/delete-chain`

- 作用：全删（删整条链）
- 入参：`{"id": 201}`
- 返回：
```json
{
  "deleted": true,
  "ids": [200, 201, 202],
  "count": 3
}
```
- 规则/限制：链内任一点触发整链删除

## 3.3 `POST /tables/annotations/ext/delete-one`

- 作用：单删（仅删链中一条并维护链）
- 入参：`{"id": 201}`
- 返回：
```json
{
  "deleted": true,
  "id": 201,
  "prev_id": 200,
  "next_id": 202,
  "relinked": true
}
```
- 规则/限制：删除后同步维护前后节点的 `prev_id/next_id`

## 3.4 `POST /tables/annotations/ext/search-all`

- 作用：按条件查找（全查模式）
- 入参：`{"filters": {...}, "limit": 200}`
- 返回规则：
  - 命中 1 条链：`[{...},{...}]`
  - 命中多条链：`[[{...}], [{...},{...}], ...]`
  - 无结果：`[]`
- 规则/限制：按链顺序返回

## 3.5 `POST /tables/annotations/ext/search-one`

- 作用：按条件查找（单查模式）
- 入参与 `search-all` 相同
- 返回规则：
  - 命中 1 条链：`[{...},{...}]`
  - 命中 0 条链：`[]`
  - 命中 >1 条链：400

## 3.6 `POST /tables/annotations/ext/update/{item_id}`

- 作用：更新指定记录业务字段（不做全链更新）
- 入参：
```json
{
  "values": {
    "annotation_text": "new text",
    "is_annotated": 1
  }
}
```
（也支持直接传字段对象）
- 返回：`{"updated": true, "id": 201}`
- 规则/限制：
  - 禁止更新 `prev_id`、`next_id`
  - 仅更新当前记录，不联动全链

---

## 4. 开发态路由对应关系

`audio_records` 扩展接口开发态路由：

- `POST /dev/db-ui/rows/audio_records/ext/create`
- `POST /dev/db-ui/rows/audio_records/ext/delete-chain`
- `POST /dev/db-ui/rows/audio_records/ext/delete-one`
- `POST /dev/db-ui/rows/audio_records/ext/search-all`
- `POST /dev/db-ui/rows/audio_records/ext/search-one`
- `POST /dev/db-ui/rows/audio_records/ext/update`

`annotations` 扩展接口开发态路由：

- `POST /dev/db-ui/rows/annotations/ext/create`
- `POST /dev/db-ui/rows/annotations/ext/delete-chain`
- `POST /dev/db-ui/rows/annotations/ext/delete-one`
- `POST /dev/db-ui/rows/annotations/ext/search-all`
- `POST /dev/db-ui/rows/annotations/ext/search-one`
- `POST /dev/db-ui/rows/annotations/ext/update`

说明：

- 开发态 `update` 延续现有风格，`id` 放在 body 中：
```json
{
  "id": 101,
  "values": {
    "status": 1
  }
}
```

