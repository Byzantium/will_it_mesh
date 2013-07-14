.EXPORT_ALL_VARIABLES:

SHELL = /bin/bash
PRGNAM = will_it_mesh
VERSION =
MODORDER = 001-
DESTDIR?=$(PKGBUILDDIR)/$(PRGNAM)
## Variables that should be inherited from the parent Makefile or the environment
# MODULEDIR - the directory where finished modules should but stored
# ARCH - from the build environment
# BYZBUILD - Byzantium build version
# MODEXT - module extension (should be '.xzm')
##

# high level targets
.PHONY : build module install clean dist-clean

build:
	echo 'build is a noop in this Makefile'

install: byzantium_configd.py verify_operation.sh
	$(INSTALL_EXEC) $@ $(DESTDIR)/opt/byzantium/bin #FIXME give correct location

module: install
	dir2xzm $(DESTDIR) $(MODULEDIR)/$(MODORDER)$(PRGNAM)$(VERSION)-$(ARCH)-$(BYZBUILD).$(MODEXT)

clean: byzantium_configd.py verify_operation.sh
	# Do *not* remove $(DESTDIR)! If the build is for a monolithic module that will remove everything from every build.
	$(CLEAN) $(DESTDIR)/opt/byzantium/bin/$@ #FIXME give correct location

dist-clean: clean
	$(CLEAN) $(MODULEDIR)/$(MODORDER)$(PRGNAM)$(VERSION)-$(ARCH)-$(BYZBUILD).$(MODEXT)


