EGGNAME="text-fabric"; (for ip in $(dig +short pypi.org); do url="https://$ip/simple/${EGGNAME}/"; echo "Purging $url..."; curl -L -H 'Host: pypi.python.org' --insecure -XPURGE $url; done)
