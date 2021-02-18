#!/usr/bin/env bash

export CONDA="${CCPNMR_TOP_DIR}"/miniconda
export PYTHONPATH="${CCPNMR_TOP_DIR}"/src/python:"${CCPNMR_TOP_DIR}"/src/c
export FONTCONFIG_FILE="${CONDA}"/etc/fonts/fonts.conf
export FONTCONFIG_PATH="${CONDA}"/etc/fonts
export QT_PLUGIN_PATH=${QT_PLUGIN_PATH}:"${CONDA}"/plugins
export QT_LOGGING_RULES="*=false;qt.qpa.*=false"

if [[ "$(uname -s)" == "Darwin" ]]; then
  export DYLD_FALLBACK_LIBRARY_PATH=/System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/ImageIO.framework/Versions/A/Resources:
  export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}"${CONDA}"/lib:
  export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}"${CONDA}"/lib/python3.8/site-packages/PyQt5:
  export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}${HOME}/lib:/usr/local/lib:/usr/lib
fi
