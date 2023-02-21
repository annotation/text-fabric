import types
from tf.advanced.app import App


REND = "italic script intl unc cor rem rec alt vac".strip().split()


def fmt_layout(app, n, **kwargs):
    return app._wrapHtml(n)


class TfApp(App):
    def __init__(app, *args, **kwargs):
        app.fmt_layout = types.MethodType(fmt_layout, app)
        super().__init__(*args, **kwargs)
        app.rendFeatures = tuple((f, f[5:]) for f in app.api.Fall() if f.startswith("rend_"))
        app.isFeatures = tuple(("is_meta", "is_note"))

    def _wrapHtml(app, n):
        rendFeatures = app.rendFeatures
        isFeatures = app.isFeatures
        api = app.api
        F = api.F
        Fs = api.Fs
        material = F.ch.v(n)
        rClses = " ".join(f"r_ r_{r}" for (fr, r) in rendFeatures if Fs(fr).v(n))
        iClses = " ".join(ic for ic in isFeatures if Fs(ic).v(n))
        if rClses or iClses:
            material = f'<span class="{rClses} {iClses}">{material}</span>'
        return material
