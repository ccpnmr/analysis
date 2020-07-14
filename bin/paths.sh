#!/usr/bin/env bash

export _PARENT_FONTCONFIG_FILE=${FONTCONFIG_FILE}
export _PARENT_FONTCONFIG_PATH=${FONTCONFIG_PATH}
export _PARENT_QT_PLUGIN_PATH=${QT_PLUGIN_PATH}
export _PARENT_QT_LOGGING_RULES=${QT_LOGGING_RULES}

export ANACONDA3="${CCPNMR_TOP_DIR}"/miniconda
export PYTHONPATH="${CCPNMR_TOP_DIR}"/src/python:"${CCPNMR_TOP_DIR}"/src/c
export FONTCONFIG_FILE="${ANACONDA3}"/etc/fonts/fonts.conf
export FONTCONFIG_PATH="${ANACONDA3}"/etc/fonts
export QT_PLUGIN_PATH=${QT_PLUGIN_PATH}:"${ANACONDA3}"/plugins
export QT_LOGGING_RULES="*=false;qt.qpa.*=false"

if [[ "$(uname -s)" == "Darwin" ]]; then
  export DYLD_FALLBACK_LIBRARY_PATH=/System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/ImageIO.framework/Versions/A/Resources:
  export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}"${ANACONDA3}"/lib:
  export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}"${ANACONDA3}"/lib/python3.5/site-packages/PyQt5:
  export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}${HOME}/lib:/usr/local/lib:/usr/lib
fi
