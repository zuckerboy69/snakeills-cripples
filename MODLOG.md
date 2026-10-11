# MODLOG: Snake Eater: Operation Long Ramp

## Decisions (from the interview)
- Host: Katawa Shoujo (primary). Companion: MGS Δ: SNAKE EATER. Single player. Visual novel format is unchanged.
- Scope: a new 20-30 min infiltration chapter at a Soviet Yamaku. Extras: codec calls. Camo: a hotkey picker usable during any line.
  Ending: a fixed mission cliffhanger.

## Route
- KS is Ren'Py (1.3.x on Ren'Py 6.99/Py2; KS: Re-Engineered on Ren'Py 8/Py3). Established mod route: loose `.rpy` files under `game/`,
  registered in KS's own `mods` dict (Mods menu → `Start(label)`). Confirmed in the KSRE source:
  definitions.rpy:16 and screens.rpy:1217-1254, using the example mod `game/mods/pxt`.
- Sprites, backgrounds, music and sfx are KS's own image tags and aliases (images.rpy make_sprites / bgs loop, ost.rpy ks_music).
  Their names were checked against `tools/ks_names.json`.
- The code avoids `default`, f-strings and `removesuffix` so it can parse on both Ren'Py generations.
- MGS Δ (Unreal Engine 5): its content is read from the player's install into `game/mods/snake_eater/mgs_cache/`. The plan is a bundled
  extractor (CUE4Parse, Apache-2.0, plus vgmstream for Wwise audio). It is **not built yet**, because neither the game nor the .NET SDK was available in the build sandbox.

## Verified
- preflight: 0 errors (dev mode). lint_rpy: 0 errors across 72 labels, and the lint was mutation-tested to make sure it catches errors.

## Not verified / open
1. MGS Δ install layout: exe, Paks folder, whether the paks are AES-encrypted, and the asset paths for 8 camo icons, the camo-change sfx,
   codec ring/open/close sounds and the Snake/Zero/Para-Medic codec portraits (`design/mgs_assets.json`, all `source_path` null).
2. The extractor (`tools/sk_extract`): needs item 1 first.
3. A run in a real KS install: the Mods menu entry, the C-key picker via `call_in_new_context` mid-line, the codec overlay,
   and which KS edition the player has (1.3.1 vs Re-Engineered: exe name, whether the `mods` dict exists).
4. Melty: melty.gg was unreachable from the build sandbox, so search_mashups, game_info, validate_recipe, one_click_check
   and test_release have not run. The recipe is a draft with placeholder slugs.
5. Listing: content licence and remix choice not set. No screenshot yet (needs a real run).
