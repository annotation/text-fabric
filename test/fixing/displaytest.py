import marimo

__generated_with = "0.4.2"
app = marimo.App(width="full")


@app.cell
def __():
    from tf.app import use
    return use,


@app.cell
def __(use):
    A = use("ETCBC/bhsa")
    return A,


@app.cell
def __(A):
    F = A.api.F
    return F,


@app.cell
def __(A, F):
    A.pretty(F.otype.s("sentence")[0], withNodes=True, highlights={3: "", 651573: "goldenrod"})
    return


@app.cell
def __():
    i = 1
    return i,


@app.cell
def __(i):
    print(i)
    return


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
