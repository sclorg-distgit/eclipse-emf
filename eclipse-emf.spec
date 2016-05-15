%{?scl:%scl_package eclipse-emf}
%{!?scl:%global pkg_name %{name}}
%{?java_common_find_provides_and_requires}

%global baserelease 1

# The core sub-package must be archful because it is required to be in
# libdir by the platform, but we have no natives, so suppress debuginfo
%global debug_package %{nil}

%global git_tag R2_11_maintenance

%if 0%{?fedora} >= 24
%global droplets droplets
%else
%global droplets dropins
%endif

Name:      %{?scl_prefix}eclipse-emf
Version:   2.11.2
Release:   1.%{baserelease}%{?dist}
Summary:   Eclipse Modeling Framework (EMF) Eclipse plug-in

License:   EPL
URL:       http://www.eclipse.org/modeling/emf/
Source0:   http://git.eclipse.org/c/emf/org.eclipse.emf.git/snapshot/org.eclipse.emf-%{git_tag}.tar.xz
# This is a template used by tycho for generating parent pom
Source1:   parent-pom.xml

# look inside correct directory for platform docs
Patch0:    eclipse-emf-platform-docs-location.patch
# Include documentation search index, exclude non-existing files
Patch1:    fix-build-properties.patch
# Fix test dependency on missing RAP bundles
Patch2:    remove-rap-dependency.patch

BuildRequires: %{?scl_prefix}tycho >= 0.23.0
BuildRequires: %{?scl_prefix}tycho-extras >= 0.23.0
BuildRequires: %{?scl_prefix}eclipse-filesystem
BuildRequires: %{?scl_prefix}eclipse-pde

%description
The Eclipse Modeling Framework (EMF) allows developers to build tools and
other applications based on a structured data model. From a model
specification described in XMI, EMF provides tools and run-time support to
produce a set of Java classes for the model, along with a set of adapter
classes that enable viewing and command-based editing of the model, and a
basic editor.

%package   core
Epoch:     1
Summary:   Eclipse EMF Core
Requires:  %{?scl_prefix}eclipse-filesystem

%description core
EMF bundles required by eclipse-platform.

%package   runtime
Summary:   Eclipse Modeling Framework (EMF) Eclipse plug-in

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
set -e -x
%setup -q -n org.eclipse.emf-%{git_tag}

find . -type f -name "*.jar" -exec rm {} \;
find . -type f -name "*.class" -exec rm {} \;

%patch0
%patch1
%patch2

# Fix spurious exec perms on license
chmod 0644 features/org.eclipse.emf.license-feature/rootfiles/epl-v10.html

# TODO: ODA, GWT, Xtext and RAP components are not packaged.
find -maxdepth 2 -type d -name "*.xcore*" -exec rm -r {} \;
find -maxdepth 2 -type d -name "*.xtext*" -exec rm -r {} \;
find -maxdepth 2 -type d -name "*.oda*" -exec rm -r {} \;
find -maxdepth 2 -type d -name "*.rap*" -exec rm -r {} \;
find -maxdepth 2 -type d -name "*.gwt*" -exec rm -r {} \;

# Insert pom templates
mkdir pom-templates
cp -p %{SOURCE1} pom-templates/.

# Disable tests due to no eclipse-xsd for
rm -rf tests/

# Generate pom.xml
mv doc/org.eclipse.emf.examples.jet.article2 examples
xmvn -o org.eclipse.tycho:tycho-pomgenerator-plugin:generate-poms -DgroupId=org.eclipse.emf
find features -name pom.xml -exec sed -i -e 's/^  <groupId>\(.*\)</  <groupId>\1.features</' {} \;
find examples -name pom.xml -exec sed -i -e 's/^  <groupId>\(.*\)</  <groupId>\1.examples</' {} \;
find doc -name pom.xml -exec sed -i -e 's/^  <groupId>\(.*\)</  <groupId>\1.doc</' {} \;
%pom_add_plugin "org.eclipse.tycho.extras:tycho-eclipserun-plugin:0.23.0" doc/org.eclipse.emf.doc \
  "<executions><execution><goals><goal>eclipse-run</goal></goals><phase>process-sources</phase></execution></executions><configuration><appArgLine>-consolelog -debug -application org.eclipse.ant.core.antRunner -quiet -buildfile buildDoc.xml</appArgLine><repositories><repository><id>luna</id><layout>p2</layout><url>http://download.eclipse.org/releases/luna</url></repository></repositories><dependencies><dependency><artifactId>org.eclipse.ant.core</artifactId><type>eclipse-plugin</type></dependency><dependency><artifactId>org.apache.ant</artifactId><type>eclipse-plugin</type></dependency><dependency><artifactId>org.eclipse.help.base</artifactId><type>eclipse-plugin</type></dependency></dependencies></configuration>"

# Remove broken refs to source bundles
%pom_xpath_remove "includes[@id='org.eclipse.emf.source']" features/org.eclipse.emf.sdk-feature/feature.xml
%pom_xpath_remove "includes[@id='org.eclipse.emf.doc.source']" features/org.eclipse.emf.sdk-feature/feature.xml
%pom_xpath_remove "includes[@id='org.eclipse.emf.examples.source']" examples/org.eclipse.emf.examples-feature/feature.xml

# Disable modules unneeded for tycho build
%pom_disable_module 'features/org.eclipse.emf.all-feature'
%pom_disable_module 'releng/org.eclipse.emf.build-feature'
%pom_disable_module 'releng/org.eclipse.emf.base.build-feature'

%mvn_package "::pom::" __noinstall
%mvn_package "::jar:{sources,sources-feature}:" sdk
%mvn_package ":org.eclipse.emf.{sdk,example.installer}" sdk
%mvn_package "org.eclipse.emf.doc:" sdk
%mvn_package "org.eclipse.emf.features:org.eclipse.emf.{base,common,ecore}" core
%mvn_package "org.eclipse.emf:org.eclipse.emf.{common,ecore,ecore.change,ecore.xmi}" core
%mvn_package "org.eclipse.emf.tests:" tests
%mvn_package "org.eclipse.emf.examples:" examples
%mvn_package ":" runtime
%{?scl:EOF}


%build
%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
set -e -x
%mvn_build -f -j -- -DforceContextQualifier=$(date -u +v%Y%m%d-1000)
%{?scl:EOF}


%install
%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
set -e -x
%mvn_install

# Move to libdir due to being part of core platform
install -d -m 755 %{buildroot}%{_libdir}/eclipse
mv %{buildroot}%{_datadir}/eclipse/%{droplets}/emf-core/eclipse/{plugins,features} %{buildroot}%{_libdir}/eclipse
rm -r %{buildroot}%{_datadir}/eclipse/%{droplets}/emf-core

# Fixup metadata
sed -i -e 's|%{_datadir}/eclipse/%{droplets}/emf-core/eclipse|%{_libdir}/eclipse|' %{buildroot}%{_datadir}/maven-metadata/eclipse-emf-core.xml
sed -i -e 's|%{_datadir}/eclipse/%{droplets}/emf-core/eclipse/features/|%{_libdir}/eclipse/features/|' \
       -e 's|%{_datadir}/eclipse/%{droplets}/emf-core/eclipse/plugins/|%{_libdir}/eclipse/plugins/|' .mfiles-core
sed -i -e '/%{droplets}/d' .mfiles-core
%{?scl:EOF}


%files core -f .mfiles-core

%files runtime -f .mfiles-runtime

%files sdk -f .mfiles-sdk

%files examples -f .mfiles-examples

%changelog
* Sat Mar 19 2016 Mat Booth <mat.booth@redhat.com> - 2.11.2-1.1
- Import latest from Fedora

* Mon Feb 29 2016 Mat Booth <mat.booth@redhat.com> - 2.11.1-1.2
- Rebuild 2016-02-29

* Sat Feb 27 2016 Mat Booth <mat.booth@redhat.com> - 2.11.2-1
- Update to Mars.2 release

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2.11.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Tue Jan 12 2016 Mat Booth <mat.booth@redhat.com> - 2.11.1-1.1
- Import latest from Fedora
- Remove tests package due to no eclipse-xsd in DTS

* Mon Sep 28 2015 Mat Booth <mat.booth@redhat.com> - 2.11.1-1
- Update to Mars.1 release
- Build with maven/tycho
- Add tests package

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
