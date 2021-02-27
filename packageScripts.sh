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
# LAST EDITED:      02/20/2021
###

read -r -d '' USAGE <<EOF
Usage: packageScripts.sh <command>

Commands:
  upload                 Run the full packaging procedure and upload the wheels
                         archive to the PyPI server
  build                  Build the SPA and copy the build artifacts to the
                         Django app (executed by 'upload' command)
EOF

usage() {
    printf '%s\n' "$USAGE"
}

USER=edtwardy
SERVER=edtwardy.hopto.org
PORT=5000
LOCATION=/var/www/$SERVER/pypi/web-publishing/
PACKAGE=web_publishing.egg-info

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

command=$1
shift
case $command in
    upload)
        upload
        ;;
    build)
        build
        ;;
    *)
        usage
        ;;
esac

###############################################################################
