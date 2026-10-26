# Python Backend Server Template

以 Python 3.11+、FastAPI 建立的通用後端伺服器藍圖，定位為**共用平台能力＋按產品需求加入的應用模組＋可選的運算 kernel**。平台定義技術邊界與擴充契約，應用自行定義資料模型、使用案例、規則與外部系統整合。

範本採明確分層的 package，應用註冊清單與演算法預設空白，不預設任何產業、產品資料模型、應用流程或演算法。共用能力包含 runtime／lifespan、async 任務調派、MongoDB 連線、本地使用者與 JWT Bearer 驗證、資料權限／匯出契約、kernel 擴充與資源協調。各選用服務需明確啟用。

## 新進開發者：從這裡開始

第一次參與專案時，先閱讀 [團隊協作規範](CONTRIBUTING.md)，再依下方「本機空白啟動」建立環境。建議使用 Python 3.13；最低支援版本為 Python 3.11。Windows 開發環境使用 WSL2 或 Linux 容器。

新增業務 module 時，將它視為一個 `<capability>`，使用相同名稱放進既有分層：

```text
src/domain/<capability>/                業務模型、規則、錯誤與 ports
src/application/<capability>/           use cases、流程協調與選用的背景 handlers
src/api/<capability>/                   FastAPI routers、schemas 與 HTTP error mapping
src/infrastructure/<adapter_kind>/<capability>.py  DB／外部系統等 outbound adapters
src/plugins/<inference|heuristics>/<capability>.py 選用：可替換的 AI／ML／rule implementations
src/config/<capability>.py              選用：能力專屬設定
bootstrap/<capability>.py               ModuleDefinition、依賴注入與資源 lifespan
bootstrap/wiring.py                     明確選入並啟用能力
tests/test_<capability>_*.py            use case、權限、邊界與 adapter 測試
```

業務規則放在 `domain`，業務流程放在 `application`。不要把業務 application service 放進 `src/services/`；該 package 只承載 lifespan、concurrency、health、observability 等平台 runtime 技術服務。只有可替換的 AI／ML／rule 演算法才放入 `plugins`。

第一次貢獻的最短流程：

1. 從團隊指定的基線建立工作分支。
2. 建立 `.venv`、安裝 hash-locked 依賴並安裝 pre-commit hook。
3. 依上述位置加入 capability；在 `bootstrap/<capability>.py` 組裝，最後只在 `bootstrap/wiring.py` 選入。
4. 將新檔案加入 Git 後執行品質與單元測試：

   ```bash
   git add <本次變更的檔案>
   python -m pre_commit run --all-files --show-diff-on-failure
   python -m pytest -m "not integration" --cov --cov-report=term
   ```

5. 檢查 `git diff --cached`，確認程式、測試、設定與文件一起更新，再依團隊流程建立 Pull Request。

完整的可複製範例與設計模式見 [業務團隊開發手冊](docs/developer-guide.md)，規範性依賴與 module 契約見 [module 功能規範](docs/module-spec.md)，本機 hooks 與 CI 門檻見 [CI／pre-commit 操作規範](docs/ci-precommit.md)。

## 名詞與擴充界線

`server.create_app()` 採 **Application Factory Pattern（應用建立函式模式）**：建立 FastAPI application 與 lifespan 定義。`--factory` 是 Uvicorn 呼叫該函式的參數；dataclass／Pydantic 的 `default_factory` 是欄位預設值建立機制。本文不以「工廠」簡稱上述軟體機制，完整定義見 [術語表](docs/glossary.md)。

通用平台提供 lifecycle、transport、安全、資料存取與任務執行契約；應用在需要時才加入自己的 domain entity、policy、workflow 與 adapter。`tenant_id` 只表示授權與資料隔離邊界，設定解析與應用識別由產品自行設計。空 package 代表擴充位置，不表示功能已完成。

## 本機空白啟動

以下命令使用建議的 Python 3.13；使用最低支援版本時，將 `python3.13` 換成 `python3.11`。

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements-build.lock
python -m pip install --require-hashes -r requirements-dev.lock
python -m pip install --no-deps --no-build-isolation -e .
python -m pre_commit install
cp .env.example .env
python server.py --reload
```

這份 hash lock／CI 以 Linux 為基準，另有 macOS 本機驗證。原生 Windows 不屬於本次驗證範圍；Windows 團隊請使用 WSL2 或 Linux 容器。也可執行 `uvicorn server:create_app --factory --reload`。預設採 memory 任務後端與單一 API 程序，MongoDB、身份、kernel、匯出及 job 查詢 API 均關閉；只提供健康檢查與 API 文件。

```bash
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
```

文件位於 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)。應用模組、任務、kernel 與匯出資料源清單皆為空，不會自動產生應用端點或資料表。

## 不使用背景工作的部署

純 HTTP API 可明確停用背景工作，在 production 啟用多個 API 程序，不需 RabbitMQ／Redis：

```bash
APP_ENVIRONMENT=production APP_TASK_BACKEND=disabled APP_WORKERS=4 \
python server.py --workers 4
```

此命令沿用 Mongo／identity 等能力的關閉預設；若已有 `.env`，需確認其中的能力與 resource backend 設定符合目標。`disabled` 不啟動 queue consumers；模組取得的 `context.jobs` 為 `None`，匯出 tasks 或開啟 job 查詢會在啟動驗證時拒絕。需要身分管理或儲存時可分別啟用，受保護的 application API 仍須 identity。同步 kernel 可單獨使用；`/kernels/{name}/runs` 與 job 查詢只在背景工作啟用時掛載。kernel 的 identity 與多程序／production Redis 容量協調要求仍適用。

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

前端後續請求帶 `Authorization: Bearer <access_token>`。管理員透過受控的 `/api/v1/identity/register` 建立同租戶使用者；沒有公開 signup。短效 token 預設 900 秒，每次受保護請求重新檢查 session、使用者狀態與目前權限，登出／停權於後續受保護請求生效。第一版不包含 refresh token、SSO、MFA 或完整角色引擎。

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

完整規範見 [module 功能規範](docs/module-spec.md)，舊 Python import 的破壞性變更見 [搬移對照](docs/package-migration.md)。`src` 是實際可匯入的 package，套件安裝同時包含 `src` 與 `bootstrap`。`hierarchy.py` 只是可選的設定解析擴充點；平台不提供預設繼承階層或固定 workflow。

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

`--reload` 與多 worker 不能合用。有共享背景工作時使用 distributed；不需要背景工作時可使用 disabled。直接執行 Uvicorn 時，必須自行維持 APP_WORKERS 與實際 worker 數一致；Application Factory 無法可靠得知 Uvicorn CLI 的 worker 數。[Uvicorn settings](https://uvicorn.dev/settings/)

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

kernel／匯出 API 開關不會安裝任何實際 kernel 或資料源。job 查詢預設關閉；開啟 kernel API 且 task backend 啟用時，會一併提供具 tenant／owner 保護的 job 查詢。正式環境的 job API 必須啟用 identity；自訂任務提交需保存 tenant／owner metadata。MongoDB、任務快照與外部副作用不是單一交易；需要原子提交與永久歷史時，依需求設計 outbox、持久 repository 與冪等契約。

## 驗證

```bash
python -m pre_commit run --all-files --show-diff-on-failure
pytest
python scripts/verify_package.py
python scripts/verify_guide.py
```

測試 fixture 留在 `tests/`，正式業務 initializer 清單保持空白。RabbitMQ／Redis 可用時可啟用真實跨程序測試：

```bash
APP_RABBITMQ_URL=amqp://backend:local-backend-password@127.0.0.1:5672/ \
RUN_SYSTEM_INTEGRATION=1 pytest tests/test_system_integration.py -v
```

CI 定義位於 `.github/workflows/ci.yml`；本次實際驗證與未執行項目見 [驗證紀錄](docs/validation.md)。

## 設計交付文件

不同團隊新增 application 的操作手冊見 [developer-guide.md](docs/developer-guide.md)，包含檔案落點、設計模式、可複製範例、權限與接入驗證。

使用本專案衍生 ML Training／Model Serving 系統，請閱讀 [ML System 開發方向與架構設計](docs/ml-system-design.md)。文件定義模組落點、持久工作、MLflow、模型核准與部署、可靠性、開發里程碑及驗收；ML 能力為待實作設計，不改變目前空白啟動基線。

ML 設計 v0.2 附 [C4 L1～L4 圖集](docs/diagrams/ml-system-v0.2/README.md)、[DeploymentSpec 交付契約](docs/contracts/ml-deployment-v1/README.md)、[Runtime 相容矩陣](docs/ml-runtime-compatibility.md)及[程式基線符合性審查](docs/ml-system-compliance-review.md)，區分設計契約與實際驗證結果。

能力需要跨 process／deployment boundary 時，依[微服務契約設計與演進指南](docs/microservice-contracts.md)定義資料 ownership、同步／非同步 wire contract、版本相容、冪等、服務身分、觀測與發布閘門。程序內 `ModuleExports.services` 不等同網路契約。

完整 [軟體架構設計規格](docs/software-design.md) 包含組裝、scope、API／worker、並行、身份／資料、kernel、失敗語意與驗證對照。另附 [原稿比對](docs/design-review.md)、[更新 SVG](docs/diagrams/backend-platform.svg)、[架構決策](docs/adr/README.md) 及逐位元組保存的 [使用者原稿](docs/references/README.md)。目前通用基線為 PBP-SAD-001 v1.3；參考原稿只保留設計來源，不構成應用場景、實作狀態或未來必備功能的規範。

工程安裝、鎖定更新、建置與品質門檻見 [工程基線](docs/engineering-baseline.md)；本機 hooks 與 CI 合併檢查見 [CI／pre-commit 操作規範](docs/ci-precommit.md)；團隊責任與版本升級見 [CONTRIBUTING.md](CONTRIBUTING.md)；本次交付範圍見 [交付狀態](docs/handover.md)。

## Docker／RabbitMQ 真實整合驗證

Docker Engine 啟動後，從專案根目錄、已安裝 dev 依賴的 Python 環境執行：

```bash
python scripts/verify_docker.py --host-tests
```

腳本建置正式 image，先測原始 CMD，再以 `compose.validation.yaml` 啟動獨立測試 stack；測試 fixture 唯讀掛載，不寫入正式 image。它檢查雙 API／雙 Taskiq、RabbitMQ quorum queue、MongoDB／JWT 權限、背景 kernel 結果與 API 重啟後狀態，並執行原先需 opt-in 的整合測試。隨機憑證與消毒後證據存於 `work/docker-validation/`，完成後清除本次 project 的 containers/network/volumes；image 保留供檢查。若 cleanup 失敗，0600 憑證檔會保留供定向清除。只通過設定檢查不表示已通過此實跑。
