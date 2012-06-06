%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?pyver: %define pyver %(%{__python} -c "import sys ; print sys.version[:3]")}

Name:           %(%{__python} setup.py --name)
Version:        %(%{__python} setup.py --version)
Release:        1%{?dist}
Summary:        %(%{__python} setup.py --description)

Group:          Development/Libraries
License:        %(%{__python} setup.py --license)
URL:            https://github.com/jsocol/django-ratelimit
Source0:        http://pypi.python.org/packages/source/d/django-ratelimit/%{name}-%{version}.tar.gz
Source1:        LICENSE
Source2:        README.rst

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel

# NB: update this when updating setup.py
Requires:       Django


%description
%(%{__python} setup.py --description)

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT

mkdir -p %{buildroot}/%{_docdir}/%{name}-%{version}
install -m 0644 %{SOURCE1} %{buildroot}/%{_docdir}/%{name}-%{version}
install -m 0644 %{SOURCE2} %{buildroot}/%{_docdir}/%{name}-%{version}


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc %{_docdir}/%{name}-%{version}/LICENSE
%doc %{_docdir}/%{name}-%{version}/README.rst
%{python_sitelib}/ratelimit/*

# Leaving these since people may want to rebuild on older dists
%if 0%{?fedora} >= 9 || 0%{?rhel} >= 6
    %{python_sitelib}/*.egg-info
%endif

%changelog

* Wed Jun 06 2012 Alexander Todorov <atodorov@nospam.otb.bg> - 0.1-1
- initial build
