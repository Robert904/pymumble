# -*- coding: utf-8 -*-

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [
  Extension("celt_0_11",
            sources = ["celt_0_11.pyx"],
            extra_objects=["celt-0.11.1/libcelt/.libs/libcelt0.a"])
  ]

setup(
  cmdclass = {"build_ext": build_ext},
  ext_modules = ext_modules
)
