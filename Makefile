clean:
	rm -rf noarch/ BUILDROOT/

distclean: clean
	rm -f *.rpm

rpm:
	rpmbuild --define "_topdir %(pwd)" \
	--define "_builddir /tmp" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir %{_topdir}" \
	--define "_sourcedir %{_topdir}" \
	-ba django-ratelimit.spec

	mv noarch/*.rpm .

rpm-test:
	rpmlint -i *.rpm *.spec
