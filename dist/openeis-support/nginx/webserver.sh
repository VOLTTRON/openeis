#!/bin/sh
if [ -f /etc/nginx/nginx.conf ]; then
  WWWUSER="$(sed '/^\s*user\s/!d;s/\s*;\s*$//;s/^\S\+\s\+//' /etc/nginx/nginx.conf)"
fi
