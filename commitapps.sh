#!/bin/sh

function givehelp {
    echo "./commitapps.sh <app> <msg>"
    echo ""
    echo "Commit and push <app> with <tag>, <name>, <msg>"
    echo "If <app> == 'all', then all apps will be committed and pushed"
    echo ""
}

# Create a new release for all or some  apps

annotationdir=~/github/annotation
tooldir=${annotationdir}/text-fabric/tools
tool="${tooldir}/release.py"

if [[ "$1" == "" ]]; then
    givehelp
    echo "Provide an app (or 'all') and a commit message"
    exit
else
    app="$1"
    shift
fi
if [[ "$1" == "" ]]; then
    givehelp
    echo "Provide commit message"
    exit
else
    msg="$1"
    shift
fi
cd $annotationdir

if [[ "$app" == "all" ]]; then
    echo "All apps: commit changes and push"
    apps=`ls -d app-*`
else
    echo "${app}: commit changes" and push
    apps=`ls -d app-$app`
fi
for app in $apps
do
    echo "o-o-o [$app] o-o-o"
    cd $annotationdir/$app
    git add --all .
    git commit -m "$msg"
    git push origin master
done
echo "done"

