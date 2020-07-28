if __name__ == "__main__":
    '''
    from aml import chapters
    from aml import globals_

    # defining chapters
    chap = (
        chapters.Chapter.from_path(
            "{}/al-hasyr".format(globals_.COMPOSITION_PATH),
            allowed_verses=(
                "opening",
                "5"
            ),
            title="kagem Karina"
        ),
        # chapters.Chapter.from_path("{}/an-nuh".format(globals_.COMPOSITION_PATH)),
    )

    # render chapters
    # [ch(render_each_instrument=False, render_verses=False) for ch in chap]
    [ch(render_each_instrument=False, render_verses=True) for ch in chap]
    # [ch(render_each_instrument=True, render_verses=True) for ch in chap]

    '''
    # render introduction
    from aml import introduction

    # making partbooks
