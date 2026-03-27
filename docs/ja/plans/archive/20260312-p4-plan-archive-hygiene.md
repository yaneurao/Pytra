<a href="../../../en/plans/archive/20260312-p4-plan-archive-hygiene.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P4 Plan Archive Hygiene

最終更新: 2026-03-11

目的:
- `docs/ja/plans/` 直下に残っている live plan を、`active` / `backlog` / `stale-complete` に整理する。
- `docs/ja/todo/index.md` と `docs/ja/plans/` の整合を回復し、「未完了 task なのに plan が無い / 完了済みなのに live plan が残る」状態を減らす。
- archive handoff の手順を固定し、以後の完了 task が `plans/` 直下に滞留しないようにする。

背景:
- 現在の [TODO](/workspace/Pytra/docs/ja/todo/index.md) は未完了 task なしになっている一方で、[plans](/workspace/Pytra/docs/ja/plans/README.md) 直下には `p0-*` / `p1-*` / `p2-*` / `p3-*` / `p4-*` plan が大量に残っている。
- archive 側には既に多数の完了 plan が移動済みで、live plan と archive plan が混在している。
- この状態だと、`plans/` を見ただけでは active plan / backlog plan / 完了済み stale plan を判別できず、TODO 運用ルールの前提が崩れる。

非対象:
- 各 plan 本文の技術内容の見直し。
- task 優先度の再設計そのもの。
- archive 済み履歴本文の大規模 rewrite。

受け入れ基準:
- `docs/ja/plans/` 直下の `p*-*.md` について、active/backlog/stale-complete の分類基準が plan で明文化されている。
- representative な stale-complete plan を archive へ移し、TODO/archive index と整合する。
- backlog として残す plan は、TODO 未登録の backlog であることが plan か README から判別できる。
- `docs/en/` mirror が日本語版と同じ運用方針に追従している。

## 分類基準と棚卸しスナップショット

- 集計対象は `git ls-files` に載っている `docs/ja/plans/` 直下の `p*-*.md` とし、未追跡の plan draft は数えない。
- `active`: `docs/ja/todo/index.md` の未完了タスクから直接参照されている live plan。
- `stale-complete`: live plan が TODO 未登録で、checklist がすべて `[x]` で閉じており、tool の既定出力先や live status/report sink でもないもの。
- `backlog`: live plan が TODO 未登録で、未完了の backlog か、tool が live path を前提にする status/report plan。

2026-03-12 時点の tracked inventory（corrected criteria）:
- handoff 前 live `p*-*.md`: 146 件
- `active=6 / stale-complete=129 / backlog=11`
- `S2-01` で representative stale-complete 6 件を archive へ移した後は `live=140 / active=6 / stale-complete=123 / backlog=11`

representative active:
- `p4-plan-archive-hygiene.md`
- `p4-crossruntime-pyruntime-emitter-shrink.md`
- `p4-crossruntime-pyruntime-residual-caller-shrink.md`

representative stale-complete（`S2-01` handoff 済み）:
- `p1-multilang-selfhost-status.md`
- `p1-multilang-selfhost-multistage-status.md`
- `p0-backends-common-foundation.md`
- `p1-ruby-benchmark-readme-fix.md`
- `p1-go-sample01-quality-uplift.md`
- `p1-test-unit-layout-and-pruning.md`

representative backlog / live-status:
- `p0-cpp-backend-dir-realign.md`
- `p1-pytra-cli-rs-target.md`
- `p2-wildcard-import-support.md`

## 子タスク

- [x] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S1-01] live plan inventory を棚卸しし、`active` / `backlog` / `stale-complete` の分類基準と representative 件数を記録する。
- [x] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S2-01] representative な stale-complete live plan を archive へ移し、TODO/archive index のリンク整合を回復する。
- [x] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S3-01] backlog plan の置き場所または表記ルールを決め、`plans/` 直下の意味を active-first に揃える。
- [x] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S4-01] archive handoff 手順を README / 運用文書へ反映し、以後の完了 plan 滞留を防ぐ。

## 決定ログ

- 2026-03-11: この task は緊急度が低く、直近の変換器機能や runtime 契約整理を止める性質ではないため `P4` とする。
- 2026-03-11: まずは live plan 全件の archive ではなく、分類基準の明文化と representative stale-complete handoff から始める。
- 2026-03-12: 初回棚卸しでは `archive twin がある` ことを stale-complete 条件に使ってしまい、`p1-multilang-selfhost-status.md` と `p1-multilang-selfhost-multistage-status.md` を代表候補に誤分類した。
- 2026-03-12: corrected criteria では `stale-complete` を `TODO 未登録 + checklist 完了 + live status/report sink ではない` と再定義し、tracked live inventory を `active=6 / stale-complete=129 / backlog=11` に修正した。
- 2026-03-12: `S2-01` では representative stale-complete handoff として `p0-backends-common-foundation.md`, `p1-ruby-benchmark-readme-fix.md`, `p1-go-sample01-quality-uplift.md`, `p1-test-unit-layout-and-pruning.md` を archive へ移し、先行で archive 済みの selfhost status 2 件を含めて live inventory を `140` 件まで縮めた。
- 2026-03-12: `plans/README.md` を live `plans/` の canonical entrypoint に固定し、active 6 件の列挙と backlog/stale-complete の分類規則を README 側へ明記した。新規 backlog draft は `関連 TODO: なし（backlog draft / TODO 未登録）` を許容する。
- 2026-03-12: `S4-01` で `plans/README.md` と archive 運用文書に archive handoff checklist を追加し、corrected criteria に基づく分類を README に同期した。これにより、本 task 自身も同じ handoff 手順で archive へ移せる状態になった。
