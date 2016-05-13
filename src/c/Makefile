include environment.txt

all: compile

compile: contour peak

contour:
	cd ccpnc/contour && $(MAKE)

peak:
	cd ccpnc/peak && $(MAKE)

clean: contour_clean peak_clean

contour_clean:
	cd ccpnc/contour && $(MAKE) clean

peak_clean:
	cd ccpnc/peak && $(MAKE) clean

realclean: contour_realclean peak_realclean

contour_realclean:
	cd ccpnc/contour && $(MAKE) realclean

peak_realclean:
	cd ccpnc/peak && $(MAKE) realclean

