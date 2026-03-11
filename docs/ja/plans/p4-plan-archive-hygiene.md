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

## 子タスク

- [ ] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S1-01] live plan inventory を棚卸しし、`active` / `backlog` / `stale-complete` の分類基準と representative 件数を記録する。
- [ ] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S2-01] representative な stale-complete live plan を archive へ移し、TODO/archive index のリンク整合を回復する。
- [ ] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S3-01] backlog plan の置き場所または表記ルールを決め、`plans/` 直下の意味を active-first に揃える。
- [ ] [ID: P4-PLAN-ARCHIVE-HYGIENE-01-S4-01] archive handoff 手順を README / 運用文書へ反映し、以後の完了 plan 滞留を防ぐ。

## 決定ログ

- 2026-03-11: この task は緊急度が低く、直近の変換器機能や runtime 契約整理を止める性質ではないため `P4` とする。
- 2026-03-11: まずは live plan 全件の archive ではなく、分類基準の明文化と representative stale-complete handoff から始める。
