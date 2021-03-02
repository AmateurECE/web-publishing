#!/bin/sh
###############################################################################
# NAME:             packageScripts.sh
#
# AUTHOR:           Ethan D. Twardy <edtwardy@mtu.edu>
#
# DESCRIPTION:      Some tools to ease the packaging and building process.
#
# CREATED:          11/28/2020
#
# LAST EDITED:      03/01/2021
###

read -r -d '' USAGE <<EOF
Usage: packageScripts.sh <command>

Commands:
  upload                Run the full packaging procedure and upload the wheels
                        archive to the PyPI server
  build                 Build the wheels package using setuptools
  install               Install the package locally
EOF

usage() {
    printf '%s\n' "$USAGE"
}

USER=edtwardy
SERVER=edtwardy.hopto.org
PORT=5000
PACKAGE_NAME=web_publishing
LOCATION=/var/www/$SERVER/pypi/web-publishing/
PACKAGE=$PACKAGE_NAME.egg-info

upload() {
    printf '%s\n  %s\n    %s\n' "<!doctype html>" "<html>" "<body>" >index.html
    for file in `find dist ${PACKAGE} -type f`; do
        printf '      <a href="%s">%s</a>\n' $file $file >>index.html
    done
    printf '  %s\n%s\n' "</body>" "</html>" >>index.html

    rsync -e "ssh -p $PORT" -rv --delete dist ${PACKAGE} \
          index.html $USER@$SERVER:$LOCATION
}

build() {
    python3 setup.py sdist
}

install() {
    package=$(ls dist | sort | tail -n1)
    python3 -m pip install --user dist/$package
}

command=$1
shift
case $command in
    upload)
        upload
        ;;
    build)
        build
        ;;
    install)
        install
        ;;
    *)
        usage
        ;;
esac

###############################################################################
