# Issue 2 validation

Related to https://github.com/xgw69/ST2MOD_MAD_SCIENTIST/issues/2. This is partial code-level coverage; it does not complete the 63-card acceptance checklist.

Validated on 2026-10-23 against public-beta v0.111.0 (41cef1ea, Steam build 24724944), installed BaseLib 3.4.7, and source baseline 64be9a65c48bebc5d87c926c6747daab1f72beea. Work used an independent source branch. No game was launched, installed mod replaced, or official save written.

## Fixes

1. Clamp the first durability repair to 20 and avoid overflow when adding subsequent repairs.
2. Allow zero durability consumption without dereferencing an absent power; keep the broken-machine guard.
3. Restrict free Blast costs to the power owner's cards.
4. Cancel card-sourced block multiplicatively after additive modifiers, so Dexterity/listener ordering cannot restore it. Non-card and teammate block remain unaffected.
5. Retain Soul Research's spent single-stack power through combat, guard repeat callbacks, and expose saved Used state plus a spent tooltip. Reapplying the card cannot install a fresh revival in the contract tests.
6. Copy Scientific Research on turn-start hand draws as well as effect draws.
7. Apply Blasting Device's independent Blast discount at X=0 even when no cards are generated.

Also translated eight English power values (four titles and four descriptions), and clarified Soul Research's once-per-combat wording in both languages. ScientificResearch and SoulResearchPower were extracted from multi-class files so the tests link the actual implementations.

## Results and limits

| Check | Result | Meaning |
|---|---|---|
| Production-linked contract assertions | 80 passed, 0 failed | Simplified game doubles and actual Harmony; not the engine, persistence or network |
| PowerShell static resources | 534 passed | Key parity, English text, card variables/portraits, eight ancient groups and PNG headers; not complete runtime localization coverage |
| Original Python resources | 4 passed | Existing validator |
| All production C# against installed assemblies | 0 errors, 18 existing nullable warnings | Compile compatibility only; excludes Godot generators, mod analyzers and packer |
| Full release build | FAILED: 17 STS001 errors, 20 warnings | No deployable DLL/PCK produced |
| Game / save-reload / UI | NOT RUN | Maintainer testing required |
| Multiplayer | NOT RUN | No second client available |

The expanded baseline reproduced 7 failing assertions (49 passed, including two failures for the base/upgraded Soul Research case). The later X-boundary run reproduced Blasting Device X=0 (79 passed, 1 failed). Final 80/80 results include fusion deep-copy/order/cost/X/keyword/replay and serialization-double tests, nine Mad Science variants, durability, block lock, temporary Blast costs, Soul Research and Scientific Research. Inventory and 9-choose-3 UI are not covered by executable tests.

Installed Hook.ModifyBlock IL was inspected to verify additive modifiers precede multiplicative modifiers. Two-owner tests verify the owner condition, not multiplayer synchronization. Scientific Research enchantments, Soul Research at very low Max HP and next-combat cleanup, native fusion serialization/material disappearance, all card play/upgrade interactions, dialogue rendering, merchant/rest layout and gestures require actual game testing.

issue-2-card-matrix.csv has 63 rows and keeps static/unit evidence separate from play, upgrade, copy/fusion, save and multiplayer statuses. All game acceptance columns remain unverified.

## Release build diagnosis

An initial sandbox restore failed with a Windows TLS credential error. An approved subsequent restore stalled and was stopped; its precise cause was not established. A bounded retry with the official nuget.org source then restored all declared dependencies successfully in 4.69 seconds, without changing versions or system security/network settings.

The full Godot build then finished in 4.17 seconds with 17 localization analyzer errors:

- Fifteen powers lack .smartDescription keys.
- The character lacks four THE_ARCHITECT.talk.MADSCIENTIST-MAD_SCIENTIST dialogue keys.
- FusedXCard resolves FUSED_X_CARD.title / .description, whereas the resource keys have the MADSCIENTIST- prefix. The analyzer also warns that FusedCard does not implement the custom-model base/interface.

These are unresolved build blockers, not a successful release build. The 534 static checks do not detect them. Further packaging work and game/save/multiplayer execution were stopped at the user's request so the current code fixes can be reviewed in a PR. Do not deploy the compile-check DLL as a release.

## Reproduction and evidence

See tests/ISSUE-2.md and tests/run_issue2.ps1 for the offline compile/contract/resource workflow. Logs in issue-2-evidence/ include the baseline failures, final passes, restored dependencies and failed full build. Absolute local paths were replaced with placeholders for publication. Assembly SHA-256 hashes are included; proprietary DLL/PCK files and saves are not.

Maintainers should first resolve the release analyzer errors, build a matching DLL/PCK, and test in a disposable user-data environment with Steam-cloud isolation. The existing headless script shares real settings/saves and must not be used on a valuable profile. Multiplayer additionally requires a second matching client. This PR relates to issue #2 without closing it.
