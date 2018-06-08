<html> 
    <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>Text-Fabric Search Box</title>
    <meta name="application-name" content="Text-Fabric Search Box"/>

    <link rel="stylesheet" href="/server/static/main.css"/>
    </head>
    <body>
        <div id="body"/>
        <!--<script src="/server/static/tf.js"></script>-->
        <form>
            <label>Query</label>
            <textarea name="searchTemplate">{{searchTemplate}}</textarea>
            <button type="submit">Go</button>
        </form>
        <div>
            <label>Results</label>
            <div class="resultlist">
            {{table}}
            </div>
        <div>
        <div>
            <label>Detail</label>
            <div class="resultitem"/>
        </div>
    </body>
</html>
