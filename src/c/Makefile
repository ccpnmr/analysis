include environment.txt

all: compile

compile: contour peak inchicode clibrary

contour:
	cd ccpnc/contour && $(MAKE)

peak:
	cd ccpnc/peak && $(MAKE)

inchicode:
	cd inchi && $(MAKE)

clibrary:
	cd clibrary && $(MAKE)

clean: contour_clean peak_clean inchi_clean clibrary_clean

contour_clean:
	cd ccpnc/contour && $(MAKE) clean

peak_clean:
	cd ccpnc/peak && $(MAKE) clean

inchi_clean:
	cd inchi && $(MAKE) clean

clibrary_clean:
	cd clibrary && $(MAKE) clean

realclean: contour_realclean peak_realclean inchi_realclean clibrary_realclean

contour_realclean:
	cd ccpnc/contour && $(MAKE) realclean

peak_realclean:
	cd ccpnc/peak && $(MAKE) realclean

inchi_realclean:
	cd inchi && $(MAKE) realclean

clibrary_realclean:
	cd clibrary && $(MAKE) realclean
