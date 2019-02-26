#!/usr/bin/env bash

export ANACONDA3="${CCPNMR_TOP_DIR}"/miniconda
export PYTHONPATH="${CCPNMR_TOP_DIR}"/src/python:"${CCPNMR_TOP_DIR}"/src/c
export FONTCONFIG_FILE="${ANACONDA3}"/etc/fonts/fonts.conf
export FONTCONFIG_PATH="${ANACONDA3}"/etc/fonts
export QT_PLUGIN_PATH=${QT_PLUGIN_PATH}:"${ANACONDA3}"/plugins

if [[ `uname` == 'Darwin' ]]; then
  export DYLD_FALLBACK_LIBRARY_PATH=/System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/ImageIO.framework/Versions/A/Resources:
  export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}"${ANACONDA3}"/lib:
  export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}"${ANACONDA3}"/lib/python3.5/site-packages/PyQt5:
  export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}${HOME}/lib:/usr/local/lib:/usr/lib
fi
