# 驗證紀錄（更新：2026-10-24）

下列命令從本專案根目錄執行，以載入 `pyproject.toml` 的 async 測試設定。host 測試環境使用 Python 3.13.11；Docker image 內為 Python 3.13.17／Linux arm64；依賴版本記錄於 `requirements.lock`。主要套件為 FastAPI 0.161.1、Uvicorn 0.54.0、Taskiq 0.12.6、taskiq-aio-pika 0.6.1、redis-py 8.1.0、PyMongo 4.19.0、pwdlib 0.3.1 與 PyJWT 2.15.1。

## v1.2 通用藍圖修訂（2026-10-24）

本輪只修訂正式文件、術語、SVG、三個 Python 檔的 docstring／註解，沒有新增執行邏輯、API、設定或訊息契約。已核對 123 個版本控制中的 Python 檔：移除 docstring 後的 AST 與修訂前一致；Ruff／格式與依賴邊界檢查通過；正式文件的產業假設掃描、Markdown 連結／fences、SVG XML 解析及渲染目視檢查通過。原始參考 `.md`／`.svg` 與既有 `docs/evidence/` 全部維持逐位元組一致。

本輪沒有重跑完整 pytest 或重新建置 Docker image。下列完整整合結果屬於修訂前已保存的 run；其 image ID、image-source-manifest 與日誌描述當時實際建置來源，並非 v1.2 文件的逐位元組映像驗證。原始證據不因文件版本更新而改寫。

## 先前已執行的工程驗證


- **先前完整 Docker 整合 run 的 host pytest：406 passed，0 skipped，10.68 秒**。由 `scripts/verify_docker.py --host-tests` 明確啟用 `RUN_SYSTEM_INTEGRATION=1`，在 host 開發環境執行，broker／MongoDB 指向隔離的真實容器。原先略過的雙 API／雙 Taskiq 測試已通過。未設定 opt-in 開關的一般 pytest 仍會略過該項。
- **正式 Docker image 與容器內整合已通過**：Docker 29.4.0，RabbitMQ 4.4.0、Redis 7.4.8、MongoDB 8.3.13。映像為非 root UID 999；原始 CMD、乾淨 OpenAPI、readiness 與 graceful shutdown 通過。另一組同 image 容器唯讀掛載測試 fixture，兩個 API PID 9/10、兩個 Taskiq PID 8/9 完成 32 筆 JWT 授權 kernel 工作；quorum queue 有兩個 consumer，最後 ready/unacknowledged 均 0；API restart 後 Mongo session／Redis snapshot 可查，logout 撤銷有效。
- 最終 image：`local/backend-validation:605e70e128ef`，ID `sha256:7e2d2d15be864e087569b2f3af80e9922999f328c52f2e0e7be7d16670b3aed9`。本次 project 的 containers、network、volumes 已清除，image 保留。[最終報告與日誌](evidence/docker-2026-10-24/README.md)、[可重跑操作手冊](docker-validation.md)。
- 空白預設 API、輸入驗證、設定互斥、secret 錯誤遮蔽、預設 JWT 保護、匿名入口明確選入、啟動失敗回滾及資源釋放順序。
- 新 API/health 邊界 14 個案例；readiness 技術檢查與 HTTP adapter 分離、route group 掛載、既有 JWT 政策。
- 可信 plugin loader 19 個案例：明確註冊、唯讀 mapping、namespace／contract／version／spec／kind、同步 execute 拒絕、async callable 支援，以及 API／worker 初始化失敗反序回滾。
- 模組 manifest、依賴拓撲／循環檢查、命名空間、公開 facade、API／worker 初始化失敗回滾。
- AST 依賴邊界檢查：161 個案例，涵蓋新 src 各層、bootstrap／entrypoints、相對／絕對 import、TYPE_CHECKING、API DI 例外、禁止 SDK 滲入內層及拒絕舊 backend package。
- 本機任務並行限制、背壓、隔離、逾時、取消、TTL、容量淘汰及 JSON 結果契約測試。
- 真實 Taskiq receiver 搭配 broker／storage 替身，驗證終態寫入先於 ack、Redis 故障恢復、取消不確認及重送處理。
- 隔離的真實 Redis 程序：共享快照、TTL、兩個 coordinator 的共享容量、續租超過原期限、fencing 與 owner-safe release。
- Bounded thread executor：入場／等待容量、contextvars、取消與重複取消、關閉取消及實體工作完成前不提前釋放資源。
- Kernel：thread 容量不足透傳為 HTTP 503 的回歸測試、空 registry、明確版本、權限、並行容量、lease 失效、timeout／取消／關閉、嚴格 JSON、背景任務重新授權及 job 租戶／擁有者隔離。演算法只使用測試專用技術 fixture。
- 匯出：空來源、權限、欄位白名單、敏感欄位遮蔽、CSV 公式防護、串流／筆數／單列大小、Mongo 查詢強制 tenant／owner 範圍。
- **真實 MongoDB 8.2.3 整合**：以獨立臨時資料路徑及 loopback 埠啟動，全程開啟 `--auth`，建立一次性資料庫帳號；驗證 Argon2／JWT 登入、受控註冊、錯誤簽章拒絕、跨租戶隔離、即時 permission、停權、session 登出、原子登入限制與受控資料匯出。結束後清除測試 DB 並關閉實例。
- 重構後真實 Uvicorn HTTP smoke：readiness 200、預設 OpenAPI 僅有兩個健康端點、X-Request-ID、src.server／src.api.http JSON 日誌；SIGTERM 後確認 application shutdown complete。
- `ruff check .`、`ruff format --check .`、`mypy src bootstrap scripts server.py worker.py manage.py`（102 個 source files）、`scripts/check_boundaries.py` 及 `pip check`。
- 離線 wheel 建置：`pip wheel --no-index --no-deps --no-build-isolation`（本機 bundled setuptools/wheel 作建置工具）。在專案外 CWD 與 Python `-I` 載入 wheel 解壓內容，server／worker／manage／domain strategy／plugin loader 均來自安裝內容；封鎖 socket 後 imports 與預設 create_app 仍成功。wheel 不含舊 backend、tests、.env、key/pem 或 pyc。
- 使用者原始 SVG 與設計文件逐位元組保存並記錄 SHA-256；原圖及更新 SVG 均經 XML／rsvg 解析與實際渲染目視檢查；本專案 Markdown 連結檢查無失效目標（原稿保留原樣）。
- 本次取捨、層級映射、狀態／timeout／retention／session 與已實作／待實作的描述經獨立程式對照，見 `design-review.md`、`software-design.md` 及 ADR。
- `docker compose config --quiet`、CI YAML 語法與 MongoDB integration service 設定；檢查時產生的 secrets 不輸出至日誌。
- TypeScript client 的 Node 原生型別移除／載入與 smoke：登入不附帶 Bearer、同源授權、拒絕跨來源／redirect、401 清除 token。未執行完整 TypeScript 編譯。

尚未執行：

- 正式 `compose.yaml` 本次完成 config 檢查；實際隔離整合使用 `compose.validation.yaml`，不是目標生產拓撲／HA 驗收。
- GitHub Actions；CI 已定義 Python 3.11／3.13 檢查、MongoDB 整合及 RabbitMQ／Redis 多程序整合工作。目前本機 Python 實測版本為 3.13。
- 完整前端應用、使用者管理 UI 與瀏覽器端端到端測試；交付內容是可整合的 JWT client。
- 生產環境的壓力測試、故障演練與部署驗收。

Docker 驗證另新增獨立 Compose、測試 fixture 與可重跑 runner；修正日誌 stdout/stderr 合併檢查、API 重啟後動態 host port 更新，以及清除／憑證遮蔽的錯誤路徑，新增四個安全回歸測試。正式應用 wiring 未載入 probe kernel，image 不包含 tests。

先前依 SVG 實際搬移 package／module，拆分 API／技術 service／application 責任，新增明確 plugin 契約驗證與中性支援入口，並更新 setuptools、Dockerfile、CI、logger roots 與文件。既有 IAM／jobs／Mongo／exports／kernel 行為保留；正式業務 initializer 與演算法仍為空，沒有新增預設產品場景。

這份紀錄描述已完成的驗證，不代表所有部署環境或未來依賴版本都具有相同行為。
