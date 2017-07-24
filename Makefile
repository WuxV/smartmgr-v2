# =======================================
#  RPM
# =======================================

all: smartmgr
ifdef topdir
    RPMTOP=$(topdir)
else
    RPMTOP=$(shell bash -c "pwd -P")/rpmtop
endif

.PHONY: top
top:
	mkdir -p $(RPMTOP)/{RPMS,SRPMS,SOURCES,BUILD,SPECS,tmp}

_version=2.6.0
_release=1.phg
_commit=$(shell bash -c "git log -1 | head -1 | cut -d ' ' -f 2")

SPEC_DIR=spec

SPEC=smartmgr.spec
RPM_NAME=smartmgr

_dir=$(RPM_NAME)-$(_version)-$(_release)
TARBALL=$(_dir).tgz

.PHONY: tarball
tarball: top
	mkdir -p $(RPMTOP)/tmp/$(_dir)
	cp -a message $(RPMTOP)/tmp/$(_dir)/message
	cp -a clients $(RPMTOP)/tmp/$(_dir)
	cp -a service_mds $(RPMTOP)/tmp/$(_dir)
	cp -a service_ios $(RPMTOP)/tmp/$(_dir)
	cp -a files/service $(RPMTOP)/tmp/$(_dir)
	cp -a files/bin $(RPMTOP)/tmp/$(_dir)
	cp -a files/conf $(RPMTOP)/tmp/$(_dir)
	cp -a files/scripts $(RPMTOP)/tmp/$(_dir)
	cp -a pdsframe $(RPMTOP)/tmp/$(_dir)
	cp -a firstboot $(RPMTOP)/tmp/$(_dir)
	tar -czf $(RPMTOP)/SOURCES/$(TARBALL) -C $(RPMTOP)/tmp $(_dir)

.PHONY: srpm
srpm: tarball
	sed 's/^%define version/%define version $(_version)/;s/^%define rel/%define rel $(_release)/;s/^%define commit/%define commit $(_commit)/' \
		$(SPEC_DIR)/$(SPEC) > $(RPMTOP)/SPECS/$(SPEC)
	rpmbuild -bs --define="_topdir $(RPMTOP)" $(RPMTOP)/SPECS/$(SPEC)

.PHONY: smartmgr
smartmgr: srpm
	rpmbuild -bb --define="_topdir $(RPMTOP)" $(RPMTOP)/SPECS/$(SPEC)

.PHONY: clean
clean:
	find . -name "*.pyc" | xargs rm -rf
	make clean -C message
	rm -rf log
	rm -rf rpmtop
