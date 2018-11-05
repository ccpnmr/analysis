include ../../environment.txt
# above gives CC, LINK, MAKE, CC_FLAGS, LINKFLAGS, ..._INCLUDE_FLAGS, ..._LIB_FLAGS, ..._LIB

NPY_CLIBRARY_OBJS = \
	npy_clibrary.$(OBJ_SUFFIX)

ALL_INCLUDE_FLAGS = $(PYTHON_INCLUDE_FLAGS) $(GL_INCLUDE_FLAGS)

ALL_LIB_FLAGS = $(PYTHON_LIB_FLAGS) $(GL_LIB_FLAGS)

ALL_LIB = $(PYTHON_LIB) $(GL_LIB) $(MATH_LIB)

all: Clibrary.$(DYLIB_SUFFIX)

Clibrary.$(DYLIB_SUFFIX): $(NPY_CLIBRARY_OBJS)
	$(LINK) $(LINK_FLAGS) $(SHARED_FLAGS) $(OUT_NAME) $(ALL_LIB_FLAGS) \
		$(NPY_CLIBRARY_OBJS) $(ALL_LIB)

npy_clibrary.$(OBJ_SUFFIX): npy_clibrary.c 
	$(CC) $(CC_FLAGS) $(ALL_INCLUDE_FLAGS) $(CO_NAME)

.c.$(OBJ_SUFFIX):;  $(CC) $(CC_FLAGS) $(CO_NAME)
 
clean:
	$(RM) *.$(OBJ_SUFFIX)
 
realclean: clean
	$(RM) *.$(DYLIB_SUFFIX)

