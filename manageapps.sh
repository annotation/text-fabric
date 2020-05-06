#!/bin/sh

# Create a nnew branch, commit all changes to that branch
# and push the branch to GitHub.
# Do this for all TF-apps.

# branch v8dev

annotationdir=~/github/annotation

if [[ "$1" == "" ]]; then
    echo "Provide a branch and a commit message"
    exit
else
    branch="$1"
    shift
fi
if [[ "$1" == "" ]]; then
    echo "Provide a commit message"
    exit
else
    msg="$1"
    shift
fi
cd $annotationdir
echo "All apps: commit changes to branch '$branch' and push to GitHub"
for app in `ls -d app-*` tutorials
do
    echo "o-o-o [$app] o-o-o"
    cd $annotationdir/$app
    # git checkout -b "$branch"
    git add --all .
    git commit -m "$msg"
    git push origin "$branch" 
done
echo "done"

