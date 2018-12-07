<html> 
	<head>
		<meta charset="utf-8"/>
		<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
		<title>TF-export {{dataSource}}-{{jobName}}</title>
		<meta name="application-name" content="Text-Fabric Search Box"/>
		<link rel="shortcut icon" href="/server/static/favicon.ico">
		<link rel="stylesheet" href="/server/static/base.css"/>
		<link rel="stylesheet" href="/server/static/highlight.css"/>
		<link rel="stylesheet" href="/server/static/export.css"/>
<style type="text/css">
	{{!css}}
</style>
	</head>
	<body>
		<div class="header">
			{{!colofon}}
		</div>
		<div class="prov">
			{{!provenance}}
		</div>
		<div class="headerdesc">
			<div class="titleline">{{title}}</div>
			<div class="authorline">{{author}}</div>
		</div>
		<div class="description">
			{{!descriptionMd}}
		</div>
		<hr/>
		<div>
			<pre class="sections">{{sections}}</pre>
		</div>
		<div id="sectionsTable" class="table">
			{{!sectionsTable}}
		</div>
		<hr/>
		<div>
				<pre class="tuples">{{tuples}}</pre>
		</div>
		<div id="tuplesTable" class="table">
			{{!tuplesTable}}
		</div>
		<hr/>
		<div>
				<pre class="query">{{query}}</pre>
			{{!setNames}}
		</div>
		<div id="queryTable" class="table">
			{{!queryTable}}
		</div>
		<hr/>
		<div>
			<p>
				<a
					target="_blank"
					href="https://dans.knaw.nl/en"
				>DANS (Data Archiving and Networked Services</a>
				<img
					class="mainlogo"
					src="/server/static/dans.png"
					align="right"
				/>
			</p>
		</div>
	</body>
</html>
