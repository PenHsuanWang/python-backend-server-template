# 團隊開發與基線維護規範

本專案交付為通用 Template Repository。新增能力依 [開發手冊](docs/developer-guide.md) 與 [module-spec](docs/module-spec.md)；共用核心不預載產業模型、資料流程或演算法。

## 責任與變更範圍

- 能力團隊維護自己在 domain/application/api、adapters、plugins、config、bootstrap 的檔案、公開契約、資料及測試。需要外部 I/O 時使用 domain port，由 bootstrap 注入 adapter。
- 一般新增能力允許修改 bootstrap/wiring.py 的明確註冊及必要依賴／部署設定。共通 runtime、授權、訊息契約、shared_models、依賴或 CI 變更由平台與受影響團隊共同審查。
- 具 ownership 的 entity 不移入 shared_models；不讀寫另一能力的 collection，不藉共用工具繞過依賴邊界。跨能力依窄公開契約與 requires 組裝，避免循環。
- GitHub reviewer、CODEOWNERS 與 branch protection 由組織管理員依實際團隊設定；目前文件不假設遠端已強制執行這些政策。

## 提交與審查

每份 clone 先依 [CI／pre-commit 操作規範](docs/ci-precommit.md) 建立 `.venv`、hash 安裝 dev 依賴並執行 `python -m pre_commit install`。工具統一使用專案 `.venv`，hook 不會隨 clone 自動安裝。

1. 由目前交付基線建立工作分支，記錄變更動機、能力 owner 與公開行為。
2. 定義 schema、錯誤、permission、tenant／owner、資料 ownership。背景工作另訂重送、冪等、副作用完成、timeout、取消及保存期限。
3. 提交時執行 staged hooks；自動修正後先檢視 diff，再重新 stage 並重試。PR 前執行 `python -m pre_commit run --all-files --show-diff-on-failure`，並依 [工程基線](docs/engineering-baseline.md) 完成授權／契約及所需測試與整合檢查；PR 附指令、結果、外部依賴與尚未驗證項目。
4. 不提交 .env、token、密碼、測試 DB 或本機產物。範例憑證必須明確是隔離測試用途；不得以廣泛忽略規則規避 secret 掃描。
5. 同步設計、開發、部署與操作文件。需要新 SDK 時由同一鎖定流程更新並審查依賴、授權及安全掃描，不手改 hash。

管理員應將 `CI required`、`python-security`、`secrets`、`image-and-broker` 設為目標分支的 required checks；先以實際 PR 核對 check 名稱。`CI required` 僅彙整 CI workflow，另兩份 workflow 的檢查需分別選取。設定細節見操作規範；本文件不代表遠端 branch protection 已設定。

## 契約、版本與升級

Python distribution 版本、架構文件版本、HTTP API 版本、kernel implementation 版本與訊息 schema_version 分別管理。/api/v1 或 kernel version 字串不代表平台自動保障所有相容性。

每個產品記錄採用的範本 commit／tag，維護平台差異及能力清單。平台修補應提供相容性說明與必要 migration；產品以獨立 PR 合入、解衝突並重跑自己的契約及整合測試。複製範本不會自動收到上游修補。

公開 API／facade／payload 的破壞性變更須與消費者協調；queue 可能殘留舊訊息，不能只升級 API。資料 migration 使用獨立管理入口，記錄向前相容、資料備份、回復或補償流程；多 worker lifespan 不是只執行一次的 migration runner。

Release 前保留建置來源、wheel／image digest、測試及掃描結果。缺陷例外必須列範圍、原因、負責人、期限與補救措施，不能用綠色 workflow 取代未完成的驗收。成品通過 staging 後以同一 digest 推廣；資料回復另訂流程。目標 registry、部署環境與生產權責確認後再建立 CD。

專案授權與著作權 metadata 由權利人決定；本次交付不自行選定開源授權。不要將交付給內部團隊等同已完成對外授權審查。
