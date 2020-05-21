# Fabric

The main class that works the core API is `tf.fabric.Fabric`.

It is responsible for feature data loading and saving.

!!! note "Tutorial"
    The tutorials for specific [annotated corpora](https://github.com/annotation)
    put the Text-Fabric API on show for vastly different corpora.

!!! note "Generic API versus apps"
    This is the API of Text-Fabric in general.
    Text-Fabric has no baked in knowledge of particular corpora.

    However, Text-Fabric comes with several *apps* that make working
    with specific `tf.about.corpora` easier.
    The result of those apps (which may only exist of a (zero-content) *config.yaml* file,
    is available through the advanced API: `A`, see `tf.app`.
