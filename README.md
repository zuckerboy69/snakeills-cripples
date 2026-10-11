# Snake Eater: Operation Long Ramp

A Katawa Shoujo × METAL GEAR SOLID Δ: SNAKE EATER mashup. **Status: source only. Not yet run in either game, and not published.**

It's 1964. Naked Snake HALO-jumps into "Yamakugrad", a Soviet closed city, and enrolls at Yamaku Academy under Hisao Nakai's name.
Emi, Hanako, Lilly, Rin and Shizune (with Misha translating) turn out to be the **Kerb Unit**. Their 26-year plan,
*Operation Long Ramp*, is to make the West spend a fortune on ramps, Braille and bus lifts: the Americans with Disabilities Act, drafted in Russian.

## What the player gets
- A new 8-scene chapter inside Katawa Shoujo (host game), started from KS's **Mods** menu. It is written in KS's own visual novel format,
  with KS's own characters, sprites, backgrounds, music and sound effects, all read from the player's KS install.
- **Camo, any time:** press **C** (or click the CAMO badge) during any line to switch between 8 camos. Whoever Snake is talking to
  reacts on the spot, and then the interrupted line carries on. There are 56 written reactions. Lilly is blind, so she reacts to the *sound*.
  Shizune is deaf, so she signs and Misha "translates". From the third swap on, they complain about the swapping itself.
- **Codec calls** from Major Zero and Para-Medic, with MGS Δ's codec ring, open and close sounds and the portraits read from the player's own MGS Δ install.
- A cliffhanger ending.
- Single player.

## Required games
- **Katawa Shoujo** (host): the mod installs into `game/mods/snake_eater/`.
- **METAL GEAR SOLID Δ: SNAKE EATER** (companion): Melty passes its folder as `SK_MGS_DIR`. The camo icons, codec sounds and portraits
  are read from it into a local cache on the player's PC. No MGS Δ or KS file is in this repo or in the upload.

## How it's built
The design lives in JSON sheets in `design/` (characters, camos, reactions, scenes, codec, mgs_assets, hooks), with one row per thing.
- `python3 tools/preflight.py` cross-checks every cell and reference against the sheets and against KS's real names
  (`tools/ks_names.json`). `--release` also requires every MGS Δ asset path and hook to be verified.
- `python3 tools/generate.py` writes `mod/snake_eater/sk_data.rpy` and `sk_chapter.rpy` from the sheets.
- `python3 tools/lint_rpy.py` runs static checks for when no Ren'Py runtime is available.
- `mod/snake_eater/sk_core.rpy` is the handwritten runtime: the camo picker, the HUD, the codec overlay, the MGS Δ bridge and the Mods menu entry.

## Still to do before release
See `MODLOG.md`. In short: confirm the MGS Δ install layout and asset paths on a PC that has it, build the extractor that fills
`mgs_cache/` from the player's MGS Δ install, run the chapter in KS, then validate the Melty recipe (`melty.draft.json`) and test it there.

## Credits and licence
- Mod script and code: the project author, built with Claude Code (AI-assisted).
- Katawa Shoujo © Four Leaf Studios (CC BY-NC-ND 3.0). Its content is used from the player's own install only.
- METAL GEAR SOLID Δ: SNAKE EATER © KONAMI. Its content is used from the player's own install only.
- Fan-made and non-commercial. Not affiliated with Four Leaf Studios or KONAMI.
- Content licence and remix permission: **not yet chosen**.
