#!/bin/bash


# $1 - tool name, $2 - version string, or keyword: 'any'
toolOnPathAndRightVer () {
    [[ $(type -P "$1") ]] && echo "  $1 is on PATH"  || ( echo "  $1 is NOT in PATH" && return 1 )
    ([[ -z $2 ]] || [[ $2 == "any" ]]) && return 0
    
    ver=$($1 -v)
    [[ "$ver" == "$2" ]] && echo "  $ver okay" && return 0
    echo "  $ver is wrong version" && return 1
}


echo "PNMP"
toolOnPathAndRightVer 'pnpm' '3.5.3'; echo ""

echo "NODE"
toolOnPathAndRightVer 'node' 'v12.18.3'; echo ""

echo "PYTHON3"
toolOnPathAndRightVer 'python3' ; echo ""

echo "JQ"
toolOnPathAndRightVer 'jq' ; echo ""

echo "DOCKER"
toolOnPathAndRightVer 'docker' ; echo ""

echo "GIT"
toolOnPathAndRightVer 'git' ; echo ""
