# Rose Project

Portable Windows build of Rose with the loading-screen skin-name hotfix restored.

## Download

Download the latest executable package from:

[Latest Release](https://github.com/lucianoestevest477-bit/rose-project/releases/latest)

Release asset:

`Rose-v2026.04.28-loading-name-rst.zip`

Extract the ZIP and run:

`Rose.exe`

## What Changed In This Version

- Restored the loading-screen name fallback so the loading card can show the selected skin name instead of only the champion name.
- Added a locale-aware stringtable override for the loading name fallback.
- Uses the active LCU locale, such as `pt_BR`, before falling back to other `Global.*.wad.client` files.
- Fixed WAD tool discovery in the packaged build, so `wad-extract.exe` and `wad-make.exe` are resolved from `_internal\injection\tools`.
- Keeps chroma labels clean by using the base English skin name instead of appending the chroma color suffix.
- Preserves normal skin, chroma, custom mod, and party mod injection flows.
- Removed temporary debug experiments from the final path:
  - no `debug_loading_name_hash`
  - no `debug_loading_name_log`
  - no `debug_stop_overlay`
  - no `LCU-RESTORE`
  - no hardcoded loading-card hash override

## Loading Name Hotfix Notes
1-Chroma without the color suffix
Yes. We kept the chroma using display_name=english_skin_name or chroma_display_name, so the loading label uses the base skin name, not something like Azir (Pink).

2-Locale without hardcoded pt_BR
Yes. The code now uses state.lcu_language, detected from LCU. The lookup tries Global..wad.client first, for example Global.pt_BR.wad.client, Global.en_US.wad.client, etc., and only then falls back to Global.*.wad.client.

3-Rebase/base with the security fix
Partially yes in practical terms: the current Rose-main version we published preserved the clean/safe base you were using. However, since the local Rose-main was not a Git repository, it was not a formal git rebase against upstream. It was an update/sync of the working local version to your GitHub.

4-Safer RST
Partially. We improved it a lot:

requires value == champion_name;
if the key is a readable string, it only replaces when it contains/starts with game_character_displayname_;
it does not compare the value against game_character_displayname_;
it does not use a hardcoded hash.

The caveat: for hash/int keys, there is still a fallback based on value == champion_name. It works, and it is what made the mod create _rose_loading_name_text, but it is still broader than ideal. The code itself has a TODO noting that this should be narrowed later to the exact loading-card display-name hash once that mapping is known.

So in summary: Chroma yes, locale yes, safe base yes in practice, RST functional but still with a technical follow-up pending before it fully matches the maintainer’s requested standard.
The primary path is still normal LCU skin selection. The stringtable override is a fallback for cases where the client accepts the selection but the loading screen still resolves the displayed name to the default champion name.

The fallback:

- finds `DATA\FINAL\Localized\Global.<locale>.wad.client` using the detected LCU locale;
- patches matching stringtable entries where the value equals the champion name;
- creates an extra CSLOL mod named `_rose_loading_name_text`;
- adds that mod to the overlay together with the selected skin mod.

Current follow-up:

- the integer/hash fallback is intentionally functional but broader than ideal;
- it should be narrowed later to the exact loading-card display-name hash once that mapping is known.

## Requirements

- Windows 10 or Windows 11
- League of Legends installed
- Run Rose as Administrator when needed
- Extract the ZIP before running `Rose.exe`

## Build Verification

The latest local build was validated with:

- `build_pyinstaller.py` using `.venv-build`
- `Rose.exe` generated in `dist\Rose`
- required CSLOL tools present:
  - `mod-tools.exe`
  - `wad-extract.exe`
  - `wad-make.exe`

Runtime test logs confirmed:

- `[LoadingName] Created stringtable mod`
- `_rose_loading_name_text` included in `--mods`
- `INJECTION COMPLETED`

## Legal Notice

This project is not affiliated with Riot Games. Use at your own risk. Rose changes local client-side assets only and does not provide gameplay advantage.
