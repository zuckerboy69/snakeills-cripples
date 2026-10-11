# Snake Eater: Operation Long Ramp - runtime core.
# Handwritten glue for the rows in design/hooks.json. Data and story come from
# sk_data.rpy / sk_chapter.rpy, which tools/generate.py builds from design/*.json.
# Written to run on both Katawa Shoujo 1.3.x (Ren'Py 6.99, Python 2) and
# KS: Re-Engineered (Ren'Py 8, Python 3).

init -1 python:
    import os

    SK_MOD_DIR = "mods/snake_eater"
    SK_CACHE_REL = SK_MOD_DIR + "/mgs_cache"

    # ---- hooks.mgs_bridge -------------------------------------------------
    # Melty passes the player's METAL GEAR SOLID Delta folder as SK_MGS_DIR.
    # tools/sk_extract reads the assets listed in SK_MGS out of that install
    # into mgs_cache/ on the player's own PC. Nothing from MGS Delta ships
    # with the mod.
    def sk_mgs_dir():
        return os.environ.get("SK_MGS_DIR", "")

    def sk_mgs_file(key):
        """Loadable path of an MGS Delta asset read from the player's install, or None."""
        row = SK_MGS.get(key)
        if row is None:
            return None
        rel = SK_CACHE_REL + "/" + row["cache_file"]
        if os.path.exists(os.path.join(config.gamedir, rel)):
            return rel
        return None

    def sk_mgs_ready():
        return all(sk_mgs_file(k) is not None for k in SK_MGS)

    # ---- hooks.characters ---------------------------------------------------
    def sk_char(who):
        return getattr(store, SK_CHARS[who]["speaker_var"])

    # ---- hooks.backgrounds / music / sfx -----------------------------------
    def sk_music(alias):
        f = getattr(store, "music_" + alias, None)
        if f:
            renpy.music.play(f, channel="music", fadeout=1.0, fadein=1.0)

    def sk_sfx(name):
        f = "sfx/%s.ogg" % name
        if renpy.loadable(f):
            renpy.sound.play(f)
            return
        f = getattr(store, "sfx_" + name, None)
        if f:
            renpy.sound.play(f)

    def sk_mgs_sound(key):
        f = sk_mgs_file(key)
        if f:
            renpy.sound.play(f)

    def sk_scene(bg, music, present, title):
        store.sk_present = list(present)
        store.sk_shown = {}
        store.sk_scene_title = title
        renpy.scene()
        renpy.show("bg " + bg)
        renpy.with_statement(dissolve)
        sk_music(music)

    # ---- hooks.sprites -----------------------------------------------------
    def sk_img(who, expr):
        c = SK_CHARS[who]
        if not c["sprite_tag"]:
            return None
        e = c[expr] if expr in SK_MOODS else expr
        for name in ("%s %s" % (c["sprite_tag"], e), "%s %s" % (c["sprite_tag"], c["neutral"])):
            if renpy.has_image(name):
                return name
        return None

    def sk_show(who, expr, pos=None):
        name = sk_img(who, expr)
        if name is None:
            return
        if pos is None:
            pos = store.sk_shown.get(who, "center")
        store.sk_shown[who] = pos
        at = getattr(store, pos, None)
        renpy.show(name, at_list=[at] if at is not None else [])

    def sk_expr(who, expr):
        # Change the face only of someone already on screen.
        if who in store.sk_shown:
            sk_show(who, expr)

    def sk_hide(who):
        c = SK_CHARS[who]
        if c["sprite_tag"]:
            renpy.hide(c["sprite_tag"])
        store.sk_shown.pop(who, None)

    # ---- hooks.camo_picker -------------------------------------------------
    def sk_open_picker():
        if store.sk_busy or not store.sk_active or getattr(store, "_menu", False):
            return
        store.sk_busy = True
        try:
            renpy.call_in_new_context("sk_camo_picker")
        finally:
            store.sk_busy = False
        renpy.restart_interaction()

    def sk_reaction_label(camo):
        """The reaction label for whoever is in front of Snake right now."""
        who = store.sk_present[0] if store.sk_present else "none"
        if who not in SK_REACTORS:
            who = "none"
        return who, "sk_react_%s_%s" % (who, camo)

    # ---- hooks.codec -------------------------------------------------------
    def sk_codec_open(call_id):
        c = SK_CODEC[call_id]
        store.sk_codec_call = call_id
        sk_mgs_sound(c["ring_asset"])
        renpy.show_screen("sk_codec", contact=c["contact"], freq=c["freq"])
        renpy.with_statement(Dissolve(0.3))
        sk_mgs_sound(c["open_asset"])

    def sk_codec_close():
        c = SK_CODEC[store.sk_codec_call]
        sk_mgs_sound(c["close_asset"])
        renpy.hide_screen("sk_codec")
        renpy.with_statement(Dissolve(0.3))
        store.sk_codec_call = None

    def sk_begin():
        store.sk_active = True
        store.sk_busy = False
        store.sk_camo = SK_CAMO_DEFAULT
        store.sk_swaps = {}
        store.sk_present = []
        store.sk_shown = {}
        store.sk_codec_call = None
        store.sk_scene_title = ""

    # Plain init assignments (not 'default') so this also parses on Ren'Py 6.99.
    sk_active = False
    sk_busy = False
    sk_camo = SK_CAMO_DEFAULT
    sk_swaps = {}
    sk_present = []
    sk_shown = {}
    sk_codec_call = None
    sk_scene_title = ""

# Speakers that KS doesn't have. Defined after KS's own init 0 'adv' so they
# share its text box style and quote marks.
init 10 python:
    sk_snake = Character(SK_CHARS["snake"]["display_name"], kind=adv, who_color=SK_CHARS["snake"]["color"])
    sk_zero = Character(SK_CHARS["zero"]["display_name"], kind=adv, who_color=SK_CHARS["zero"]["color"])
    sk_para = Character(SK_CHARS["paramedic"]["display_name"], kind=adv, who_color=SK_CHARS["paramedic"]["color"])

    # ---- hooks.mods_menu_entry ---------------------------------------------
    # KS keeps a 'mods' dict that its Mods menu lists; picking an entry
    # without its own menu calls Start(<key>).
    try:
        mods["snake_eater"] = "Snake Eater: Operation Long Ramp"
    except NameError:
        pass

screen sk_hud():
    zorder 50
    if sk_active and not _menu:
        key "c" action Function(sk_open_picker)
        key "C" action Function(sk_open_picker)
        frame:
            xalign 1.0
            yalign 0.0
            xmargin 12
            ymargin 12
            xpadding 10
            ypadding 8
            background Solid("#1a1f14cc")
            hbox:
                spacing 10
                $ sk_icon = sk_mgs_file(SK_CAMOS[sk_camo]["mgs_asset"])
                if sk_icon:
                    add im.Scale(sk_icon, 48, 48)
                textbutton ("CAMO: " + SK_CAMOS[sk_camo]["name"] + "  [[C]"):
                    action Function(sk_open_picker)
                    text_color "#d8d0a8"
                    text_hover_color "#ffffff"
                    text_size 22

screen sk_camo_select():
    modal True
    zorder 100
    add Solid("#000000b0")
    key "game_menu" action Return(None)
    frame:
        xalign 0.5
        yalign 0.5
        xpadding 24
        ypadding 20
        background Solid("#1a1f14f0")
        vbox:
            spacing 14
            text "CAMOUFLAGE" size 34 color "#d8d0a8" xalign 0.5
            grid 4 2:
                spacing 12
                for sk_c in SK_CAMO_ORDER:
                    button:
                        xsize 200
                        ysize 170
                        background (Solid("#55603f") if sk_c == sk_camo else Solid("#2c3322"))
                        hover_background Solid("#6b7a4e")
                        action Return(sk_c)
                        vbox:
                            xalign 0.5
                            spacing 6
                            $ sk_icon = sk_mgs_file(SK_CAMOS[sk_c]["mgs_asset"])
                            if sk_icon:
                                add im.Scale(sk_icon, 96, 96) xalign 0.5
                            else:
                                null height 96
                            text SK_CAMOS[sk_c]["name"] size 20 color "#ffffff" xalign 0.5
            text SK_CAMOS[sk_camo]["blurb"] size 18 color "#bdb58f" xalign 0.5
            textbutton "Back" action Return(None) xalign 0.5

screen sk_codec(contact, freq):
    zorder 40
    add Solid("#000000d8")
    hbox:
        xalign 0.5
        yalign 0.28
        spacing 60
        use sk_codec_portrait("snake")
        vbox:
            yalign 0.5
            spacing 8
            text "PTT" size 22 color "#7CFC9A" xalign 0.5
            text freq size 64 color "#7CFC9A" xalign 0.5
            text "MEMORY" size 18 color "#4f9e63" xalign 0.5
        use sk_codec_portrait(contact)

screen sk_codec_portrait(who):
    frame:
        xsize 260
        ysize 300
        background Solid("#0b2a14")
        $ sk_p = sk_mgs_file("codec_portrait_" + who)
        if sk_p:
            add im.Scale(sk_p, 248, 288) align (0.5, 0.5)
        else:
            text SK_CHARS[who]["display_name"] size 28 color "#7CFC9A" align (0.5, 0.5)

label sk_camo_picker:
    call screen sk_camo_select
    if _return and _return != sk_camo:
        $ sk_camo = _return
        $ sk_mgs_sound("camo_change_sfx")
        $ sk_who, sk_lbl = sk_reaction_label(sk_camo)
        $ sk_swaps[sk_who] = sk_swaps.get(sk_who, 0) + 1
        # From the third swap on, the person first complains about the swapping itself.
        if sk_who != "none" and sk_swaps[sk_who] >= 3 and SK_CHARS[sk_who]["repeat_line"]:
            $ sk_expr(sk_who, "angry")
            if SK_CHARS[sk_who]["signed_var"] and SK_CHARS[sk_who]["repeat_line"].startswith("[[ "):
                $ renpy.say(getattr(store, SK_CHARS[sk_who]["signed_var"]), SK_CHARS[sk_who]["repeat_line"][3:-2])
            else:
                $ renpy.say(sk_char(sk_who), SK_CHARS[sk_who]["repeat_line"])
        call expression sk_lbl
    return

# Entry point: KS's Mods menu starts this label.
label snake_eater:
    $ sk_begin()
    show screen sk_hud
    if not sk_mgs_ready():
        "{i}Snake Eater could not find the METAL GEAR SOLID Delta content it reads from your install. Start it from Melty so it can find your copy of MGS Delta.{/i}"
    call snake_eater_chapter
    $ sk_active = False
    hide screen sk_hud
    scene black with Dissolve(1.0)
    centered "{size=+10}TO BE CONTINUED{/size}"
    return
