%{?scl:%scl_package eclipse-emf}
%{!?scl:%global pkg_name %{name}}
%{?java_common_find_provides_and_requires}

# The core sub-package must be archful because it is required to be in
# libdir by the platform, but we have no natives, so suppress debuginfo
%global debug_package %{nil}

%global eclipse_dropin %{_datadir}/eclipse/dropins

# 2.11.0 was released but not tagged in yet in git
%global git_tag 01f4d4dcaf49f62a70bc8272852638adb1dbc206

Name:      %{?scl_prefix}eclipse-emf
Version:   2.11.0
Release:   4.2.bs2%{?dist}
Summary:   Eclipse Modeling Framework (EMF) Eclipse plug-in

License:   EPL
URL:       http://www.eclipse.org/modeling/emf/
Source0:   http://git.eclipse.org/c/emf/org.eclipse.emf.git/snapshot/org.eclipse.emf-%{git_tag}.tar.xz

# look inside correct directory for platform docs
Patch0:    eclipse-emf-platform-docs-location.patch
# Build docs correctly
Patch1:    eclipse-emf-build-docs.patch
Patch2:    eclipse-emf-fix-missing-index.patch


BuildRequires: %{?scl_prefix}eclipse-pde >= 1:4.4.0

%description
The Eclipse Modeling Framework (EMF) allows developers to build tools and
other applications based on a structured data model. From a model
specification described in XMI, EMF provides tools and run-time support to
produce a set of Java classes for the model, along with a set of adapter
classes that enable viewing and command-based editing of the model, and a
basic editor.

# TODO: ODA, GWT and RAP components are not packaged.

%package   core
Epoch:     1
Summary:   Eclipse EMF Core

Requires:  %{?scl_prefix}eclipse-filesystem

%description core
EMF bundles required by eclipse-platform.

%package   runtime
Summary:   Eclipse Modeling Framework (EMF) Eclipse plug-in
Requires:  %{?scl_prefix}eclipse-platform >= 1:4.4.0

# Obsoletes/provides added in F22
Obsoletes: %{name} < %{version}-%{release}
Provides:  %{name} = %{version}-%{release}

BuildArch: noarch

%description runtime
The Eclipse Modeling Framework (EMF) allows developers to build tools and
other applications based on a structured data model. From a model
specification described in XMI, EMF provides tools and run-time support to
produce a set of Java classes for the model, along with a set of adapter
classes that enable viewing and command-based editing of the model, and a
basic editor.

%package   sdk
Summary:   Eclipse EMF SDK
Requires:  %{?scl_prefix}eclipse-pde >= 1:4.4.0
Requires:  %{name}-runtime = %{version}-%{release}

BuildArch: noarch

%description sdk
Documentation and developer resources for the Eclipse Modeling Framework
(EMF) plug-in.

%package   examples
Summary:   Eclipse EMF examples
Requires:  %{name}-sdk = %{version}-%{release}

BuildArch: noarch

%description examples
Install-able versions of the example projects from the SDKs that demonstrate
how to use the Eclipse Modeling Framework (EMF) plug-ins.

%prep
%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
%setup -q -n org.eclipse.emf-%{git_tag}

find . -type f -name "*.jar" -exec rm {} \;
find . -type f -name "*.class" -exec rm {} \;

%patch0
%patch1
%patch2

mv {features,plugins,doc,examples}/* .
rm -rf features plugins doc examples

# Fix spurious exec perms on license
chmod 0644 org.eclipse.emf.license-feature/rootfiles/epl-v10.html
%{?scl:EOF}


%build
%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
# Note: We use forceContextQualifier because the docs plugins use custom build
#       scripts and don't work otherwise.
OPTIONS="-DjavacTarget=1.5 -DjavacSource=1.5 -DforceContextQualifier=$(date +v%Y%m%d-%H00)"

# Work around pdebuild entering/leaving symlink it is unaware of.
ln -s %{_builddir}/org.eclipse.emf-%{git_tag}/org.eclipse.emf.license-feature \
  %{_builddir}/org.eclipse.emf-%{git_tag}/org.eclipse.emf.license

# Build core & runtime features, docs & source features, example features
eclipse-pdebuild -f org.eclipse.emf -a "$OPTIONS"
eclipse-pdebuild -f org.eclipse.emf.sdk -a "$OPTIONS"
eclipse-pdebuild -f org.eclipse.emf.examples -a "$OPTIONS"
%{?scl:EOF}


%install
%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
install -d -m 755 %{buildroot}%{eclipse_dropin}
unzip -q -n -d %{buildroot}%{eclipse_dropin}/emf-runtime  build/rpmBuild/org.eclipse.emf.zip
unzip -q -n -d %{buildroot}%{eclipse_dropin}/emf-sdk      build/rpmBuild/org.eclipse.emf.sdk.zip
unzip -q -n -d %{buildroot}%{eclipse_dropin}/emf-examples build/rpmBuild/org.eclipse.emf.examples.zip

# The main features are a subset of the sdk feature, so delete duplicates from the sdk feature
(cd %{buildroot}%{eclipse_dropin}/emf-sdk/eclipse/features && ls %{buildroot}%{eclipse_dropin}/emf-runtime/eclipse/features | xargs rm -rf)
(cd %{buildroot}%{eclipse_dropin}/emf-sdk/eclipse/plugins  && ls %{buildroot}%{eclipse_dropin}/emf-runtime/eclipse/plugins  | xargs rm -rf)

# Move core features to libdir
install -d -m 755 %{buildroot}%{_libdir}/eclipse/{features,plugins}
mv %{buildroot}%{eclipse_dropin}/emf-runtime/eclipse/features/org.eclipse.emf.common_* %{buildroot}%{_libdir}/eclipse/features
mv %{buildroot}%{eclipse_dropin}/emf-runtime/eclipse/plugins/org.eclipse.emf.common_* %{buildroot}%{_libdir}/eclipse/plugins
mv %{buildroot}%{eclipse_dropin}/emf-runtime/eclipse/features/org.eclipse.emf.ecore_* %{buildroot}%{_libdir}/eclipse/features
mv %{buildroot}%{eclipse_dropin}/emf-runtime/eclipse/plugins/org.eclipse.emf.ecore_* %{buildroot}%{_libdir}/eclipse/plugins
mv %{buildroot}%{eclipse_dropin}/emf-runtime/eclipse/plugins/org.eclipse.emf.ecore.change_* %{buildroot}%{_libdir}/eclipse/plugins
mv %{buildroot}%{eclipse_dropin}/emf-runtime/eclipse/plugins/org.eclipse.emf.ecore.xmi_* %{buildroot}%{_libdir}/eclipse/plugins
%{?scl:EOF}


%files core
%{_libdir}/eclipse/features/*
%{_libdir}/eclipse/plugins/*
%doc org.eclipse.emf.license-feature/rootfiles/*

%files runtime
%{eclipse_dropin}/emf-runtime
%doc org.eclipse.emf.license-feature/rootfiles/*

%files sdk
%{eclipse_dropin}/emf-sdk

%files examples
%{eclipse_dropin}/emf-examples

%changelog
* Wed Jul 29 2015 Mat Booth <mat.booth@redhat.com> - 2.11.0-4.2
- Fix failure to build from source

* Mon Jun 29 2015 Mat Booth <mat.booth@redhat.com> - 2.11.0-4.1
- Import latest from Fedora

* Mon Jun 29 2015 Mat Booth <mat.booth@redhat.com> - 2.11.0-4
- Remove incomplete SCL macros

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.11.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue Jun 02 2015 Mat Booth <mat.booth@redhat.com> - 2.11.0-2
- Revert moving bundles into core package

* Tue Jun 02 2015 Mat Booth <mat.booth@redhat.com> - 2.11.0-1
- Update to 2.11.0 release
- Move extra e4 tools deps into core package
- Switch to xz tarball

* Sat May 30 2015 Alexander Kurtakov <akurtako@redhat.com> 1:2.10.2-2
- Move emf.edit to core as it's required by e4 now.

* Wed Mar 04 2015 Mat Booth <mat.booth@redhat.com> - 2.10.2-1
- Update to Luna SR2 release

* Thu Nov 20 2014 Mat Booth <mat.booth@redhat.com> - 2.10.1-3
- Qualifier must be same on all arches in archful builds

* Wed Nov 19 2014 Mat Booth <mat.booth@redhat.com> - 2.10.1-2
- Make core package archful so it can be installed into libdir
  where eclipse-platform expects it to be
- Move eclipse-emf -> eclipse-emf-runtime, this is because we can have
  noarch sub-packages of an archful package, but cannot have archful
  sub-packages of a noarch package
- Fix some minor rpmlint errors

* Wed Oct 01 2014 Mat Booth <mat.booth@redhat.com> - 2.10.1-1
- Update to Luna SR1 release
- Drop ancient obsoletes on emf-sdo package

* Wed Jun 25 2014 Mat Booth <mat.booth@redhat.com> - 2.10.0-1
- Update to latest upstream release
- Fix obsoletes on emf-core package, rhbz #1095431
- Move edit plugin from core to main package

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.9.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Thu Apr 17 2014 Mat Booth <mat.booth@redhat.com> - 2.9.2-2
- Drop XSD packages, these are now packaged separately
- Drop ancient obsolete of emf-standalone.

* Wed Mar 12 2014 Mat Booth <fedora@matbooth.co.uk> - 2.9.2-1
- Update to latest upstream, Kepler SR2
- Drop requires on java, rhbz #1068039
- Remove unused patch
- Update project URL

* Mon Sep 30 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.9.1-1
- Update to latest upstream.  

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.9.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Fri Jun 21 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.9.0-1
- Update to Kepler release.

* Fri Jun 21 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.9.0-0.2.git352e28
- 974108: Remove versions and timestamps from EMF filenames.

* Wed May 1 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.9.0-0.1.git352e28
- Update to latest upstream.

* Thu Mar 21 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-20
- Initial SCLization.

* Mon Jan 28 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-7
- Really fix RHBZ#894154.

* Thu Jan 17 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-6
- Move emf.edit back to eclipse-emf-core and symlink it.

* Thu Jan 17 2013 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-5
- Fix for RHBZ#894154

* Mon Dec 17 2012 Alexander Kurtakov <akurtako@redhat.com> 1:2.8.1-4
- Remove unneeded things.

* Mon Oct 8 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-3
- Avoid generating automatic OSGi dependencies (yet another attempt).

* Mon Oct 8 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-2
- Avoid generating automatic OSGi dependencies. (fix)

* Mon Oct 1 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.1-1
- Update to upstream 2.8.1 release

* Wed Sep 12 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.0-17
- Avoid generating automatic OSGi dependencies.

* Wed Aug 15 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.0-16
- Removed obsolete.

* Tue Aug 14 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.0-15
- Moved Obs emf-core to emf-core package.
- Removed dropins symlinks.

* Tue Aug 14 2012 Krzysztof Daniel <kdaniel@redhat.com> 1:2.8.0-14
- Added Epoch to eclipse-emf-core.
- Updated eclipse-pde dependency version to 4.2.0.

* Mon Aug 13 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-13
- Move emf.edit to eclipse-emf-core.

* Fri Aug 10 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-12
- Lower eclipse-platform version requirement (CBI Eclipse is not in yet).

* Fri Aug 10 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-11
- Get rid off conflicts clause.

* Thu Aug 2 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-10
- Moving core back to emf package (for CBI build).

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.8.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Jul 10 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-1
- Update to upstream Juno.

* Mon May 7 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.7.e674bb28ad412fc9bc786f2f9b3c157eb2cbdae0
- Update to M7.

* Mon Apr 16 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.6.postM6
- Bugs 812870, 812872 - fix building index for documentation.

* Tue Apr 10 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.5.postM6
- Remove %%clean section.
- Remove duplicated plugins.

* Mon Apr 2 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.4.postM6
- Use %%{bindir}/eclipse-pdebuild.

* Thu Mar 29 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.3.postM6
- Back noarch.
- Use the eclipse-emf-core from main eclipse-emf.

* Thu Mar 29 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.2.postM6
- Removed the noarch tag.

* Thu Mar 29 2012 Krzysztof Daniel <kdaniel@redhat.com> 2.8.0-0.1.postM6
- Update to latest upstream version.
- Package eclipse-emf-core created for the need of Eclipse 4.2. 
- Removed usage of Eclipse reconciler script.

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.7.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Nov 29 2011 Jeff Johnston <jjohnstn@redhat.com> 2.7.1-1
- Update to 2.7.1.
- Add rhel flags.

* Wed Oct 5 2011 Sami Wagiaalla <swagiaal@redhat.com> 2.7.0-2
- Use the reconciler to install/uninstall plugins during rpm
  post and postun respectively.

* Thu Sep 15 2011 Roland Grunberg <rgrunber@redhat.com> 2.7.0-1
- Update to 2.7.0.
- Re-apply necessary patches, content-handler error fixed upstream.
- licenses now exist in org.eclipse.{emf,xsd}.license-feature only.

* Wed Sep 14 2011 Roland Grunberg <rgrunber@redhat.com> 2.6.1-2
- Fix RHBZ #716165 using old patches.
- Fix ContentHandler casting issue.

* Fri Mar 18 2011 Mat Booth <fedora@matbooth.co.uk> 2.6.1-1
- Update to 2.6.1.

* Tue Feb 08 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.6.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Jul 19 2010 Charley Wang <chwang@redhat.com> - 2.6.0-1
- Update to 2.6.0

* Sat Sep 19 2009 Mat Booth <fedora@matbooth.co.uk> - 2.5.0-4
- Re-enable jar repacking now that RHBZ #461854 has been resolved.

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Jul 02 2009 Mat Booth <fedora@matbooth.co.uk> 2.5.0-2
- SDK requires PDE for example plug-in projects.

* Sun Jun 28 2009 Mat Booth <fedora@matbooth.co.uk> 2.5.0-1
- Update to 2.5.0 final release (Galileo).
- Build the features seperately to allow for a saner %%files section.

* Fri May 22 2009 Alexander Kurtakov <akurtako@redhat.com> 2.5.0-0.2.RC1
- Update to 2.5.0 RC1.
- Use %%global instead of %%define. 

* Sat Apr 18 2009 Mat Booth <fedora@matbooth.co.uk> 2.5.0-0.1.M6
- Update to Milestone 6 release of 2.5.0.
- Require Eclipse 3.5.0.

* Tue Apr 7 2009 Alexander Kurtakov <akurtako@redhat.com> 2.4.2-3
- Fix directory ownership.

* Mon Mar 23 2009 Alexander Kurtakov <akurtako@redhat.com> 2.4.2-2
- Rebuild to not ship p2 context.xml.
- Remove context.xml from %%files section.

* Sat Feb 28 2009 Mat Booth <fedora@matbooth.co.uk> 2.4.2-1
- Update for Ganymede SR2.

* Tue Feb 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Tue Feb 03 2009 Mat Booth <fedora@matbooth.co.uk> 2.4.1-4
- Make context qualifier the same as upstream.

* Sat Jan 10 2009 Mat Booth <fedora@matbooth.co.uk> 2.4.1-3
- Removed AOT bits and change package names to what they used to be.
- Obsolete standalone package.

* Tue Dec 23 2008 Mat Booth <fedora@matbooth.co.uk> 2.4.1-2
- Build example installer plugins using the source from the tarball instead of
  trying to get the examples from source control a second time.

* Fri Dec 12 2008 Mat Booth <fedora@matbooth.co.uk> 2.4.1-1
- Initial release, based on eclipse-gef spec file, but with disabled AOT
  compiled bits because of RHBZ #477707.
