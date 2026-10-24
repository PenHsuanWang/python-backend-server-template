# 架構決策紀錄

本文件記錄設計取捨與取代關係。「採用」表示本專案的程式與文件基線，不表示組織已完成生產核准。日期皆為 2026-10-23；實際驗證以 [驗證紀錄](../validation.md) 為準。

| ID | 狀態 | 決策與理由 | 代價／重新評估條件 |
| --- | --- | --- | --- |
| ADR-001 | **由 ADR-008 取代** | 前版採 `backend/modules/<name>/` feature module、模組內分層及 `runtime/composition.py` 組裝。 | 保留此紀錄解釋既有版本；不得再作新增 package 的規範。 |
| ADR-002 | 採用 | 不將 PdM 模型、Global → Fab → Tool 或診斷 pipeline 寫入通用核心；原稿保存參考。 | 首個應用須定義自身 domain、階層設定與流程，不能假設通用平台已提供這些語意。 |
| ADR-003 | 信任模型保留；實體位置由 ADR-008 取代 | 插件使用受信任、明確註冊的 Python 實作，於 lifespan 建立並注入；前版模組內 `plugins/` 位置不再使用。 | Python import 執行程式；AST checker 不提供 sandbox。第三方分發／熱更新前須另定契約版本、簽章、artifact 驗證與程序隔離。 |
| ADR-004 | 採用 | 開發可用單程序 memory；共享任務採 Taskiq＋RabbitMQ、Redis TTL 快照。先寫終態再 ack，明列不確定提交與重送界線。 | 無 outbox、跨儲存交易、自動業務重試或永久結果；關鍵副作用需持久冪等與 reconciliation。 |
| ADR-005 | 採用 | 計算容量使用 memory 或 Redis lease，具 owner token、續租與 fencing token；失效時取消 cooperative 工作。 | 不能殺死 Python thread，也不能保證舊持有者停止寫入；外部 adapter 必須檢查 fencing，Redis failover／災難復原需另訂策略。 |
| ADR-006 | 採用 | 首版使用本地帳號、Argon2、短效 JWT＋Mongo session、permission 與 tenant／owner policy；管理員受控註冊。 | 非完整 RBAC／ABAC／企業 IAM；SSO、逐 kernel entitlement、密碼復原、session 全撤銷與完整稽核需另訂介面。 |
| ADR-007 | 內向抽象原則保留；檢查規範由 ADR-009 更新 | infrastructure 使用 TaskResolver 與 domain export policy，避免具體 application 耦合；靜態檢查搭配行為測試。 | 靜態 import 不能驗證反射、re-export 語意、外部副作用或所有 SOLID 特性。 |
| ADR-008 | **採用；取代 ADR-001 及 ADR-003 的 package 位置** | 採用使用者 SVG 的實體架構與命名：根目錄 `bootstrap/`，以及 `src/{api,services,application,domain,plugins,infrastructure,config,utils,shared_models}`。 | 更改 Python import 路徑，跨層同一能力的檔案不再集中於 feature package；須用一致能力名稱、規範與靜態檢查維持可追溯性。 |
| ADR-009 | 採用；更新 ADR-007 的邊界守門 | 按實體層驗證向內 import；保留穩定 facade、跨層啟動描述與 API／worker 共用使用案例。 | facade 不能重出口外層造成反向依賴；明確註冊不是安全 sandbox，也不提供動態外掛相容性保證。 |

## ADR-008：以 SVG 作實體 package 基線

使用者明確要求依 SVG 改寫 package、modules 名稱及功能規範；因此前版「保留 feature modules、僅映射邏輯層」的取捨已被取代。此次採實體層級改寫，程式 import、測試、型別檢查、部署入口與文件同步改用 `src.*`／`bootstrap.*`，不留下另一套 `backend.*` 相容性 package。

採用下列責任：

- `bootstrap/` 是 composition root：讀取設定、選擇可信 plugin、建構資源、注入使用案例。組裝不是 request-time 呼叫鏈。
- `src/api/` 負責 HTTP adaptation；`src/application/` 負責使用案例；`src/domain/` 定義純模型、政策、strategy 與 ports。
- `src/services/` 負責技術性 runtime 支援，與 application 同層；不強制所有請求經過 services。
- `src/plugins/{inference,heuristics,interceptors}` 實作 domain 策略；`src/infrastructure/{persistence,messaging,locking,downstream}` 實作 outbound ports。身份技術 adapter 另列 `infrastructure/security.py`。
- `src/config`、`src/utils`、`src/shared_models` 按需使用，不能充當繞過邊界的共用資料夾。

SVG 的業務標籤未變成預設行為。`application/hierarchy.py` 保留不帶政策的擴充位置；沒有 Fab／Tool 設定解析。`application/orchestration.py` 管理既有背景 kernel 使用案例接入；沒有預設 Lock → Fetch → Evaluate → Publish 診斷流程。`plugins` 的目錄存在不代表已有模型／規則／interceptor 實作。這保留 ADR-002 的通用核心界線。

新增應用沿 `domain/<capability>`、`application/<capability>`、`api/<capability>` 及相應 plugins／infrastructure 模組協作。組裝描述放在 `bootstrap/`，不再建立 `backend/modules/<name>/`。具體規則見 [Package 與模組規範](../module-spec.md)。

## ADR-009：穩定公開契約與明確組裝

SVG 所示 `src/domain/models.py`、`src/domain/ports.py` 聚合內層穩定契約；`src/domain/strategy.py` 直接定義 `SolutionKernel`。`src/application/use_cases.py` 公開四項共通 service 及 `KernelJobHandler`。它們不複製另一套型別、不隱藏資源建構，也不讓 domain 依賴外層。能力專屬實作仍可使用同名子 package，以免所有程式集中於單一大型檔案。

保留 `ModuleDefinition`、`ModuleContext`、`ModuleExports`、`ModuleCatalog`、`build_modules()` 及 `create_app(..., modules=...)` 的 Python 註冊契約，實作移至 `bootstrap`。此處 module 指跨層功能的啟動描述，不代表 feature module 實體目錄。依賴排序、資源 rollback、反向關閉、任務 namespace 與測試注入能力繼續使用。

`bootstrap.plugin_loader.PluginBinding(name, implementation, contract_version="solution-kernel/v1")` 與 `load_approved_plugins()` 只處理受信任且明確選入的 kernel bindings；檢查 `<capability>.<local_name>`、重名、契約識別、KernelSpec 版本／kind 及 execute 為 async function／async callable。`ModuleCatalog` 實際使用此驗證器，不從 request／queue 決定 import 路徑；它不保證 async 函式內不阻塞或可取消，也不驗證模型內容、簽章或外部核准。`bootstrap.config.load_settings()` 是入口實際使用的設定載入點；`src/services/lifecycle.py` 登記 dispatcher、active operations、threads 的關閉順序。`src/application/registry.py` 查找已註冊任務；它不負責按工廠身份自動選擇演算法。API 與 worker 各自建立資源，直接重用 application 使用案例，worker 不經 API 轉送。

CI 守門應依新分層攔截 domain 反向 import、application 選擇具體 adapter、API 存取 infrastructure、plugins 與 infrastructure 直接耦合等問題。行為、動態 import、第三方副作用及資源 ownership 仍需審查與測試；穩定公開名稱不等於任意重出口皆合理。

## 待需求確定的決策

| ID | 何時必須決定 | 必須產出的規格／證據 |
| --- | --- | --- |
| OD-01 | 首個工廠應用 | 識別與資料 schema、時間／單位、設定 scope／precedence／merge／conflict、版本與 audit 快照。 |
| OD-02 | 使用者／租戶可選不同 kernel | entitlement、策略選擇、輸入／輸出 schema、contract version、模型 provenance 與 artifact 驗證。 |
| OD-03 | 寫入關鍵業務結果或向下游發布命令 | idempotency key、交易範圍、持久結果、重送、重試上限、outbox 或補償／對帳契約。 |
| OD-04 | 投入 CPU／GPU 模型或長時間阻塞 SDK | 每程序模型記憶體、native threads、GPU 配額、執行隔離、timeout 與強制終止方案。 |
| OD-05 | 廠內上線 | 網路／TLS／secrets、最小權限 DB 帳號、worker probe、metrics／tracing／audit、SLO、壓測、HA／備份／RPO／RTO、故障演練與回滾驗收。 |

本基線已選 Taskiq／RabbitMQ／Redis 作共享任務方案，未因此完成所有真實部署驗收。容量 lease 也未完成設備業務互斥／副作用契約。最新已執行及未執行項目以驗證紀錄列出的實際證據為準。
