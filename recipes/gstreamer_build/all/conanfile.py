from conans import ConanFile, tools, Meson, VisualStudioBuildEnvironment
import glob
import os
import shutil

from conans.client.tools import pkg_config

required_conan_version = ">=1.29"


class GStreamerBuildConan(ConanFile):
    name = "gst-build"
    description = "GStreamer is a development framework for creating applications like media players, video editors, streaming media broadcasters and so on"
    topics = ("conan", "gstreamer", "multimedia", "video",
              "audio", "broadcasting", "framework", "media")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://gstreamer.freedesktop.org/"
    license = "GPL-2.0-only"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False],
               # subproject options -- forward to meson
               "python": ['enabled', 'auto', 'disabled'],
               "libav": ['enabled', 'auto', 'disabled'],
               "libnice": ['enabled', 'auto', 'disabled'],
               "base": ['enabled', 'auto', 'disabled'],
               "good": ['enabled', 'auto', 'disabled'],
               "ugly": ['enabled', 'auto', 'disabled'],
               "bad": ['enabled', 'auto', 'disabled'],
               "devtools": ['enabled', 'auto', 'disabled'],
               "ges": ['enabled', 'auto', 'disabled'],
               "rtsp_server": ['enabled', 'auto', 'disabled'],
               "omx": ['enabled', 'auto', 'disabled'],
               "vaapi": ['enabled', 'auto', 'disabled'],
               "sharp": ['enabled', 'auto', 'disabled'],
               "rs": ['enabled', 'auto', 'disabled'],
               "gst_examples": ['enabled', 'auto', 'disabled'],
               "tls": ['enabled', 'auto', 'disabled'],
               "qt5": ['enabled', 'auto', 'disabled'],
               # other options -- forward to meson
               "custom_subprojects": "ANY",
               "gst_full_libraries": "ANY",
               "gst_full_version_script": "ANY",
               "gst_full_plugins": "ANY",
               "gst_full_elements": "ANY",
               "gst_full_typefind_functions": "ANY",
               "gst_full_device_providers": "ANY",
               "gst_full_dynamic_types": "ANY",
               # common options -- forward to meson
               "tests": ['enabled', 'auto', 'disabled'],
               "examples": ['enabled', 'auto', 'disabled'],
               "introspection": ['enabled', 'auto', 'disabled'],
               "nls": ['enabled', 'auto', 'disabled'],
               "orc": ['enabled', 'auto', 'disabled'],
               "doc": ['enabled', 'auto', 'disabled'],
               "gtk_doc": ['enabled', 'auto', 'disabled'],
               # this recipe build options
               "keep_gstreamer_package_names": [True, False]
               }

    # https://gitlab.freedesktop.org/gstreamer/gst-build/-/blob/master/meson_options.txt
    default_options = {"shared": False, "fPIC": True,
                       "python": "auto",
                       "libav": "auto",
                       "libnice": "auto",
                       "base": "enabled",
                       "good": "enabled",
                       "ugly": "auto",
                       "bad": "auto",
                       "devtools": "auto",
                       "ges": "auto",
                       "rtsp_server": "auto",
                       "omx": "disabled",
                       "vaapi": "disabled",
                       "sharp": "disabled",
                       "rs": "disabled",
                       "gst_examples": "auto",
                       "tls": "auto",
                       "qt5": "auto",
                       "custom_subprojects": "",
                       "gst_full_libraries": "",
                       "gst_full_version_script": "gstreamer-full-default.map",
                       "gst_full_plugins": "*",
                       "gst_full_elements": "",
                       "gst_full_typefind_functions": "",
                       "gst_full_device_providers": "",
                       "gst_full_dynamic_types": "",
                       "tests": "auto",
                       "examples": "auto",
                       "introspection": "auto",
                       "nls": "auto",
                       "orc": "auto",
                       "doc": "auto",
                       "gtk_doc": "disabled",
                       "keep_gstreamer_package_names": False,
                       }
    generators = "pkg_config"
    _meson = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def requirements(self):
        self.requires("glib/2.68.0")  # required by gdk-pixbuf/2.42.4 for gtk3

    @property
    def _is_msvc(self):
        return self.settings.compiler == "Visual Studio"

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def build_requirements(self):
        self.build_requires("meson/0.56.2")
        self.build_requires("pkgconf/1.7.3")
        if self.settings.os == 'Windows':
            self.build_requires("winflexbison/2.5.22")
        else:
            self.build_requires("bison/3.7.1")
            self.build_requires("flex/2.6.4")
            self.build_requires("gtk/4.1.2")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("%s-%s" % (self.name, self.version), self._source_subfolder)

    def _get_pkg_config_paths(self):

        pkg_config_paths = [self.build_folder]
        if self.settings.os == 'Linux':
            pkg_config_paths = [
                '/usr/lib/x86_64-linux-gnu/pkgconfig', '/usr/share/pkgconfig']

        subprojects_dir = os.sep.join(
            [self.build_folder, 'build_subfolder', 'subprojects'])

        # always add base gstreamer path
        pkg_config_paths.append(os.sep.join(
            [subprojects_dir, 'gstreamer', 'pkgconfig']))

        # conditionally add more paths if the options are turned on
        if self.options.base:
            pkg_config_paths.append(os.sep.join(
                [subprojects_dir, 'gst-plugins-base', 'pkgconfig']))
        if self.options.bad:
            pkg_config_paths.append(os.sep.join(
                [subprojects_dir, 'gst-plugins-bad', 'pkgconfig']))
        if self.options.rtsp_server:
            pkg_config_paths.append(os.sep.join(
                [subprojects_dir, 'gst-rtsp-server', 'pkgconfig']))
        if self.options.devtools:
            pkg_config_paths.append(os.sep.join(
                [subprojects_dir, 'gst-devtools', 'pkgconfig']))
        if self.options.orc:
            pkg_config_paths.append(os.sep.join([subprojects_dir, 'orc']))

        # always add gst-editing-services pkgconfig path (not sure if the trigger)
        pkg_config_paths.append(os.sep.join(
            [subprojects_dir, 'gst-editing-services', 'pkgconfig']))

        return pkg_config_paths

    def _configure_meson(self, pkg_config_paths):
        if self._meson:
            return self._meson
        meson = Meson(self)
        if self._is_msvc:
            if tools.Version(self.settings.compiler.version) < "14":
                meson.options["c_args"] = " -Dsnprintf=_snprintf"
                meson.options["cpp_args"] = " -Dsnprintf=_snprintf"
        if self.settings.get_safe("compiler.runtime"):
            meson.options["b_vscrt"] = str(
                self.settings.compiler.runtime).lower()

        meson.options['python'] = self.options.python
        meson.options['libav'] = self.options.libav
        meson.options['libnice'] = self.options.libnice
        meson.options['base'] = self.options.base
        meson.options['good'] = self.options.good
        meson.options['ugly'] = self.options.ugly
        meson.options['bad'] = self.options.bad
        meson.options['devtools'] = self.options.devtools
        meson.options['ges'] = self.options.ges
        meson.options['rtsp_server'] = self.options.rtsp_server
        meson.options['omx'] = self.options.omx
        meson.options['vaapi'] = self.options.vaapi
        meson.options['sharp'] = self.options.sharp
        meson.options['rs'] = self.options.rs
        meson.options['gst-examples'] = self.options.gst_examples
        meson.options['tls'] = self.options.tls
        meson.options['qt5'] = self.options.qt5
        meson.options['custom_subprojects'] = self.options.custom_subprojects
        meson.options['gst-full-libraries'] = self.options.gst_full_libraries
        meson.options['gst-full-version-script'] = self.options.gst_full_version_script
        meson.options['gst-full-plugins'] = self.options.gst_full_plugins
        meson.options['gst-full-elements'] = self.options.gst_full_elements
        meson.options['gst-full-typefind-functions'] = self.options.gst_full_typefind_functions
        meson.options['gst-full-device-providers'] = self.options.gst_full_device_providers
        meson.options['gst-full-dynamic-types'] = self.options.gst_full_dynamic_types
        meson.options['tests'] = self.options.tests
        meson.options['examples'] = self.options.examples
        meson.options['introspection'] = self.options.introspection
        meson.options['nls'] = self.options.nls
        meson.options['orc'] = self.options.orc
        meson.options['doc'] = self.options.doc
        meson.options['gtk_doc'] = self.options.gtk_doc

        meson.configure(pkg_config_paths=pkg_config_paths,
                        build_folder=self._build_subfolder,
                        source_folder=self._source_subfolder,
                        args=['--wrap-mode=nofallback'])
        self._meson = meson
        return self._meson

    def build(self):

        pkg_config_paths = self._get_pkg_config_paths()

        env_vars = VisualStudioBuildEnvironment(self).vars if self._is_msvc else {
            'PKG_CONFIG_PATH': ':'.join(pkg_config_paths)}

        with tools.environment_append(env_vars):
            self.output.info('pkg_config_paths:' + str(pkg_config_paths))
            meson = self._configure_meson(pkg_config_paths)
            meson.build()

    def _fix_library_names(self, path):
        # regression in 1.16
        if self.settings.compiler == "Visual Studio":
            with tools.chdir(path):
                for filename_old in glob.glob("*.a"):
                    filename_new = filename_old[3:-2] + ".lib"
                    self.output.info("rename %s into %s" %
                                     (filename_old, filename_new))
                    shutil.move(filename_old, filename_new)

    def package(self):
        self.copy(pattern="COPYING", dst="licenses",
                  src=self._source_subfolder)
        pkg_config_paths = self._get_pkg_config_paths()

        env_vars = VisualStudioBuildEnvironment(self).vars if self._is_msvc else {
            'PKG_CONFIG_PATH': ':'.join(pkg_config_paths)}

        with tools.environment_append(env_vars):
            meson = self._configure_meson(pkg_config_paths)
            meson.install()

        self._fix_library_names(os.path.join(self.package_folder, "lib"))
        self._fix_library_names(os.path.join(
            self.package_folder, "lib", "gstreamer-1.0"))

        if not self.options.keep_gstreamer_package_names:
            self.output.info('Removing gstreamer-generated pkg-config files')
            tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
            tools.rmdir(os.path.join(self.package_folder,
                                     "lib", "gstreamer-1.0", "pkgconfig"))
        
        tools.rmdir(os.path.join(self.package_folder, "share"))
        tools.remove_files_by_mask(self.package_folder, "*.pdb")

    def package_info(self):
        gst_plugin_path = os.path.join(
            self.package_folder, "lib", "gstreamer-1.0")

        self.cpp_info.components["gstreamer-1.0"].names["pkg_config"] = "gstreamer-1.0"
        self.cpp_info.components["gstreamer-1.0"].requires = [
            "glib::glib-2.0", "glib::gobject-2.0"]
        if not self.options.shared:
            self.cpp_info.components["gstreamer-1.0"].requires.append(
                "glib::gmodule-no-export-2.0")
            self.cpp_info.components["gstreamer-1.0"].defines.append(
                "GST_STATIC_COMPILATION")
        self.cpp_info.components["gstreamer-1.0"].libs = ["gstreamer-1.0"]
        self.cpp_info.components["gstreamer-1.0"].includedirs = [
            os.path.join("include", "gstreamer-1.0")]

        self.cpp_info.components["gstreamer-base-1.0"].names["pkg_config"] = "gstreamer-base-1.0"
        self.cpp_info.components["gstreamer-base-1.0"].requires = ["gstreamer-1.0"]
        self.cpp_info.components["gstreamer-base-1.0"].libs = ["gstbase-1.0"]
        self.cpp_info.components["gstreamer-base-1.0"].includedirs = [
            os.path.join("include", "gstreamer-1.0")]

        self.cpp_info.components["gstreamer-controller-1.0"].names["pkg_config"] = "gstreamer-controller-1.0"
        self.cpp_info.components["gstreamer-controller-1.0"].requires = ["gstreamer-1.0"]
        self.cpp_info.components["gstreamer-controller-1.0"].libs = [
            "gstcontroller-1.0"]
        self.cpp_info.components["gstreamer-controller-1.0"].includedirs = [
            os.path.join("include", "gstreamer-1.0")]

        self.cpp_info.components["gstreamer-net-1.0"].names["pkg_config"] = "gstreamer-net-1.0"
        self.cpp_info.components["gstreamer-net-1.0"].requires = [
            "gstreamer-1.0", "glib::gio-2.0"]
        self.cpp_info.components["gstreamer-net-1.0"].libs = ["gstnet-1.0"]
        self.cpp_info.components["gstreamer-net-1.0"].includedirs = [
            os.path.join("include", "gstreamer-1.0")]

        self.cpp_info.components["gstreamer-check-1.0"].names["pkg_config"] = "gstreamer-check-1.0"
        self.cpp_info.components["gstreamer-check-1.0"].requires = ["gstreamer-1.0"]
        self.cpp_info.components["gstreamer-check-1.0"].libs = ["gstcheck-1.0"]
        self.cpp_info.components["gstreamer-check-1.0"].includedirs = [
            os.path.join("include", "gstreamer-1.0")]

        # gstcoreelements and gstcoretracers are plugins which should be loaded dynamicaly, and not linked to directly
        if not self.options.shared:
            self.cpp_info.components["gstcoreelements"].names["pkg_config"] = "gstcoreelements"
            self.cpp_info.components["gstcoreelements"].requires = [
                "glib::gobject-2.0", "glib::glib-2.0", "gstreamer-1.0", "gstreamer-base-1.0"]
            self.cpp_info.components["gstcoreelements"].libs = [
                "gstcoreelements"]
            self.cpp_info.components["gstcoreelements"].includedirs = [
                os.path.join("include", "gstreamer-1.0")]
            self.cpp_info.components["gstcoreelements"].libdirs = [
                gst_plugin_path]

            self.cpp_info.components["gstcoretracers"].names["pkg_config"] = "gstcoretracers"
            self.cpp_info.components["gstcoretracers"].requires = [
                "gstreamer-1.0"]
            self.cpp_info.components["gstcoretracers"].libs = [
                "gstcoretracers"]
            self.cpp_info.components["gstcoretracers"].includedirs = [
                os.path.join("include", "gstreamer-1.0")]
            self.cpp_info.components["gstcoretracers"].libdirs = [
                gst_plugin_path]

        if self.options.shared:
            self.output.info(
                "Appending GST_PLUGIN_PATH env var : %s" % gst_plugin_path)
            self.env_info.GST_PLUGIN_PATH.append(gst_plugin_path)
        gstreamer_root = self.package_folder
        self.output.info("Creating GSTREAMER_ROOT env var : %s" %
                         gstreamer_root)
        self.env_info.GSTREAMER_ROOT = gstreamer_root
        gst_plugin_scanner = "gst-plugin-scanner.exe" if self.settings.os == "Windows" else "gst-plugin-scanner"
        gst_plugin_scanner = os.path.join(
            self.package_folder, "bin", "gstreamer-1.0", gst_plugin_scanner)
        self.output.info(
            "Creating GST_PLUGIN_SCANNER env var : %s" % gst_plugin_scanner)
        self.env_info.GST_PLUGIN_SCANNER = gst_plugin_scanner
        if self.settings.arch == "x86":
            self.output.info(
                "Creating GSTREAMER_ROOT_X86 env var : %s" % gstreamer_root)
            self.env_info.GSTREAMER_ROOT_X86 = gstreamer_root
        elif self.settings.arch == "x86_64":
            self.output.info(
                "Creating GSTREAMER_ROOT_X86_64 env var : %s" % gstreamer_root)
            self.env_info.GSTREAMER_ROOT_X86_64 = gstreamer_root

        if self.options.keep_gstreamer_package_names:
            pkg_config_path = os.path.join(
                self.package_folder, 'lib', 'pkgconfig'
            )
            self.output.info("Creating PKG_CONFIG_PATH env var : %s" % pkg_config_path)
            self.env_info.PKG_CONFIG_PATH = pkg_config_path
