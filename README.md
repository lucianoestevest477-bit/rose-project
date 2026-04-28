# Rose Project

## Download

### Baixar executavel atualizado

[Download Rose-Executavel-Atualizado.zip](https://github.com/lucianoestevest477-bit/rose-project/releases/download/v2026.04.28-loading-name-rst/Rose-Executavel-Atualizado.zip)

Esse ZIP contem o `Rose.exe` atualizado e a pasta `_internal` necessaria para o programa funcionar.

Como usar:

1. Baixe `Rose-Executavel-Atualizado.zip`.
2. Extraia a pasta.
3. Execute `Rose.exe`.

Nao baixe `Source code`; ele e apenas o codigo-fonte automatico do GitHub.

## Alteracoes desta versao

- Restaurado o fallback RST para mostrar o nome da skin selecionada na loading screen.
- Stringtable agora e locale-aware e usa o locale detectado pela LCU, como `pt_BR`.
- Corrigida a busca das WAD tools no build empacotado (`_internal\injection\tools`).
- `_rose_loading_name_text` e criado como mod extra e incluido no `--mods` junto com a skin.
- Mantido o fluxo normal de skin, chroma, custom mods e party mods.
- Removidos experimentos temporarios: `debug_loading_name_hash`, `debug_loading_name_log`, `debug_stop_overlay`, `LCU-RESTORE` e hash hardcoded.

## Status dos pedidos do maintainer

- Chroma label: corrigido para usar o nome base da skin, sem sufixo da cor.
- Idioma: corrigido para usar `state.lcu_language` e buscar `Global.<locale>.wad.client`.
- Base/security fix: preservada na versao atual publicada.
- RST: funcional e mais seguro, exigindo `value == champion_name`; ainda ha follow-up tecnico para estreitar o fallback de hash/int para o hash exato do loading-card quando esse mapeamento for conhecido.

## Verificacao

- Build gerado com `.venv-build` usando `build_pyinstaller.py`.
- `Rose.exe`, `mod-tools.exe`, `wad-extract.exe` e `wad-make.exe` verificados no `dist`.
- Log de teste confirmou `[LoadingName] Created stringtable mod`, `_rose_loading_name_text` no `--mods` e `INJECTION COMPLETED`.

## Integridade

SHA256 do ZIP:

`DB5D000B3F6058E656F304804A7033CAB8673892766C26953AD97392A5CF521F`

## Aviso legal

Este projeto nao e afiliado a Riot Games. Use por sua conta e risco. Rose altera apenas assets locais do cliente e nao oferece vantagem de gameplay.
