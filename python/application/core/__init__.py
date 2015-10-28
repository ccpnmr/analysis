# # Necessary to make sure loads are in the right order
# NBNB if anything it is application.core that depends on ccpnmr, not the other way around
# But it is coded so that the the graphics classes are imported in ccpnmr
# NBNB TBD FIXME maybe move actual instantiated classes to application.core?
import application
del application