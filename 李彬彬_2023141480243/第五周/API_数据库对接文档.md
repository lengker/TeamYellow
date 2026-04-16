# A5 数据库接口对接文档（简版）

## 1. 基本信息

- 服务地址：`http://127.0.0.1:8000`
- 文档页：`http://127.0.0.1:8000/docs`
- 健康检查：`GET /health`
- 请求体格式：`application/json`
- 开发态接口前缀：`/dev/*`（只有 `APP_ENV=development/dev/local` 才可用）
- 服务启动时会自动做“数据库完整性检查”：如果发现缺表，会按依赖顺序自动补建。

## 2. 表 key 一览

接口里 `table_key` 只能是以下 7 个值：

- `airports` -> `LNG_AIRPORTS`（主键 `airport_code`，非自增）
- `users` -> `LNG_USERS`（主键 `user_id`，自增）
- `tracks` -> `LNG_TRACKS`（主键 `track_id`，自增）
- `audio_records` -> `LNG_AUDIO_RECORDS`（主键 `audio_id`，自增）
- `annotations` -> `LNG_ANNOTATIONS`（主键 `annotation_id`，自增）
- `vsp_data` -> `LNG_VSP_DATA`（主键 `vsp_id`，自增）
- `storage_log` -> `LNG_STORAGE_LOG`（主键 `id`，自增）

## 3. 通用 CRUD 接口（稳定）

这些是基础接口

### 3.1 新增一条

- `POST /tables/{table_key}`
- Body：直接传字段对象

示例（新增机场）：

```json
{
  "airport_code": "VHHH",
  "name": "Hong Kong",
  "country_code": "CN",
  "latitude": 22.308,
  "longitude": 113.918
}
```

返回：

```json
{
  "id": "VHHH"
}
```

### 3.2 按主键查一条

- `GET /tables/{table_key}/{item_id}`

### 3.3 列表查询

- `GET /tables/{table_key}?limit=100&offset=0`

### 3.4 按主键更新

- `PUT /tables/{table_key}/{item_id}`
- Body：只传要改的字段

### 3.5 按主键删除

- `DELETE /tables/{table_key}/{item_id}`

## 4. 数据库管理接口（开发态）

> 用于测试、调试、前端管理页联动，不建议生产环境开放。

### 4.1 表快照

- `GET /dev/db-ui/snapshot?limit=100`
- 返回每张表是否存在、字段、数据（最多 `limit` 条）

### 4.2 级联删表

- `POST /dev/db-ui/drop/{table_key}`
- 规则：删除该表及其下级依赖表（`DROP TABLE`）

### 4.3 级联建表

- `POST /dev/db-ui/ensure/{table_key}`
- 规则：先确保上级依赖表存在，再建当前表（已存在会跳过）

### 4.4 启动时数据库级联检查（给后端同学）

这部分是对接重点：后端服务**每次启动**都要确保 7 张表是完整的。

- 当前项目已经内置该逻辑（应用启动时自动执行）。
- 检查方式：查询 `sqlite_master` 看表是否存在。
- 修复方式：缺哪张就按依赖顺序补建，不会重复建已存在的表。
- 所以你们对接时，正常启动服务即可，不需要手动先建库。

若你们后续拆成别的服务，也请保留同样逻辑，伪代码如下：

```python
with get_connection() as conn:
    initialize_database(conn)  # 缺表自动补齐，已存在则跳过
```

## 5. 行级 CRUD 测试接口（开发态）

这组是管理页弹窗直接用的接口，后端联调也可以直接调。

---

### 5.1 新增一条（带业务规则）

- `POST /dev/db-ui/rows/create/{table_key}`
- Body：

```json
{
  "values": {
    "field_a": "value_a"
  }
}
```

也支持直接传字段对象（不包 `values`）。

返回：

```json
{
  "id": 123
}
```

---

### 5.2 删除一条（按主键）

- `POST /dev/db-ui/rows/delete/{table_key}`
- Body：

```json
{
  "id": 123
}
```

返回：

```json
{
  "deleted": true,
  "id": 123
}
```

---

### 5.3 条件查找

- `POST /dev/db-ui/rows/search/{table_key}`
- Body：

```json
{
  "filters": {
    "field_a": "value_a",
    "field_b": 1
  },
  "limit": 200
}
```

说明：

- `filters` 可空；空时等于全查。
- 主键条件会被忽略（本接口不支持按主键查）。

返回：

```json
{
  "rows": [
    {
      "id": 1
    }
  ]
}
```

---

### 5.4 更新一条

- `POST /dev/db-ui/rows/update/{table_key}`
- Body：

```json
{
  "id": 123,
  "new_id": null,
  "values": {
    "field_a": "new_value"
  }
}
```

说明：

- `id`：要更新的“旧主键”。
- `new_id`：仅 `airports` 使用（可选），用于改主键 `airport_code`。
- 其他表不允许改主键，`new_id` 会被忽略。

返回：

```json
{
  "updated": true,
  "id": 123
}
```

## 6. 关键业务规则（联调必须知道）

### 6.1 主键输入规则

- `airports`：新增时要传 `airport_code`。
- 其他 6 张表：主键是自增，新增时不要传主键。

### 6.2 时间字段自动维护

- `audio_records.last_access_at`：在以下操作会自动更新为当前时间：
  - `rows/create/audio_records`
  - `rows/update/audio_records`
  - `rows/search/audio_records`（命中行会更新）
- `annotations.annotation_time`：在以下操作会自动更新：
  - `rows/create/annotations`
  - `rows/update/annotations`

### 6.3 删除联动规则

- 删除父数据时会递归删下游数据（应用层处理）。
- 删除 `audio_records` 行时，会额外写入一条 `LNG_STORAGE_LOG`：
  - `action_type = "CLEANUP"`
  - `target_file_id = audio_id`
  - `released_space = 0`
  - `op_time = 当前时间`
- 不强制“主键连续重排”，只保证后续继续自增。

### 6.4 airports 主键更新级联

当调用 `rows/update/airports` 且 `new_id` 不为空时，会同步更新：

- `LNG_TRACKS.departure_airport_code`
- `LNG_TRACKS.arrival_airport_code`
- `LNG_VSP_DATA.airport_code`

## 7. 常见错误码

- `400`：参数不合法、外键约束失败、业务规则错误
- `403`：当前不是开发环境，但调用了 `/dev/*`
- `404`：`table_key` 不存在或数据不存在

错误返回统一示例：

```json
{
  "detail": "错误原因描述"
}
```

## 8. 快速联调示例（推荐）

### 8.1 新增一条音频

`POST /dev/db-ui/rows/create/audio_records`

```json
{
  "values": {
    "source_url": "https://example.com/a.wav",
    "start_time_utc": "2026-04-07T12:00:00Z",
    "end_time_utc": "2026-04-07T12:10:00Z",
    "duration_ms": 600000,
    "file_name": "a.wav",
    "file_path": "/tmp/a.wav",
    "track_id": 1
  }
}
```

### 8.2 查找音频（空条件全查）

`POST /dev/db-ui/rows/search/audio_records`

```json
{
  "filters": {}
}
```

### 8.3 删除音频（会写 storage_log）

`POST /dev/db-ui/rows/delete/audio_records`

```json
{
  "id": 1
}
```

### 8.4 更新机场主键

`POST /dev/db-ui/rows/update/airports`

```json
{
  "id": "VHHH",
  "new_id": "VHHX",
  "values": {
    "name": "Hong Kong X"
  }
}
```

