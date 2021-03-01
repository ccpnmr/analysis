# Linux fpic option: replace -fPIC with -fpic if the latter works
# Comment out "LINUX_Z_RELRO =" if -z relro is not supported
# These options are needed to avoid the following SELinux message:
# "Error: cannot restore segment prot after reloc: Permission denied"
# In addition, inchi.map restricts set of expoorted from .so
# functions to those which belong to InChI API
include ../environment.txt
# above gives CC, LINK, MAKE, CC_FLAGS, LINKFLAGS, ..._INCLUDE_FLAGS, ..._LIB_FLAGS, ..._LIB

# === version ===
# MAIN_VERSION = .1
# VERSION = $(MAIN_VERSION).03.00
# VERSION = .1.03.00

# === executable & library directory ===
LIB_DIR = .

# === InChI Library name ===
INCHI_LIB_NAME = libinchi
INCHI_LIB_PATHNAME = $(LIB_DIR)/$(INCHI_LIB_NAME)

# === InChI Library Source files ============

INCHI_LIB_SRCS = ichican2.c       ichicano.c \
                 ichicans.c       ichiisot.c \
                 ichilnct.c       ichimak2.c \
                 ichimake.c       ichimap1.c \
                 ichimap2.c       ichimap4.c \
                 ichinorm.c       ichiparm.c \
                 ichiprt1.c       ichiprt2.c \
                 ichiprt3.c       ichiqueu.c \
                 ichiring.c       ichisort.c \
                 ichister.c       ichitaut.c \
                 ichi_bns.c       inchi_dll.c \
                 ichiread.c       ichirvr1.c \
                 ichirvr2.c       ichirvr3.c \
                 ichirvr4.c       ichirvr5.c \
                 ichirvr6.c       ichirvr7.c \
                 inchi_dll_main.c runichi.c  \
                 inchi_dll_a.c    inchi_dll_a2.c  \
                 ikey_dll.c       ikey_base26.c  \
                 ichi_io.c                   \
                 sha2.c           strutil.c  \
                 util.c           inchi_py.c

# === InChI Library Object files ============

INCHI_LIB_OBJS = ichican2.$(OBJ_SUFFIX)       ichicano.$(OBJ_SUFFIX) \
                 ichicans.$(OBJ_SUFFIX)       ichiisot.$(OBJ_SUFFIX) \
                 ichilnct.$(OBJ_SUFFIX)       ichimak2.$(OBJ_SUFFIX) \
                 ichimake.$(OBJ_SUFFIX)       ichimap1.$(OBJ_SUFFIX) \
                 ichimap2.$(OBJ_SUFFIX)       ichimap4.$(OBJ_SUFFIX) \
                 ichinorm.$(OBJ_SUFFIX)       ichiparm.$(OBJ_SUFFIX) \
                 ichiprt1.$(OBJ_SUFFIX)       ichiprt2.$(OBJ_SUFFIX) \
                 ichiprt3.$(OBJ_SUFFIX)       ichiqueu.$(OBJ_SUFFIX) \
                 ichiring.$(OBJ_SUFFIX)       ichisort.$(OBJ_SUFFIX) \
                 ichister.$(OBJ_SUFFIX)       ichitaut.$(OBJ_SUFFIX) \
                 ichi_bns.$(OBJ_SUFFIX)       inchi_dll.$(OBJ_SUFFIX) \
                 ichiread.$(OBJ_SUFFIX)       ichirvr1.$(OBJ_SUFFIX) \
                 ichirvr2.$(OBJ_SUFFIX)       ichirvr3.$(OBJ_SUFFIX) \
                 ichirvr4.$(OBJ_SUFFIX)       ichirvr5.$(OBJ_SUFFIX) \
                 ichirvr6.$(OBJ_SUFFIX)       ichirvr7.$(OBJ_SUFFIX) \
                 inchi_dll_main.$(OBJ_SUFFIX) runichi.$(OBJ_SUFFIX)  \
                 inchi_dll_a.$(OBJ_SUFFIX)    inchi_dll_a2.$(OBJ_SUFFIX)  \
                 ikey_dll.$(OBJ_SUFFIX)       ikey_base26.$(OBJ_SUFFIX)  \
                 ichi_io.$(OBJ_SUFFIX)                   \
                 sha2.$(OBJ_SUFFIX)           strutil.$(OBJ_SUFFIX)  \
                 util.$(OBJ_SUFFIX)           inchi_py.$(OBJ_SUFFIX)

# === InChI Library link rule =========

ALL_INCLUDE_FLAGS = $(PYTHON_INCLUDE_FLAGS)

ALL_LIB_FLAGS = $(PYTHON_LIB_FLAGS)

ALL_LIB = $(PYTHON_LIB) $(MATH_LIB)

all: $(INCHI_LIB_NAME).$(DYLIB_SUFFIX)

$(INCHI_LIB_NAME).$(DYLIB_SUFFIX): $(INCHI_LIB_OBJS)
	$(LINK) $(LINK_FLAGS) $(SHARED_FLAGS) $(OUT_NAME) $(ALL_LIB_FLAGS) \
		$(INCHI_LIB_OBJS) $(ALL_LIB)

# === InChI Library compile rule =========

# Special case, inchi_py requires include flags for numpy and python
inchi_py.$(OBJ_SUFFIX): inchi_py.c
	$(CC) $(CC_FLAGS) $(ALL_INCLUDE_FLAGS) $(CO_NAME)

# Generic case for all others
.c.$(OBJ_SUFFIX):;  $(CC) $(CC_FLAGS) $(CO_NAME)

# Cleaning rules
clean:
	$(RM) *.$(OBJ_SUFFIX)

realclean: clean
	$(RM) *.$(DYLIB_SUFFIX)
