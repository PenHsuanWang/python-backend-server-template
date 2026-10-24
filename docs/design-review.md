# SVG 架構採納與設計評估（更新版）

日期：2026-10-23。使用者後續明確指定以 SVG 的**實體架構、package／module 命名與功能規範**改寫專案，因此本版取代前版「保留 backend feature modules」的取捨。原始設計完整保存於 [references](references/README.md)，最新版規格見 [software-design.md](software-design.md)。

| 面向 | SVG 的優點／代價 | 本版採納方式 |
| --- | --- | --- |
| 啟動組裝 | bootstrap 位於外緣，區分 wiring 與 request call；需避免容器成為 service locator | 實體建立 config/container/plugin_loader/wiring，保留具型別初始化與反序清理 |
| 分層命名 | api/services/application/domain/plugins/infrastructure 直觀，方便 SE/DS 分工；大型能力可能分散多層 | 採圖中頂層 package；層內保留同名 capability 子 package；以 use_cases/models/ports 等公開契約降低耦合 |
| 執行關係 | API 與 worker 共用 application，技術 services 不必成每次呼叫的中介層 | 保留 HTTP 與背景相同使用案例；不增加內部 worker→API HTTP |
| 策略與 adapter | plugins 實作 domain strategy，infrastructure 實作 ports，依賴內向 | SolutionKernel 移至 domain/strategy.py，可信插件於 bootstrap 驗證；repositories/locks/brokers 依責任搬移 |
| 共用支援 | config/utils/shared_models 可獨立重用；過度共用會成依賴捷徑 | settings/environment/constants、純 CSV／時間／request ID helpers、中性 JSON/error DTO；checker 禁止反向依賴 |
| 業務通用性 | 原圖的 Global→Fab→Tool、diagnostic models/pipeline 帶有 PdM 情境 | 保留命名與擴充位置，尚不預設工廠識別、合併政策、診斷流程或演算法 |
| 可維護性 | 平鋪 layers 使同功能橫跨多處；必須有一致命名與註冊規範 | 功能跨層使用同名 `<capability>`，bootstrap 只組裝，Module* 為初始化契約；新版模組規範提供新增流程 |

## 真正調整的責任邊界

- api.health 只處理 HTTP，services.health 檢查 runtime readiness；api.routers 集中掛載路由。
- IdentityServices 由 API 移到 application.identity.facade，API auth 與背景組裝共用相同 facade。
- KernelJobHandler 移到 application.orchestration，HTTP 與 worker 共享 KernelService。
- services.lifecycle 維持 dispatcher→active work→physical threads→resource cleanup 的技術順序。
- container 實際建構通用服務，plugin_loader 對明確選入的 kernel binding 驗證 metadata、契約版本與 async execute。
- package discovery、Dockerfile COPY、CI、測試 imports 與 logger roots 一起調整；不保留舊 backend shim。

## 保留的行為與限制

本地 IAM、JWT/session、tenant/owner、MongoDB、memory/Taskiq jobs、Redis snapshot-before-ack、capacity lease、受控匯出均保留。lease 不是設備業務互斥，job snapshot 不是永久歷史，跨 Redis／RabbitMQ／MongoDB 沒有原子交易；沒有 exactly-once、完整模型 registry、動態插件認證、worker readiness、metrics/tracing exporters 或生產 HA 保證。正式應用清單與演算法預設為空。

驗證及尚未執行項目見 [validation.md](validation.md)，逐一舊新路徑見 [package-migration.md](package-migration.md)，採納與被取代決策見 [ADRs](adr/README.md)。
