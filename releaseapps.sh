#!/bin/sh

# Create a new release for all apps

annotationdir=~/github/annotation
tooldir=${annotationdir}/text-fabric/tools
tool="${tooldir}/release.py"

if [[ "$1" == "" ]]; then
    echo "Provide a tag and release name and message"
    exit
else
    tag="$1"
    shift
fi
if [[ "$1" == "" ]]; then
    echo "Provide release name and message"
    exit
else
    name="$1"
    shift
fi
if [[ "$1" == "" ]]; then
    echo "Provide release message"
    exit
else
    msg="$1"
    shift
fi
cd $annotationdir
echo "All apps: commit changes and make new release"
for app in `ls -d app-*`
do
    echo "o-o-o [$app] o-o-o"
    cd $annotationdir/$app
    git add --all .
    git commit -m "$msg"
    git push origin master
    python3 $tool annotation $app $tag "$name" "$msg"
done
echo "done"

