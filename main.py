if __name__ == "__main__":
    from aml import chapters
    from aml import globals_

    # defining chapters
    chap = (
        chapters.Chapter.from_path(
            "{}/al-hasyr".format(globals_.COMPOSITION_PATH),
            allowed_verses=(
                "opening",
                "1",
                "5",
                "closing",
            ),
            title="kagem Karina"
        ),
    )

    # render chapters
    [ch(render_each_instrument=False, render_verses=False) for ch in chap]

    # render introduction
    from aml import introduction
    introduction.make_introduction(make_graphics=False)

    # making partbooks & general score
    from aml import partbooks
    partbooks.make(chap)
