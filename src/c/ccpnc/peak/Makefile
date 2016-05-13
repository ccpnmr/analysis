include ../../environment.txt
# above gives CC, LINK, MAKE, CC_FLAGS, LINKFLAGS, ..._INCLUDE_FLAGS, ..._LIB_FLAGS, ..._LIB

NPY_PEAK_OBJS = \
	gauss_jordan.$(OBJ_SUFFIX) \
	nonlinear_model.$(OBJ_SUFFIX) \
	npy_peak.$(OBJ_SUFFIX)

ALL_INCLUDE_FLAGS = $(PYTHON_INCLUDE_FLAGS)

ALL_LIB_FLAGS = $(PYTHON_LIB_FLAGS)

ALL_LIB = $(PYTHON_LIB) $(MATH_LIB)

all: Peak.$(DYLIB_SUFFIX)

Peak.$(DYLIB_SUFFIX): $(NPY_PEAK_OBJS)
	$(LINK) $(LINK_FLAGS) $(SHARED_FLAGS) $(OUT_NAME) $(ALL_LIB_FLAGS) \
		$(NPY_PEAK_OBJS) $(ALL_LIB)

npy_peak.$(OBJ_SUFFIX): npy_peak.c
	$(CC) $(CC_FLAGS) $(ALL_INCLUDE_FLAGS) $(CO_NAME)


.c.$(OBJ_SUFFIX):;  $(CC) $(CC_FLAGS) $(CO_NAME)
 
clean:
	$(RM) *.$(OBJ_SUFFIX)
 
realclean: clean
	$(RM) *.$(DYLIB_SUFFIX)

