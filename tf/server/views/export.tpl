<html> 
    <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>{{jobName}}</title>
        <meta name="application-name" content="Text-Fabric Search Box"/>
        <link rel="shortcut icon" href="/server/static/favicon.ico">
<style type="text/css">
body {
    padding: 2rem;
}
a:link, a:visited {
    text-decoration: None;
}

*,
*:before,
*:after {
	box-sizing: border-box;
}

div.tline,.aline {
    text-align: center;
}
div.tline {
    font-size: x-large;
    font-style: italic;
    padding: 2rem;
}
div.aline {
    font-size: large;
    font-weight: bold;
    padding: 1rem;
}
pre.sections {
	font-size: medium;
	font-family: monospace;
	width: calc(100% - 1rem);
	margin: 0.3rem 0.3rem;
    background-color: #ddeeff;
}
pre.tuples {
	font-size: medium;
	font-family: monospace;
	width: calc(100% - 1rem);
	margin: 0.3rem 0.3rem;
    background-color: #eeffdd;
}
pre.template {
	font-size: medium;
	font-family: monospace;
	width: calc(100% - 1rem);
	margin: 0.3rem 0.3rem;
    background-color: #ffeedd;
}
div.description {
	font-size: medium;
	font-family: sans-serif;
}
div.description a:link, div.description a:visited,
div.prov a:link, div.prov a:visited {
    color: #0000ee;
    text-decoration: underline;
}
div.dtheadrow {
    font-weight: bold;
    background-color: #dddddd;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
}
div.dtheadrow > span {
    margin: 0.2rem;
    padding: 0 0.5rem;
    border-right: 0.2rem solid #ffffff;
}
details.dtrow {
    border: 0.1rem solid #bbbbbb;
}

details.dtrow[open] {
    page-break-before: always;
    break-before: always;
}
details.dtrow[open] {
    page-break-after: always;
    break-after: always;
}
details.dtrow[open]+details.dtrow[open] {
    page-break-before: auto;
    break-before: auto;
}

details.dtrow > summary {
    background-color: #f0f0f0;
    margin: 0.2rem 0;
    padding: 0.2rem;
}
details.dtrow > summary > span {
    padding: 0 0.5rem;
    border-right: 0.2rem solid #bbbbbb;
}
div.pretty {
    width: 100%;
    margin: 0.2rem 0 0.5rem 0;
}
a.rwh {
    font-size: x-small;
    background-color: #ddeeff;
}
a.sq {
    font-size: small;
    background-color: #eeffdd;
}
a.nd {
    font-size: small;
    background-color: #eeffdd;
}
a.rwh:link,a.rwh:visited,
a.sq:link,a.sq:visited,
a.nd:link,a.nd:visited {
    color: #444444;
} 
div.colofon {
    display: flex;
    flex-flow: row nowrap;
    justify-content: space-between;
    align-items: flex-start;
}
img.hdlogo {
    flex: 0 0 auto;
    max-width: 5rem;
    height: 4rem;
}
img.mainlogo {
    max-width: 15rem;
    height: 5rem;
}
div.hdlinks {
    flex: 0 1 auto;
    display: flex;
    flex-flow: row wrap;
    justify-content: space-around;
    align-items: baseline;
}
div.hdlinks > a {
    flex: 1 1 4rem;
    background-color: #eeeeff;
    border-radius: 0.4rem;
    border: 0.1rem solid #cccccc;
    padding: 0.2rem 0.2rem;
    margin: 0.2rem 0.2rem;
    text-align: center;
    text-decoration: none;
}
div.prov {
    margin: 2rem;
    padding: 1rem;
    border: 0.1rem solid #aaaaaa;
}
div.pline {
    display: flex;
    flex-flow: row nowrap;
    justify-content: stretch;
    align-items: baseline;
}
div.p2line {
    margin-left: 2em;
    display: flex;
    flex-flow: row nowrap;
    justify-content: stretch;
    align-items: baseline;
}
div.pname {
    flex: 0 0 5rem;
    font-weight: bold;
}
div.pval {
    flex: 1 1 auto;
}
</style>
        {{!css}}
    </head>
    <body>
        <div class="colofon">
            {{!colofon}}
        </div>
        <div class="prov">
            {{!provenance}}
        </div>
        <div class="header">
            <div class="tline">{{title}}</div>
            <div class="aline">{{author}}</div>
        </div>
        <div class="description">
            {{!descriptionMd}}
        </div>
        <hr/>
        <div>
            <pre class="tuples">{{tuples}}</pre>
        </div>
        <div>
            <pre class="template">{{searchTemplate}}</pre>
        </div>
        <div class="table">
            {{!table}}
        </div>
        <hr/>
        <div>
            <p>
               <a target="_blank" href="https://dans.knaw.nl/en">DANS (Data Archiving and Networked Services</a>
              <img class="mainlogo" src="/server/static/dans.png" align="right"/>
            </p>
        </div>
    </body>
</html>
