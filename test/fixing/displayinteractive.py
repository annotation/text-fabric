import marimo

__generated_with = "0.4.2"
app = marimo.App(width="full")


@app.cell
def __(A, F, x):
    A.pretty(F.otype.s("sentence")[x.value])
    return


@app.cell
def __(mo):
    x = mo.ui.slider(1,9)
    x
    return x,


@app.cell
def __():
    from tf.app import use
    import marimo as mo
    return mo, use


@app.cell
def __(use):
    A = use("ETCBC/bhsa")
    return A,


@app.cell
def __(A):
    F = A.api.F
    return F,


if __name__ == "__main__":
    app.run()
