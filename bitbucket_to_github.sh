
git remote add github "https://$GITHUB_TOKEN@github.com/ccpnmr/${1}"
git checkout $BITBUCKET_BRANCH
git fetch --unshallow
git push --force github ${2}