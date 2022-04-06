from conans import ConanFile, CMake, tools
import os
import functools


required_conan_version = ">= 1.43.0"


class OpenDDLParserConan(ConanFile):
    name = "openddl-parser"
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/kimkulling/openddl-parser"
    description = "A simple and fast OpenDDL Parser"
    topics = ("conan", "openddl", "parser")

    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }

    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    @property
    def _is_msvc(self):
        return str(self.settings.compiler) in ["Visual Studio", "msvc"]

    def source(self):
        tools.get(**self.conan_data["sources"][self.version], strip_root=True,
                  destination=self._source_subfolder)

    def configure(self):
        if self.options.shared:
            del self.options.fPIC

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    @functools.lru_cache(1)
    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["DDL_STATIC_LIBRARY"] = not self.options.shared
        cmake.definitions["DDL_BUILD_TESTS"] = False
        cmake.definitions["DDL_BUILD_PARSER_DEMO"] = False
        cmake.configure()
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("LICENSE", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        self.copy("*.dll", dst="bin", src="bin", keep_path=False)
        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "openddlparser")
        self.cpp_info.set_property("cmake_target_name", "openddlparser::openddlparser")
        self.cpp_info.libs = ["openddlparser"]
        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")
        if self._is_msvc and not self.options.shared:
            self.cpp_info.defines.append("OPENDDL_STATIC_LIBARY")

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.names["cmake_find_package"] = "openddlparser"
        self.cpp_info.names["cmake_find_package_multi"] = "openddlparser"
