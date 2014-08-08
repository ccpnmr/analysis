include environment.txt

all: compile

compile: contour

contour:
	cd ccpnc/contour && $(MAKE)

clean: contour_clean

contour_clean:
	cd ccpnc/contour && $(MAKE) clean

realclean: contour_realclean

contour_realclean:
	cd ccpnc/contour && $(MAKE) realclean

