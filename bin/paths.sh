#!/usr/bin/env bash

export CONDA="${CCPNMR_TOP_DIR}"/miniconda
export CCPN_PYTHON="/bin/lib/CcpNmrAnalysis"
export PYTHONPATH="${CCPNMR_TOP_DIR}"/src/python:"${CCPNMR_TOP_DIR}"/src/c
export PYTHONHOME="${CCPNMR_TOP_DIR}"/miniconda
export PYTHONUNBUFFERED=1
export PYTHONUTF8=1
export FONTCONFIG_FILE="${CONDA}"/etc/fonts/fonts.conf
export FONTCONFIG_PATH="${CONDA}"/etc/fonts
export QT_PLUGIN_PATH=${QT_PLUGIN_PATH}:"${CONDA}"/plugins
export QT_LOGGING_RULES="*=false;qt.qpa.*=false"

if [[ "$(uname -s)" == "Darwin" ]]; then
    export DYLD_FALLBACK_LIBRARY_PATH=/System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/ImageIO.framework/Versions/A/Resources:
    export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}"${CONDA}"/lib:
    export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}"${CONDA}"/lib/python${MAC_PYTHON_VERSION}/site-packages/PyQt5:
    export DYLD_FALLBACK_LIBRARY_PATH=${DYLD_FALLBACK_LIBRARY_PATH}${HOME}/lib:/usr/local/lib:/usr/lib
fi

# set the GL-platform-type if Ubuntu22.04
OSFILE=/etc/os-release
if [[ $(uname -s) == "Linux" && -f ${OSFILE} && $(grep VERSION_ID ${OSFILE}) == *"22.04"* ]]; then
    export PYOPENGL_PLATFORM=x11
fi

# check that the Darwin cpu-type matches the build-type, conda is intel/amd specific
if [[ ${NO_PROCESSOR_INFO} != 1 && $(uname) == Darwin* ]]; then
    # skip if the NO_PROCESSOR_INFO flag is defined (and == 1)
    # otherwise causes extraneous info to be printed in nef-pipelines output
    cpu_type=$(uname -m)
    case $(uname -m) in
        aarch64 | ppc64le | arm64) ;; # pass
        *) cpu_type="64" ;;
    esac
    build_file="${CCPNMR_TOP_DIR}/config/os-build-version"
    build_type=$([[ -f "${build_file}" ]] && grep CPU_TYPE "${build_file}" | sed -e 's/^CPU_TYPE=//')
    if [[ ${cpu_type} == "arm64" ]]; then
        # build-type is defined in the os-build-version file
        if [[ ! ${build_type} ]]; then
            rosetta=$(sysctl -in sysctl.proc_translated)
            if [[ ${rosetta} != *1* ]]; then
                echo "You are using an Apple-Silicon processor (M-series)." >&2
                echo "Your version of CcpnmrAnalysis predates the download for version 3.2.2 and" >&2
                echo "will be an Intel distribution." >&2
                echo "If you are experiencing issues you may not have Rosetta installed or" >&2
                echo "you should download an Apple-Silicon distribution." >&2
                echo "Please see the website https://www.ccpn.ac.uk for more details." >&2
                echo "Information on Rosetta can be found at https://support.apple.com/en-us/102527." >&2
            fi
        elif [[ ${build_type} != "arm64" ]]; then
            echo "You are using an Apple-Silicon processor (M-series) and this is an Intel distribution." >&2
            echo "If you are experiencing issues you may not have Rosetta installed or" >&2
            echo "you should download an Apple-Silicon distribution." >&2
            echo "Please see the website https://www.ccpn.ac.uk for more details." >&2
            echo "Information on Rosetta can be found at https://support.apple.com/en-us/102527." >&2
        fi
    else
        if [[ ! ${build_type} ]]; then
            echo "You are using an Intel processor." >&2
            echo "If you are experiencing issues, see the website https://www.ccpn.ac.uk for more details." >&2
        elif [[ ${build_type} == "arm64" ]]; then
            echo "You are using an Intel processor and this is an Apple-Silicon (M-series) distribution." >&2
            echo "Please download an Intel distribution from the website https://www.ccpn.ac.uk." >&2
        fi
    fi
fi
