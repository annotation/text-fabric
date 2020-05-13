#!/bin/sh

function givehelp {
    echo "./releaseapps.sh <app> <tag> <name> <msg>"
    echo ""
    echo "Make a new release for <app> with <tag>, <name>, <msg>"
    echo "If <app> == 'all', then all apps will be released"
    echo ""
}

# Create a new release for all or some  apps

annotationdir=~/github/annotation
tooldir=${annotationdir}/text-fabric/tools
tool="${tooldir}/release.py"

if [[ "$1" == "" ]]; then
    givehelp
    echo "Provide an app (or 'all'), a tag and release name and message"
    exit
else
    app="$1"
    shift
fi
if [[ "$1" == "" ]]; then
    givehelp
    echo "Provide a tag and release name and message"
    exit
else
    tag="$1"
    shift
fi
if [[ "$1" == "" ]]; then
    givehelp
    echo "Provide release name and message"
    exit
else
    name="$1"
    shift
fi
if [[ "$1" == "" ]]; then
    givehelp
    echo "Provide release message"
    exit
else
    msg="$1"
    shift
fi
cd $annotationdir

if [[ "$app" == "all" ]]; then
    echo "All apps: commit changes and make new release"
    apps=`ls -d app-*`
else
    echo "${app}: commit changes and make new release"
    apps=`ls -d app-$app`
fi
for app in $apps
do
    echo "o-o-o [$app] o-o-o"
    cd $annotationdir/$app
    git add --all .
    git commit -m "$msg"
    git push origin master
    python3 $tool annotation $app $tag "$name" "$msg"
done
echo "done"

