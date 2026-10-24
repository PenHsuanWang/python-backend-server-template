# Python Backend Platform

以 Python 3.11+、FastAPI 建立的模組化後端產品基礎，定位為**共用平台＋依工廠需求的應用模組＋可替換 solution kernel**。平台負責上層協調、決策與資料服務；設備控制層負責執行、硬即時控制與安全連鎖。

範本採 SVG 的分層 package，正式業務註冊清單與演算法預設空白，不預設製程、設備、資料模型、應用流程或演算法。共用能力包含 runtime／lifespan、async 任務調派、MongoDB 連線、本地使用者與 JWT Bearer 驗證、資料權限／匯出契約、kernel 擴充與資源協調。各選用服務需明確啟用。

## 本機空白啟動

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -c requirements.lock -e '.[dev]'
cp .env.example .env
python server.py --reload
```

Windows PowerShell 使用 `.venv\Scripts\Activate.ps1`。也可執行 `uvicorn server:create_app --factory --reload`。預設採 memory 任務後端與單一 API 程序，MongoDB、身份、kernel、匯出及 job 查詢 API 均關閉；只提供健康檢查與 API 文件。

```bash
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
```

文件位於 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)。應用模組、任務、kernel 與匯出資料源清單皆為空，不會自動產生應用端點或資料表。

## 啟動產品開發環境

1. 複製 `.env.example` 為 `.env`。
2. 執行兩次 `openssl rand -hex 32`，將兩個獨立結果分別填入 `.env` 的 `APP_JWT_SECRET`、`MONGO_ROOT_PASSWORD`。
3. 啟動容器：

```bash
docker compose up --build -d
docker compose logs -f api worker
```

Compose 明確啟用 MongoDB 與 identity，使用 RabbitMQ／Redis 分散式任務及 Redis 資源協調。JWT secret 與 MongoDB 密碼未填時會拒絕啟動。沒有內建使用者或預設應用帳密；建立第一個租戶管理員：

```bash
docker compose exec api python manage.py create-admin \
  --tenant-id TENANT --username USERNAME
```

命令互動讀取密碼並確認，不接受把密碼放在 CLI 參數。登入使用 JSON：

```text
POST /api/v1/identity/login
{"tenant_id":"<tenant_id>","username":"<username>","password":"<password>"}
```

前端後續請求帶 `Authorization: Bearer <access_token>`。管理員透過受控的 `/identity/register` 建立同租戶使用者；沒有公開 signup。短效 token 預設 900 秒，每次受保護請求重新檢查 session、使用者狀態與目前權限，登出／停權於後續受保護請求生效。第一版不包含 refresh token、SSO、MFA 或完整角色引擎。

前端可直接整合 [同源 TypeScript JWT client](frontend/auth-client.ts)，token 只留在記憶體，401 時清除，重新整理後重新登入。更多部署、權限、MongoDB 與 kernel 限制見 [產品平台說明](docs/product-platform.md)。

## 專案結構

```text
server.py / worker.py / manage.py
bootstrap/
  config.py / container.py / plugin_loader.py / wiring.py
  components.py / identity.py / worker.py
src/
  api/                   routers, schemas, dependencies, auth, exceptions
  services/              lifecycle, resource_manager, health, observability, concurrency
  application/           use_cases, registry, hierarchy, orchestration + capability packages
  domain/                models, ports, strategy + capability packages
  plugins/               inference, heuristics, interceptors（預設空白）
  infrastructure/        persistence, messaging, locking, downstream, security
  config/                settings, environment, constants
  utils/                 formatting, time_helpers, validation
  shared_models/         dto, schemas, types
frontend/auth-client.ts
```

新增功能在各層以相同 capability 名稱協作；domain 定義模型／ports，application 定義使用案例，plugins 實作演算法，infrastructure 接外部系統，api 處理 HTTP。最後由 `bootstrap/wiring.py` 的明確 initializer 組裝。`ModuleDefinition` 保留為初始化契約，並非舊 `backend/modules` 實體 package。

完整規範見 [module 功能規範](docs/module-spec.md)，舊 Python import 的破壞性變更見 [搬移對照](docs/package-migration.md)。`src` 是實際可匯入的 package，套件安裝同時包含 `src` 與 `bootstrap`。SVG 的 hierarchy/pipeline 擴充位置不預設工廠模型或流程。

## 多程序、async 與資源協調

Uvicorn 的多個 worker 是獨立程序，每個都有自己的 lifespan、模組、MongoDB／HTTP 連線池與 thread pool。程序間共享的工作透過 RabbitMQ／Redis 協調，不能依賴 Python 全域變數。[FastAPI workers](https://fastapi.tiangolo.com/deployment/server-workers/)

Compose 調整 API 程序數：

```bash
APP_WORKERS=4 docker compose up -d --build api
```

本機命令可分別啟動 API 與 Taskiq worker，兩側需使用相同模組版本與佇列設定：

```bash
APP_TASK_BACKEND=distributed APP_RESOURCE_BACKEND=redis python server.py --workers 4
```

```bash
APP_TASK_BACKEND=distributed APP_TASK_CONCURRENCY=8 APP_RESOURCE_BACKEND=redis \
taskiq worker worker:broker \
  --workers 2 --max-async-tasks 8 --ack-type when_saved \
  --wait-tasks-timeout 10
```

`--reload` 與多 worker 不能合用。直接執行 Uvicorn 時，必須自行指定 distributed；factory 無法可靠得知 Uvicorn CLI 的 worker 數。[Uvicorn settings](https://uvicorn.dev/settings/)

async 適合等待 I/O；受限 thread pool 用於阻塞 SDK，CPU 密集 Python 工作需另用 process pool／獨立 worker。增加 async 並行數不等於增加 CPU 核心。[Taskiq CLI](https://taskiq-python.github.io/guide/cli.html)

kernel 共享資源可使用 Redis token lease／heartbeat。失去 lease 會取消可協作的 async 工作並等待清理，但 Python thread 無法強制中止；外部受保護資源仍需 adapter 檢查 fencing token。大型模型／GPU 建議由獨立 kernel worker 或 remote adapter 持有，避免每個 API 程序重複載入。

## 設定入口

全部設定與說明位於 `.env.example`。`APP_` 環境變數優先於 `.env`；`server.py` CLI 可覆寫 host、port、workers、reload。模組專屬設定留在模組自己的設定模型，使用獨立前綴。

| 設定群組 | 主要變數 |
| --- | --- |
| API／runtime | `APP_WORKERS`、`APP_RELOAD`、`APP_THREAD_WORKERS`、`APP_THREAD_QUEUE_SIZE` |
| 任務 | `APP_TASK_BACKEND`、`APP_TASK_CONCURRENCY`、`APP_JOB_TIMEOUT_SECONDS` |
| MongoDB | `APP_MONGO_ENABLED`、`APP_MONGO_URI`、`APP_MONGO_POOL_SIZE` |
| 身份 | `APP_IDENTITY_ENABLED`、`APP_JWT_SECRET`、`APP_ACCESS_TOKEN_SECONDS` |
| Kernel | `APP_KERNEL_API_ENABLED`、`APP_KERNEL_TIMEOUT_SECONDS` |
| 共享資源 | `APP_RESOURCE_BACKEND`、`APP_RESOURCE_LIMITS`、`APP_RESOURCE_LEASE_SECONDS` |
| 匯出 | `APP_EXPORTS_API_ENABLED` |

kernel／匯出 API 開關不會安裝任何實際 kernel 或資料源。job 查詢預設關閉；開啟 kernel API 時會一併提供具 tenant／owner 保護的 job 查詢。正式環境的 job API 必須啟用 identity；自訂任務提交需保存 tenant／owner metadata。MongoDB、任務快照與外部副作用不是單一交易；需要原子提交與永久歷史時，依需求設計 outbox、持久 repository 與冪等契約。

## 驗證

```bash
python scripts/check_boundaries.py
pytest
ruff check .
ruff format --check .
mypy src bootstrap server.py worker.py manage.py
```

測試 fixture 留在 `tests/`，正式業務 initializer 清單保持空白。RabbitMQ／Redis 可用時可啟用真實跨程序測試：

```bash
APP_RABBITMQ_URL=amqp://backend:local-backend-password@127.0.0.1:5672/ \
RUN_SYSTEM_INTEGRATION=1 pytest tests/test_system_integration.py -v
```

CI 定義位於 `.github/workflows/ci.yml`；本次實際驗證與未執行項目見 [驗證紀錄](docs/validation.md)。

## 設計交付文件

完整 [軟體架構設計規格](docs/software-design.md) 包含組裝、scope、API／worker、並行、身份／資料、kernel、失敗語意與驗證對照。另附 [原稿比對](docs/design-review.md)、[更新 SVG](docs/diagrams/backend-platform.svg)、[架構決策](docs/adr/README.md) 及逐位元組保存的 [使用者原稿](docs/references/README.md)。本版採用原稿的實體 package/module 命名；其中 PdM、Fab／Tool 模型與流程僅供未來應用設計參考。

## Docker／RabbitMQ 真實整合驗證

Docker Engine 啟動後，從專案根目錄、已安裝 dev 依賴的 Python 環境執行：

```bash
python scripts/verify_docker.py --host-tests
```

腳本建置正式 image，先測原始 CMD，再以 `compose.validation.yaml` 啟動獨立測試 stack；測試 fixture 唯讀掛載，不寫入正式 image。它檢查雙 API／雙 Taskiq、RabbitMQ quorum queue、MongoDB／JWT 權限、背景 kernel 結果與 API 重啟後狀態，並執行原先需 opt-in 的整合測試。隨機憑證與消毒後證據存於 `work/docker-validation/`，完成後清除本次 project 的 containers/network/volumes；image 保留供檢查。若 cleanup 失敗，0600 憑證檔會保留供定向清除。只通過設定檢查不表示已通過此實跑。
