# Linux fpic option: replace -fPIC with -fpic if the latter works
# Comment out "LINUX_Z_RELRO =" if -z relro is not supported
# These options are needed to avoid the following SELinux message:
# "Error: cannot restore segment prot after reloc: Permission denied"
# In addition, inchi.map restricts set of expoorted from .so
# functions to those which belong to InChI API
include ../environment.txt

ifndef windir
#LINUX_MAP = ,--version-script=libinchi.map
ifdef ISLINUX
LINUX_FPIC  = -fPIC
LINUX_Z_RELRO = ,-z,relro
endif
endif

# === version ===
# MAIN_VERSION = .1
# VERSION = $(MAIN_VERSION).03.00
# VERSION = .1.03.00

# === executable & library directory ===
ifndef LIB_DIR
  LIB_DIR = .
endif

# === InChI Library name ===
ifndef INCHI_LIB_NAME
  INCHI_LIB_NAME = libinchi
endif
INCHI_LIB_PATHNAME = $(LIB_DIR)/$(INCHI_LIB_NAME)

# === Linker to create (Shared) InChI library ====
ifndef SHARED_LINK
  SHARED_LINK = $(CC) $(SHARED_FLAGS)
endif

# === C Compiler ===============
ifndef C_COMPILER
  C_COMPILER = gcc
endif

# === C Compiler Options =======
ifndef C_OPTIONS
  C_OPTIONS = -ansi $(FPIC_FLAG) $(OPT_FLAG) $(M32_FLAG) $(M64_FLAG) -c
  ifndef C_SO_OPTIONS
    C_SO_OPTIONS = $(FPIC_FLAG) $(M32_FLAG) $(M64_FLAG)
  endif
  ifndef C_MAIN_OPTIONS
    C_MAIN_OPTIONS = -DINCHI_LINK_AS_DLL
  endif
endif

ifdef windir
  INCHI_DEF        = $(INCHI_LIB_NAME).def
  SHARED_LINK_PARM =
endif


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

INCHI_LIB_OBJS = ichican2.o       ichicano.o \
                 ichicans.o       ichiisot.o \
                 ichilnct.o       ichimak2.o \
                 ichimake.o       ichimap1.o \
                 ichimap2.o       ichimap4.o \
                 ichinorm.o       ichiparm.o \
                 ichiprt1.o       ichiprt2.o \
                 ichiprt3.o       ichiqueu.o \
                 ichiring.o       ichisort.o \
                 ichister.o       ichitaut.o \
                 ichi_bns.o       inchi_dll.o \
                 ichiread.o       ichirvr1.o \
                 ichirvr2.o       ichirvr3.o \
                 ichirvr4.o       ichirvr5.o \
                 ichirvr6.o       ichirvr7.o \
                 inchi_dll_main.o runichi.o  \
                 inchi_dll_a.o    inchi_dll_a2.o  \
                 ikey_dll.o       ikey_base26.o  \
                 ichi_io.o                   \
                 sha2.o           strutil.o  \
                 util.o           inchi_py.o

# === InChI Library link rule =========

ifdef windir

$(INCHI_LIB_PATHNAME).a: $(INCHI_LIB_OBJS)
	$(SHARED_LINK) -o $(INCHI_LIB_PATHNAME).$(DYLIB_SUFFIX) $(INCHI_DEF) \
  $(INCHI_LIB_OBJS) \
  -Wl,--out-implib,$(INCHI_LIB_PATHNAME).a,-soname,$(INCHI_LIB_PATHNAME).$(DYLIB_SUFFIX)

else

$(INCHI_LIB_PATHNAME).so$(VERSION): $(INCHI_LIB_OBJS)
	$(SHARED_LINK) $(SHARED_LINK_PARM) $(C_SO_OPTIONS) -o \
  $(INCHI_LIB_PATHNAME).$(DYLIB_SUFFIX)$(VERSION) \
  $(PYTHON_LIB_FLAGS) $(PYTHON_LIB) \
  $(INCHI_LIB_OBJS)

endif

# === InChI Library compile rule =========

%.o: %.c
	$(CC) $(CC_FLAGS) $(C_OPTIONS) $(PYTHON_INCLUDE_FLAGS) $<

# Cleaning rules
clean:
	$(RM) *.$(OBJ_SUFFIX)
 
realclean: clean
	$(RM) *.$(DYLIB_SUFFIX)
