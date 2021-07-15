#!/usr/bin/env python3
# ==============================================================================
#
#          FILE:  hxltmcli.py
#
#         USAGE:  hxltmcli un-htcds.tm.hxl.csv un-htcds.xliff
#                 cat un-htcds.tm.hxl.csv | hxltmcli > un-htcds.xliff
#
#   DESCRIPTION:  _[eng-Latn] The HXLTM reference implementation in python.
#                             While this can installed with hdp-toolchain:
#                                 pip install hdp-toolchain
#                             The one--big-file hxltmcli.py (along with the
#                             cor.hxltm.yml) can be customized as single
#                             python script. But on this case, you will need
#                             to install at least the hard dependencies
#                             of hxltmcli:
#
#                             pip install libhxl langcodes pyyaml python-liquid
#
#                 [eng-Latn]_
#                 @see http://docs.oasis-open.org/xliff/xliff-core/v2.1
#                      /os/xliff-core-v2.1-os.html
#                 @see https://www.gala-global.org/lisa-oscar-standards
#                 @see https://github.com/HXL-CPLP/forum/issues/58
#                 @see https://github.com/HXL-CPLP/Auxilium-Humanitarium-API
#                      /issues/16
#
#       OPTIONS:  ---
#
#  REQUIREMENTS:  - python3
#                     - libhxl (@see https://pypi.org/project/libhxl/)
#                       - pip3 install libhxl
#                     - langcodes (@see https://github.com/rspeer/langcodes)
#                       - pip3 install langcodes
#                     - pyyaml (@see https://github.com/yaml/pyyaml)
#                       - pip3 install pyyaml
#                     - langcodes (@see https://github.com/jg-rp/liquid)
#                       - pip3 install python-liquid
#          BUGS:  ---
#         NOTES:  ---
#        AUTHOR:  Emerson Rocha <rocha[at]ieee.org>
#       COMPANY:  EticaAI
#       LICENSE:  Public Domain dedication
#                 SPDX-License-Identifier: Unlicense
#       VERSION:  v0.8.2
#       CREATED:  2021-06-27 19:50 UTC v0.5, de github.com/EticaAI
#                     /HXL-Data-Science-file-formats/blob/main/bin/hxl2example
#      REVISION:  2021-06-27 21:16 UTC v0.6 de hxl2tab
#      REVISION:  2021-06-27 23:53 UTC v0.7 --archivum-extensionem=.csv
#                 2021-06-29 22:29 UTC v0.8 MVP of --archivum-extensionem=.tmx
#                                    Translation Memory eXchange format (TMX).
#                 2021-06-29 23:16 UTC v0.8.1 hxltm2xliff renamed to hxltmcli;
#                      Moved from github.com/HXL-CPLP/Auxilium-Humanitarium-API
#                       to github.com/EticaAI/HXL-Data-Science-file-formats
#                 2021-07-04 04:35 UTC v0.8.2 Configurations on cor.hxltm.yml
# ==============================================================================

# Tests
# Exemplos: https://github.com/oasis-tcs/xliff-xliff-22/blob/master/xliff-21
#          /test-suite/core/valid/allExtensions.xlf
# ./_systema/programma/hxltmcli.py --help
# ./_systema/programma/hxltmcli.py _hxltm/schemam-un-htcds.tm.hxl.csv
# ./_systema/programma/hxltmcli.py _hxltm/schemam-un-htcds-5items.tm.hxl.csv
# ./_systema/programma/hxltmcli.py _hxltm/schemam-un-htcds.tm.hxl.csv \
#    --fontem-linguam=eng-Latn
# ./_systema/programma/hxltmcli.py _hxltm/schemam-un-htcds-5items.tm.hxl.csv \
#    --fontem-linguam=eng-Latn --archivum-extensionem=.tmx
# ./_systema/programma/hxltmcli.py _hxltm/schemam-un-htcds-5items.tm.hxl.csv \
#    _hxltm/schemam-un-htcds-5items.tmx --fontem-linguam=eng-Latn \
#    --archivum-extensionem=.tmx
# python3 -m doctest ./_systema/programma/hxltmcli.py
# python3 -m doctest bin/hxltmcli
# python3 -m doctest hxlm/core/bin/hxltmcli.py

# from re import S
import sys
import os
import logging
import argparse
# import textwrap # used for make_args epilog
from pathlib import Path
from abc import ABC, abstractmethod

import csv
import tempfile

from functools import reduce
from typing import (
    Any,
    Dict,
    List,
    Type,
    Union,
)

from dataclasses import dataclass, InitVar

import json
import yaml

# @see https://github.com/HXLStandard/libhxl-python
#    pip3 install libhxl --upgrade
# Do not import hxl, to avoid circular imports
import hxl.converters
import hxl.filters
import hxl.io
import hxl.datatypes

# @see https://github.com/rspeer/langcodes
# pip3 install langcodes
import langcodes

# @see https://github.com/jg-rp/liquid
# pip3 install -U python-liquid
# from liquid import Template as LiquidTemplate
# TODO: implement a JSON filter
#       @see https://github.com/jg-rp/liquid-extra/blob/main/liquid_extra
#            /filters/additional.py

# template = LiquidTemplate("Hello, {{ you }}!")
# print(template.render(you="World"))  # "Hello, World!"

__VERSION__ = "v0.8.2"

# _[eng-Latn]
# Note: If you are doing a fork and making it public, please customize
# __SYSTEMA_VARIANS__, even if the __VERSION__ keeps the same
# [eng-Latn]_
__SYSTEMA_VARIANS__ = "hxltmcli.py;eticaai;rocha+voluntārium-commūne"
# Trivia:
# - systēma, https://en.wiktionary.org/wiki/systema#Latin
# - variāns, https://en.wiktionary.org/wiki/varians#Latin
# - furcam, https://en.wiktionary.org/wiki/furca#Latin
# - commūne, https://en.wiktionary.org/wiki/communis#Latin
# - voluntārium, https://en.wiktionary.org/wiki/voluntarius#Latin

__DESCRIPTIONEM_BREVE__ = """
_[eng-Latn] hxltmcli {0} is an implementation of HXLTM tagging conventions
on HXL to manage and export tabular data to popular translation memories
and glossaries file formats with non-close standards.
[eng-Latn]_"
""".format(__VERSION__)

# tag::epilogum[]
__EPILOGUM__ = """
Exemplōrum gratiā:

HXLTM (csv) -> Translation Memory eXchange format (TMX):
    hxltmcli fontem.tm.hxl.csv objectivum.tmx --objectivum-TMX

HXLTM (xlsx; sheet 7) -> Translation Memory eXchange format (TMX):
    hxltmcli fontem.xlsx objectivum.tmx --sheet 7 --objectivum-TMX

HXLTM (xlsx; sheet 7, Situs interretialis) -> HXLTM (csv):
    hxltmcli https://example.org/fontem.xlsx --sheet 7 fontem.tm.hxl.csv

HXLTM (Google Docs) -> HXLTM (csv):
    hxltmcli https://docs.google.com/spreadsheets/(...) fontem.tm.hxl.csv

HXLTM (Google Docs) -> Translation Memory eXchange format (TMX):
    hxltmcli https://docs.google.com/spreadsheets/(...) objectivum.tmx \
--objectivum-TMX
"""
# end::epilogum[]

# systēma
# In Python2, sys.stdin is a byte stream; in Python3, it's a text stream
STDIN = sys.stdin.buffer

_HOME = str(Path.home())

# TODO: clean up redundancy from hxlm/core/schema/urn/util.py
HXLM_CONFIG_BASE = os.getenv(
    'HXLM_CONFIG_BASE', _HOME + '/.config/hxlm')
# ~/.config/hxlm/cor.hxltm.yml
# This can be customized with enviroment variable HXLM_CONFIG_BASE

# Since hpd-toolchain is not a hard requeriment, we first try to load
# hdp-toolchain lib, but if hxltmcli is a standalone script with
# only libhxl, yaml, etc installed, we tolerate it
try:
    from hxlm.core.constant import (
        HXLM_ROOT,
        HDATUM_EXEMPLUM
    )
    HXLTM_SCRIPT_DIR = HXLM_ROOT + '/core/bin'
    HXLTM_TESTUM_BASIM_DEFALLO = str(HDATUM_EXEMPLUM).replace('file://', '')
except ImportError:
    HXLTM_SCRIPT_DIR = str(Path(__file__).parent.resolve())
    HXLTM_TESTUM_BASIM_DEFALLO = str(Path(
        HXLTM_SCRIPT_DIR + '/../../../testum/hxltm').resolve())

HXLTM_RUNNING_DIR = str(Path().resolve())


class HXLTMCLI:  # pylint: disable=too-many-instance-attributes
    """
    _[eng-Latn] hxltmcli is an working draft of a tool to
                convert prototype of translation memory stored with HXL to
                XLIFF v2.1
    [eng-Latn]_
    """

    def __init__(self):
        """
        _[eng-Latn] Constructs all the necessary attributes for the
                    HXLTMCLI object.
        [eng-Latn]_
        """
        self.hxlhelper = None
        self.args = None
        self.conf = {}  # Crudum, raw file
        self.ontologia = None  # HXLTMOntologia object

        # @deprecated Use HXLTMArgumentum
        # self.objectivum_typum = None

        self.argumentum: Type['HXLTMArgumentum'] = None

        # TODO: migrade from HXLTMcli to HXLTMASA the
        # fontem_linguam, objectivum_linguam, alternativum_linguam, linguam

        # # @deprecated Use HXLTMArgumentum
        # self.fontem_linguam: HXLTMLinguam = None
        # # @deprecated Use HXLTMArgumentum
        # self.objectivum_linguam: HXLTMLinguam = None
        # # @deprecated Use HXLTMArgumentum agendum_linguam
        # self.alternativum_linguam: List[HXLTMLinguam] = []
        # # @deprecated Use HXLTMArgumentum
        # self.agendum_linguam: List[HXLTMLinguam] = []

        # TODO: replace self.datum by HXLTMASA
        self.datum: HXLTMDatum = None
        self.hxltm_asa: Type['HXLTMASA'] = None
        # self.meta_archivum_fontem = {}
        self.meta_archivum_fontem = {}
        self.errors = []

        # Posix exit codes
        self.EXIT_OK = 0
        self.EXIT_ERROR = 1
        self.EXIT_SYNTAX = 2

        self.original_outfile = None
        self.original_outfile_is_stdout = True

    def _objectivum_typum_from_outfile(self, outfile):
        """Uses cor.hxltm.yml fontem_archivum_extensionem to detect output
        format without user need to explicitly inform the option.

        This is not used if the result is stdout

        Args:
            outfile ([str]): Path string of output file

        Returns:
            [str]: A valid cor.hxltm.yml formatum
        """
        outfile_lower = outfile.lower()

        if self.conf and self.conf['fontem_archivum_extensionem']:
            for key in self.conf['fontem_archivum_extensionem']:
                if outfile_lower.endswith(key):
                    return self.conf['fontem_archivum_extensionem'][key]

        return 'INCOGNITUM'

    def _initiale(self, args):
        """Trivia: initiāle, https://en.wiktionary.org/wiki/initialis#Latin
        """
        # if args.expertum_metadatum_est:
        #     self.expertum_metadatum_est = args.expertum_metadatum_est

        # TODO: migrate all this to HXLTMASA._initiale

        if args:
            self.argumentum = HXLTMArgumentum().de_argparse(args)
        else:
            self.argumentum = HXLTMArgumentum()

        self.conf = HXLTMUtil.load_hxltm_options(
            args.archivum_configurationem,
            args.venandum_insectum
        )

        self.ontologia = HXLTMOntologia(self.conf)

        # if args.fontem_linguam:
        #     self.fontem_linguam = HXLTMLinguam(args.fontem_linguam)
        #     if is_debug:
        #         print('fontem_linguam', self.fontem_linguam.v())

        # if args.objectivum_linguam:
        #     self.objectivum_linguam = HXLTMLinguam(args.objectivum_linguam)
        #     if is_debug:
        #         print('objectivum_linguam', self.objectivum_linguam.v())

        # if args.alternativum_linguam and len(args.alternativum_linguam) > 0:
        #     unicum = set(args.alternativum_linguam)
        #     for rem in unicum:
        #         rem_obj = HXLTMLinguam(rem)
        #         if is_debug:
        #             print('alternativum_linguam', rem_obj.v())
        #         self.alternativum_linguam.append(rem_obj)

        # if args.agendum_linguam and len(args.agendum_linguam) > 0:
        #     unicum = set(args.agendum_linguam)
        #     for rem in unicum:
        #         rem_obj = HXLTMLinguam(rem)
        #         if is_debug:
        #             print('agendum_linguam', rem_obj.v())
        #         self.agendum_linguam.append(rem_obj)

        # if is_debug:
        #     print('fontem_linguam', self.fontem_linguam.v())
        #     print('objectivum_linguam', self.objectivum_linguam.v())
        #     print('alternativum_linguam')
        #     if len(self.alternativum_linguam):
        #         for rem in

    def _initiale_hxltm_asa(self, archivum: str, argumentum: Dict) -> bool:
        """Pre-populate metadata about source file

        Requires already HXLated file saved on disk.

        Trivia:
        - initiāle, https://en.wiktionary.org/wiki/initialis#Latin
        - HXLTM, https://hdp.etica.ai/hxltm
        - HXLTM ASA, https://hdp.etica.ai/hxltm/archivum/#HXLTM-ASA

        Args:
            archivum (str): Archīvum trivia
            argumentum (Dict):
                _[lat-Latn]
                Python argumentum,
                https://docs.python.org/3/library/argparse.html
                [lat-Latn]_
        Returns:
            bool: If okay.
        """

        # with open(archivum, 'r') as arch:
        #     hxltm_crudum = arch.read().splitlines()

        self.hxltm_asa = HXLTMASA(
            archivum,
            ontologia=self.ontologia,
            argumentum=argumentum,
            # verbosum=argumentum.hxltm_asa_verbosum
        )

    def make_args_hxltmcli(self):
        """make_args_hxltmcli
        """

        self.hxlhelper = HXLUtils()
        parser = self.hxlhelper.make_args(
            #     description=("""
            # _[eng-Latn] hxltmcli is an working draft of a tool to
            #             convert prototype of translation memory stored with
            #             HXL to XLIFF v2.1
            # [eng-Latn]_
            # """)
            description=__DESCRIPTIONEM_BREVE__,
            epilog=__EPILOGUM__
        )

        # TODO: implement example using index number (not language) as
        #       for very simple cases (mostly for who is learning
        #       or doing very few languages) know the number is easier

        parser.add_argument(
            '--fontem-linguam', '-FL',
            help='(For bilingual operations) Source natural language ' +
            '(use if not auto-detected). ' +
            'Must be like {ISO 639-3}-{ISO 15924}. Example: lat-Latn. ' +
            'Accept a single value.',
            # dest='fontem_linguam',
            metavar='fontem_linguam',
            action='store',
            default='lat-Latn',
            nargs='?'
        )

        parser.add_argument(
            '--objectivum-linguam', '-OL',
            help='(For bilingual operations) Target natural language ' +
            '(use if not auto-detected). ' +
            'Must be like {ISO 639-3}-{ISO 15924}. Example: arb-Arab. ' +
            'Requires: mono or bilingual operation. ' +
            'Accept a single value.',
            metavar='objectivum_linguam',
            action='store',
            default='arb-Arab',
            nargs='?'
        )

        # --alternativum-linguam is a draft. Not 100% implemented
        parser.add_argument(
            '--alternativum-linguam',
            help='(Deprecated, use --agendum-linguam) '
            '(Planned, but not implemented yet) ' +
            'Alternative source languages (up to 5) to be added ' +
            'as metadata (like XLIFF <note>) for operations that ' +
            'only accept one source language. ' +
            'Requires: bilingual operation. ' +
            'Accepts multiple values.',
            metavar='alternativum_linguam',
            action='append',
            nargs='?'
        )

        # --linguam is a draft. Not 100% implemented
        parser.add_argument(
            '--agendum-linguam', '-AL',
            help='(Planned, but not implemented yet) ' +
            'Restrict working languages to a list. Useful for ' +
            'HXLTM to HXLTM or multilingual formats like TMX. ' +
            'Requires: multilingual operation. ' +
            'Accepts multiple values.',
            metavar='agendum_linguam',
            action='append',
            nargs='?'
        )

        # --non-linguam is a draft. Not 100% implemented
        parser.add_argument(
            '--non-linguam', '-non-L',
            help='(Planned, but not implemented yet) ' +
            'Inverse of --non-linguam. Document one or more languages that ' +
            'should be ignored if they exist. ' +
            'Requires: multilingual operation.' +
            'Accept a single value.',
            metavar='non_linguam',
            action='append',
            nargs='?'
        )

        parser.add_argument(
            '--objectivum-HXLTM', '--HXLTM',
            help='Save output as HXLTM (default). Multilingual output format.',
            # metavar='objectivum_typum',
            dest='objectivum_typum',
            action='append_const',
            const='HXLTM'
        )

        parser.add_argument(
            '--objectivum-TMX', '--TMX',
            help='Export to Translation Memory eXchange (TMX) v1.4b. ' +
            ' Multilingual output format',
            # metavar='objectivum_typum',
            dest='objectivum_typum',
            action='append_const',
            const='TMX'
        )

        parser.add_argument(
            '--objectivum-TBX-Basim', '--TBX-Basim',
            help='(Planned, but not implemented yet) ' +
            'Export to Term Base eXchange (TBX). ' +
            ' Multilingual output format',
            # metavar='objectivum_typum',
            dest='objectivum_typum',
            action='append_const',
            const='TBX-Basim'
        )

        parser.add_argument(
            '--objectivum-UTX', '--UTX',
            help='(Planned, but not implemented yet) ' +
            'Export to Universal Terminology eXchange (UTX). ' +
            ' Multilingual output format',
            # metavar='objectivum_typum',
            dest='objectivum_typum',
            action='append_const',
            const='UTX'
        )

        parser.add_argument(
            '--objectivum-XLIFF', '--XLIFF', '--XLIFF2',
            help='Export to XLIFF (XML Localization Interchange File Format)' +
            ' v2.1. ' +
            '(mono or bi-lingual support only as per XLIFF specification)',
            dest='objectivum_typum',
            action='append_const',
            const='XLIFF'
        )

        parser.add_argument(
            '--objectivum-XLIFF-obsoletum', '--XLIFF-obsoletum', '--XLIFF1',
            help='(Not implemented) ' +
            'Export to XLIFF (XML Localization Interchange ' +
            'File Format) v1.2, an obsolete format for lazy developers who ' +
            'don\'t implemented XLIFF 2 (released in 2014) yet.',
            dest='objectivum_typum',
            action='append_const',
            const='XLIFF1'
        )

        parser.add_argument(
            '--objectivum-CSV-3', '--CSV-3',
            help='(Not implemented yet) ' +
            'Export to Bilingual CSV with BCP47 headers (source to target)' +
            ' plus comments on last column ',
            dest='objectivum_typum',
            action='append_const',
            const='CSV-3'
        )

        parser.add_argument(
            '--objectivum-CSV-HXL-XLIFF', '--CSV-HXL-XLIFF',
            help='(experimental) ' +
            'HXLated bilingual CSV (feature compatible with XLIFF)',
            dest='objectivum_typum',
            action='append_const',
            const='CSV-HXL-XLIFF'
        )

        parser.add_argument(
            '--objectivum-JSON-kv', '--JSON-kv',
            help='(Not implemented yet) ' +
            'Export to Bilingual JSON. Keys are ID (if available) or source '
            'natural language. Values are target language. '
            'No comments are exported. Monolingual/Bilingual',
            dest='objectivum_typum',
            action='append_const',
            const='JSON-kv'
        )

        parser.add_argument(
            '--limitem-quantitatem',
            help='(Advanced, large datasets) '
            'Customize the limit of the maximum number of raw rows can '
            'be in a single step. Try increments of 1 million.'
            'Use value -1 to disable limits (even if means exaust '
            'all computer memory require full restart). '
            'Defaults to 1048576 (but to avoid non-expert humans or '
            'automated workflows generate output with missing data '
            'without no one reading the warning messages '
            'if the --limitem-quantitatem was reached AND '
            'no customization was done on --limitem-initiale-lineam '
            'an exception will abort',
            metavar='limitem_quantitatem',
            type=int,
            default=1048576,
            nargs='?'
        )

        parser.add_argument(
            '--limitem-initiale-lineam',
            help='(Advanced, large datasets) ' +
            'When working in batches and the initial row to process is not '
            'the first one (starts from 0) use this option if is '
            'inviable increase to simply --limitem-quantitatem',
            metavar='limitem_initiale_lineam',
            type=int,
            default=-1,
            nargs='?'
        )

        parser.add_argument(
            '--non-securum-limitem', '--ad-astra-per-aspera',
            help='(For situational/temporary usage, as '
            'in "one weekend" NOT six months) '
            'Disable any secure hardware limits and make the program '
            'try harder tolerate (even if means '
            'ignore entire individual rows or columns) but still work with '
            'what was left from the dataset. '
            'This option assume is acceptable not try protect from exhaust '
            'all memory or disk space when working with large datasets '
            'and (even for smaller, but not well know from the '
            'python or YAML ontologia) the current human user evaluated that '
            'the data loss is either false positive or tolerable '
            'until permanent fix.',
            metavar='ad_astra',
            action='store_const',
            const=True,
            default=None
        )

        # sēlēctum

        # @see https://stackoverflow.com/questions/15459997
        #      /passing-integer-lists-to-python/15460288
        parser.add_argument(
            '--selectum-columnam-numerum',
            help='(Advanced) ' +
            'Select only columns from source HXLTM dataset by a list of '
            'index numbers (starts by zero). As example: '
            'to select the first 3 columns'
            'use "0,1,2" and NOT "1,2,3"',
            metavar='columnam_numerum',
            # type=lambda x: x.split(',')
            type=lambda x: map(int, x.split(','))
        )
        # @see https://stackoverflow.com/questions/15459997
        #      /passing-integer-lists-to-python/15460288
        parser.add_argument(
            '--non-selectum-columnam-numerum',
            help='(Advanced) ' +
            'Exclude columns from source HXLTM dataset by a list of '
            'index numbers (starts by zero). As example: '
            'to ignore the first ("Excel A"), and fifth ("Excel: E") column:'
            'use "0,4" and not "1,5"',
            metavar='non_columnam_numerum',
            # type=lambda x: x.split(',')
            type=lambda x: map(int, x.split(','))
        )

        # Trivia: caput, https://en.wiktionary.org/wiki/caput#Latin
        # --rudum-objectivum-caput is a draft. Not 100% implemented
        parser.add_argument(
            '--crudum-objectivum-caput',
            help='(Advanced override for tabular output, like CSV). ' +
            'Explicit define first line of output (separed by ,) ' +
            'Example: "la,ar,Annotationem"',
            metavar='fon_hxlattrs',
            action='store',
            default=None,
            nargs='?'
        )

        # --crudum-fontem-linguam-hxlattrs is a draft. Not 100% implemented
        parser.add_argument(
            '--crudum-fontem-linguam-hxlattrs', '--fon-hxlattrs',
            help='(Advanced override for --fontem-linguam). ' +
            'Explicit HXL Attributes for source language. ' +
            'Example: "+i_la+i_lat+is_latn"',
            metavar='fon_hxlattrs',
            action='store',
            default=None,
            nargs='?'
        )

        # --crudum-fontem-linguam-bcp47 is a draft. Not 100% implemented
        parser.add_argument(
            '--crudum-fontem-linguam-bcp47', '--fon-bcp47',
            help='(Advanced override for --fontem-linguam). ' +
            'Explicit IETF BCP 47 language tag for source language. ' +
            'Example: "la"',
            metavar='fon_bcp47',
            action='store',
            default=None,
            nargs='?'
        )

        # --crudum-objectivum-linguam-hxlattrs is a draft. Not 100% implemented
        parser.add_argument(
            '--crudum-objectivum-linguam-hxlattrs', '--obj-hxlattrs',
            help='(Advanced override for --objectivum-linguam). ' +
            'Explicit HXL Attributes for target language. ' +
            'Example: "+i_ar+i_arb+is_arab"',
            metavar='obj_hxlattrs',
            action='store',
            default=None,
            nargs='?'
        )

        # --crudum-objectivum-linguam-bcp47 is a draft. Not 100% implemented
        parser.add_argument(
            '--crudum-objectivum-linguam-bcp47', '--obj-bcp47',
            help='(Advanced override for --objectivum-linguam). ' +
            'Explicit IETF BCP 47 language tag for target language. ' +
            'Example: "ar"',
            metavar='obj_bcp47',
            action='store',
            default=None,
            nargs='?'
        )

        # https://hdp.etica.ai/ontologia/cor.hxltm.yml
        parser.add_argument(
            '--archivum-configurationem',
            help='Path to custom configuration file (The cor.hxltm.yml)',
            action='store_const',
            const=True,
            default=None
        )
        # TODO: --archivum-configurationem-appendicem
        parser.add_argument(
            '--archivum-configurationem-appendicem',
            help='(Not implemented yet)' +
            'Path to custom configuration file (The cor.hxltm.yml)',
            action='store_const',
            const=True,
            default=None
        )

        parser.add_argument(
            '--silentium',
            help='Silence warnings? Try to not generate any warning. ' +
            'May generate invalid output',
            action='store_const',
            const=True,
            default=False
        )

        # parser.add_argument(
        #     '--expertum-metadatum',
        #     help='(Deprecated, use --expertum-HXLTM-ASA) ' +
        #     '(Expert mode) Return metadata of the operation ' +
        #     'in JSON format instead of generate the output. ' +
        #     'Good for debugging.',
        #     # dest='fontem_linguam',
        #     metavar='expertum_metadatum_est',
        #     action='store_const',
        #     const=True,
        #     default=False
        # )

        parser.add_argument(
            '--expertum-HXLTM-ASA',
            help='(Expert mode) Save an Abstract Syntax Tree  ' +
            'in JSON format to a file path. ' +
            'With --expertum-HXLTM-ASA-verbosum output entire dataset data. ' +
            'File extensions with .yml/.yaml = YAML output. ' +
            'Files extensions with .json/.json5 = JSONs output. ' +
            'Default: JSON output. ' +
            'Good for debugging.',
            # dest='fontem_linguam',
            metavar='hxltm_asa',
            dest='hxltm_asa',
            action='store',
            default=None,
            nargs='?'
        )

        # verbōsum, https://en.wiktionary.org/wiki/verbosus#Latin
        parser.add_argument(
            '--expertum-HXLTM-ASA-verbosum',
            help='(Expert mode) Enable --expertum-HXLTM-ASA verbose mode',
            # dest='fontem_linguam',
            metavar='hxltm_asa_verbosum',
            dest='hxltm_asa_verbosum',
            action='store_const',
            const=True,
            default=False
        )

        # Trivia: experīmentum, https://en.wiktionary.org/wiki/experimentum
        parser.add_argument(
            # '--venandum-insectum-est, --debug',
            '--experimentum-est',
            help='(Internal testing only) Enable undocumented feature',
            metavar="experimentum_est",
            action='store_const',
            const=True,
            default=False
        )

        parser.add_argument(
            # '--venandum-insectum-est, --debug',
            '--venandum-insectum-est', '--debug',
            help='Enable debug? Extra information for program debugging',
            metavar="venandum_insectum",
            dest="venandum_insectum",
            action='store_const',
            const=True,
            default=False
        )

        self.args = parser.parse_args()
        return self.args

    def execute_cli(self, args,
                    stdin=STDIN, stdout=sys.stdout, stderr=sys.stderr):
        """
        The execute_cli is the main entrypoint of HXLTMCLI. When
        called will convert the HXL source to example format.
        """
        # pylint: disable=too-many-branches,too-many-statements

        self._initiale(args)

        # print(HXLTMArgumentum().de_argparse(args))
        # # print(HXLTMArgumentum().fontem_linguam)
        # print(HXLTMArgumentum().est_fontem_linguam('por-Latn'))
        # print(HXLTMArgumentum().est_fontem_linguam('por-Latn').v())
        # print(HXLTMArgumentum({'fontem_linguam': 'por-Latn'}).v())
        # print(HXLTMLinguam('por-Latn').__dict__)

        # print(self.ontologia.hxl_de_aliud_nomen_breve())
        # raise RuntimeError('JUST TESTING, remove me')

        # If the user specified an output file, we will save on
        # self.original_outfile. The args.outfile will be used for temporary
        # output
        if args.outfile:
            self.original_outfile = args.outfile
            self.original_outfile_is_stdout = False
            # self.objectivum_typum = self._objectivum_typum_from_outfile(
            #     self.original_outfile)
            self.argumentum.est_objectivum_formatum(
                self._objectivum_typum_from_outfile(
                    self.original_outfile))

        # if args.objectivum_typum:
        #     if len(args.objectivum_typum) > 1:
        #         raise RuntimeError("More than 1 output format. see --help")
        #     self.objectivum_typum = args.objectivum_typum[0]

        print(self.argumentum.v())

        try:
            temp = tempfile.NamedTemporaryFile()
            temp_csv4xliff = tempfile.NamedTemporaryFile()
            args.outfile = temp.name

            # print(temp_csv4xliff)
            # print(temp_csv4xliff.name)

            with self.hxlhelper.make_source(args, stdin) as source, \
                    self.hxlhelper.make_output(args, stdout) as output:
                # Save the HXL TM locally. It will be used by either in_csv
                # or in_csv + in_xliff
                hxl.io.write_hxl(output.output, source,
                                 show_tags=not args.strip_tags)

            hxlated_input = args.outfile

            # TODO: replace self.datum by HXLTMASA
            # self.datum = HXLTMDatum(hxlated_input, self.ontologia)

            # _[eng-Latn]
            # This step will do raw analysis of the hxlated_input on a
            # temporary on the disk.
            # [eng-Latn]_
            self._initiale_hxltm_asa(hxlated_input, args)

            # print(args)

            if args.hxltm_asa:
                self.in_asa(args.hxltm_asa)

            # if args.expertum_metadatum:
            #     self.in_expertum_metadatum(hxlated_input,
            #                                self.original_outfile,
            #                                self.original_outfile_is_stdout,
            #                                args)
            #     return self.EXIT_OK

            # if archivum_extensionem == '.csv':
            #     # print('CSV!')
            #     self.in_csv(hxlated_input, self.original_outfile,
            #                    self.original_outfile_is_stdout, args)
            if self.argumentum.objectivum_formatum == 'TMX':
                # print('TMX')

                if args.experimentum_est:
                    if self.original_outfile_is_stdout:
                        archivum_objectivum = False
                    else:
                        archivum_objectivum = self.original_outfile
                    self.in_tmx_de_hxltmasa(archivum_objectivum)
                else:
                    self.in_tmx(hxlated_input, self.original_outfile,
                                self.original_outfile_is_stdout, args)

            elif self.argumentum.objectivum_formatum == 'TBX-Basim':
                raise NotImplementedError('TBX-Basim not implemented yet')

            elif self.argumentum.objectivum_formatum == 'UTX':
                raise NotImplementedError('UTX not implemented yet')

            elif self.argumentum.objectivum_formatum == 'XLIFF1':
                raise NotImplementedError('XLIFF1 not implemented')

            elif self.argumentum.objectivum_formatum == 'CSV-3':
                # raise NotImplementedError('CSV-3 not implemented yet')
                self.in_csv3(hxlated_input, self.original_outfile,
                             self.original_outfile_is_stdout, args)

            elif self.argumentum.objectivum_formatum == 'CSV-HXL-XLIFF':
                # raise NotImplementedError('CSV-3 not implemented yet')
                self.in_csv(hxlated_input, self.original_outfile,
                            self.original_outfile_is_stdout, args)

            elif self.argumentum.objectivum_formatum == 'JSON-kv':
                self.in_jsonkv(hxlated_input, self.original_outfile,
                               self.original_outfile_is_stdout, args)
                # raise NotImplementedError('JSON-kv not implemented yet')

            elif self.argumentum.objectivum_formatum == 'XLIFF':
                # print('XLIFF (2)')

                if args.experimentum_est:
                    if self.original_outfile_is_stdout:
                        archivum_objectivum = False
                    else:
                        archivum_objectivum = self.original_outfile
                    self.in_xliff_de_hxltmasa(archivum_objectivum)
                else:
                    self.in_csv(
                        hxlated_input, temp_csv4xliff.name,
                        False, args)
                    self.in_xliff(
                        temp_csv4xliff.name, self.original_outfile,
                        self.original_outfile_is_stdout, args)

            elif self.argumentum.objectivum_formatum == 'HXLTM':
                # print('HXLTM')
                self.in_noop(hxlated_input, self.original_outfile,
                             self.original_outfile_is_stdout)

            elif self.argumentum.objectivum_formatum == 'INCOGNITUM':
                # print('INCOGNITUM')
                raise ValueError(
                    'INCOGNITUM (objetive file output based on extension) ' +
                    'failed do decide what you want. Check --help and ' +
                    'manually select an output format, like --TMX'
                )
            else:
                raise ValueError(
                    'INCOGNITUM (objetive file output based on extension) ' +
                    'failed do decide what you want. Check --help and ' +
                    'manually select an output format, like --TMX'
                )
                # print('default / unknow option result')
                # Here maybe error?
                # self.hxl2tab(hxlated_input, self.original_outfile,
                #              self.original_outfile_is_stdout, args)

                # self.in_csv(hxlated_input, temp_csv4xliff.name,
                #                False, args)
                # print('noop')
                # self.in_noop(hxlated_input, self.original_outfile,
                #              self.original_outfile_is_stdout)

        finally:
            temp.close()
            temp_csv4xliff.close()

        return self.EXIT_OK

    def in_asa(self, hxltm_asa):

        # deprecated: hxltm_asa

        if str(hxltm_asa).endswith(('.yml', '.yaml')):
            resultatum = HXLTMTypum.in_textum_yaml(
                self.hxltm_asa.v(), formosum=True, clavem_sortem=True)
        elif str(hxltm_asa).endswith(('.json', '.json5')):
            resultatum = HXLTMTypum.in_textum_json(
                self.hxltm_asa.v(), formosum=True, clavem_sortem=True)
        else:
            resultatum = HXLTMTypum.in_textum_json(
                self.hxltm_asa.v(), formosum=True, clavem_sortem=True)

        with open(hxltm_asa, 'w') as writer:
            writer.write(resultatum)

    # def in_expertum_metadatum(
    #         self, hxlated_input: str, tab_output: str, is_stdout: bool, args):  # noqa
    #     """in_expertum_metadatum

    #     Trivia:
    #     - in, https://en.wiktionary.org/wiki/in#Latin
    #     - expertum, https://en.wiktionary.org/wiki/expertus#Latin
    #     - meta
    #       - https://en.wiktionary.org/wiki/meta#English
    #         - https://en.wiktionary.org/wiki/metaphysica#Latin
    #     - datum, https://en.wiktionary.org/wiki/datum#Latin

    #     Args:
    #         hxlated_input ([str]): Path to input data on disk
    #         tab_output ([str]): If not stdout, path to output on disk
    #         is_stdout (bool): If is stdout
    #     """
    #     resultatum = {
    #         '_typum': 'HXLTMExpertumMetadatum',
    #         'argumentum': {
    #             'fontem_linguam': self.fontem_linguam.v(),
    #             'objectivum_linguam': self.objectivum_linguam.v(),
    #             'alternativum_linguam': [],
    #             'agendum_linguam': []
    #         },
    #         'archivum_fontem': self.meta_archivum_fontem,
    #         'archivum_fontem_m': {},
    #         'archivum_objectivum': {},
    #     }

    #     resultatum['archivum_fontem_m'] = self.datum.v()

    #     if len(self.alternativum_linguam) > 0:
    #         for rem in self.alternativum_linguam:
    #             resultatum['argumentum']['alternativum_linguam'].append(
    #                 rem.v())

    #     if len(self.agendum_linguam) > 0:
    #         for rem in self.agendum_linguam:
    #             resultatum['argumentum']['agendum_linguam'].append(rem.v())

    #     if not args.venandum_insectum:
    #         venandum_insectum_notitia = {
    #             '__annotatianem': "optio --venandum-insectum-est requirere"
    #         }

    #         resultatum['archivum_fontem'] = venandum_insectum_notitia

    #     json_out = json.dumps(
    #         resultatum, indent=4, sort_keys=False, ensure_ascii=False)

    #     # TODO: maybe implement option to save the metadata on a different
    #     #       file (or allow generate the metadata even if actual result
    #     #       final output was generated)
    #     print(json_out)

    def in_noop(self, hxlated_input, tab_output, is_stdout):
        """
        in_noop only export whatever the initial HXL input was.

        Requires that the input must be a valid HXLated file
        """

        with open(hxlated_input, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)

            if is_stdout:
                # txt_writer = csv.writer(sys.stdout, delimiter='\t')
                txt_writer = csv.writer(sys.stdout)
                # txt_writer.writerow(header_new)
                for line in csv_reader:
                    txt_writer.writerow(line)
            else:

                tab_output_cleanup = open(tab_output, 'w')
                tab_output_cleanup.truncate()
                tab_output_cleanup.close()

                with open(tab_output, 'a') as new_txt:
                    txt_writer = csv.writer(new_txt)
                    for line in csv_reader:
                        txt_writer.writerow(line)

    def in_csv(self, hxlated_input, tab_output, is_stdout, args):
        """
        in_csv pre-process the initial HXL TM on a intermediate format that
        can be used alone or as requisite of the in_xliff exporter
        """

        with open(hxlated_input, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)

            # TODO: fix problem if input data already only have HXL hashtags
            #       but no extra headings (Emerson Rocha, 2021-06-28 01:27 UTC)

            # Hotfix: skip first non-HXL header. Ideally I think the already
            # exported HXlated file should already save without headers.
            next(csv_reader)
            header_original = next(csv_reader)
            header_new = self.in_csv_header(
                header_original,
                fontem_linguam=args.fontem_linguam,
                objectivum_linguam=args.objectivum_linguam,
            )

            if is_stdout:
                # txt_writer = csv.writer(sys.stdout, delimiter='\t')
                txt_writer = csv.writer(sys.stdout)
                txt_writer.writerow(header_new)
                for line in csv_reader:
                    txt_writer.writerow(line)
            else:

                tab_output_cleanup = open(tab_output, 'w')
                tab_output_cleanup.truncate()
                tab_output_cleanup.close()

                with open(tab_output, 'a') as new_txt:
                    # txt_writer = csv.writer(new_txt, delimiter='\t')
                    txt_writer = csv.writer(new_txt)
                    txt_writer.writerow(header_new)
                    for line in csv_reader:
                        txt_writer.writerow(line)

    def hxl2tab(self, hxlated_input, tab_output, is_stdout, args):
        """
        (deprecated hxl2tab)
        """

        with open(hxlated_input, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)

            # Hotfix: skip first non-HXL header. Ideally I think the already
            # exported HXlated file should already save without headers.
            next(csv_reader)
            header_original = next(csv_reader)
            header_new = self.in_csv_header(
                header_original,
                fontem_linguam=args.fontem_linguam,
                objectivum_linguam=args.objectivum_linguam,
            )

            if is_stdout:
                txt_writer = csv.writer(sys.stdout, delimiter='\t')
                txt_writer.writerow(header_new)
                for line in csv_reader:
                    txt_writer.writerow(line)
            else:

                tab_output_cleanup = open(tab_output, 'w')
                tab_output_cleanup.truncate()
                tab_output_cleanup.close()

                with open(tab_output, 'a') as new_txt:
                    txt_writer = csv.writer(new_txt, delimiter='\t')
                    txt_writer.writerow(header_new)
                    for line in csv_reader:
                        txt_writer.writerow(line)

    def in_csv3(self, hxlated_input, file_output, is_stdout, args):
        """Convert HXLTM to output 'CSV-3'

        Args:
            hxlated_input ([str]): Path to HXLated CSV
            tmx_output ([str]): Path to file to write output (if not stdout)
            is_stdout (bool): Flag to tell the output is stdout
            args ([type]): python argparse
        """

        # fon_ling = HXLTMUtil.linguam_2_hxlattrs(args.fontem_linguam)
        fon_bcp47 = HXLTMUtil.bcp47_from_linguam(args.fontem_linguam)
        # obj_ling = HXLTMUtil.linguam_2_hxlattrs(args.objectivum_linguam)
        obj_bcp47 = HXLTMUtil.bcp47_from_linguam(args.objectivum_linguam)

        data_started = False
        fon_index = None
        obj_index = None
        meta_index = None
        datum = []
        with open(hxlated_input, 'r') as csvfile:
            lines = csv.reader(csvfile)
            for row in lines:
                if not data_started:
                    if row[0].startswith('#'):
                        fon_index = 0
                        obj_index = 1
                        meta_index = 2
                        # TODO: get exact row IDs without hardcoded
                        data_started = True
                        datum.append([fon_bcp47, obj_bcp47, ''])
                    continue
                datum.append([row[fon_index], row[obj_index], row[meta_index]])
                # print(', '.join(row))

        if is_stdout:
            txt_writer = csv.writer(sys.stdout)
            for line in datum:
                txt_writer.writerow(line)
        else:
            old_file = open(file_output, 'w')
            old_file.truncate()
            old_file.close()

            with open(file_output, 'a') as new_txt:
                txt_writer = csv.writer(new_txt)
                for line in datum:
                    txt_writer.writerow(line)

    def in_jsonkv(self, hxlated_input, file_output, is_stdout, args):
        """Convert HXLTM to output 'JSON-kv'

        Args:
            hxlated_input ([str]): Path to HXLated CSV
            tmx_output ([str]): Path to file to write output (if not stdout)
            is_stdout (bool): Flag to tell the output is stdout
            args ([type]): python argparse
        """

        # fon_ling = HXLTMUtil.linguam_2_hxlattrs(args.fontem_linguam)
        # fon_bcp47 = HXLTMUtil.bcp47_from_linguam(args.fontem_linguam)
        # obj_ling = HXLTMUtil.linguam_2_hxlattrs(args.objectivum_linguam)
        # obj_bcp47 = HXLTMUtil.bcp47_from_linguam(args.objectivum_linguam)

        data_started = False
        fon_index = None
        obj_index = None
        # meta_index = None
        datum = {}
        with open(hxlated_input, 'r') as csvfile:
            lines = csv.reader(csvfile)
            for row in lines:
                if not data_started:
                    if row[0].startswith('#'):
                        fon_index = 0
                        obj_index = 1
                        # meta_index = 2
                        # TODO: get exact row IDs without hardcoded
                        data_started = True
                        # datum.append([fon_bcp47, obj_bcp47, ''])
                    continue
                datum[row[fon_index]] = row[obj_index]
                # print(', '.join(row))
        json_out = json.dumps(
            datum, indent=4, sort_keys=True, ensure_ascii=False)

        if is_stdout:
            # print(json_out)
            for line in json_out.split("\n"):
                print(line)
                # sys.stdout.write(line + "\n")

        else:
            old_file = open(file_output, 'w')
            old_file.truncate()
            old_file.close()

            # TODO: test this part better.
            with open(file_output, 'a') as new_txt:
                new_txt.write(json_out)
                # txt_writer = csv.writer(new_txt)
                # for line in datum:
                #     txt_writer.writerow(line)

    def in_tmx(self, hxlated_input, tmx_output, is_stdout, args):
        """
        in_tmx is  is the main method to de facto make the conversion.

        TODO: this is a work-in-progress at this moment, 2021-06-28
        @see https://en.wikipedia.org/wiki/Translation_Memory_eXchange
        @see https://www.gala-global.org/lisa-oscar-standards
        @see https://cloud.google.com/translate/automl/docs/prepare
        @see http://xml.coverpages.org/tmxSpec971212.html
        """

        datum = []

        with open(hxlated_input, 'r') as csv_file:
            # TODO: fix problem if input data already only have HXL hashtags
            #       but no extra headings (Emerson Rocha, 2021-06-28 01:27 UTC)

            # Hotfix: skip first non-HXL header. Ideally I think the already
            # exported HXlated file should already save without headers.
            next(csv_file)

            csvReader = csv.DictReader(csv_file)

            # Convert each row into a dictionary
            # and add it to data
            for item in csvReader:

                datum.append(HXLTMUtil.tmx_item_relevan_options(item))

        resultatum = []
        resultatum.append("<?xml version='1.0' encoding='utf-8'?>")
        resultatum.append('<!DOCTYPE tmx SYSTEM "tmx14.dtd">')
        resultatum.append('<tmx version="1.4">')
        # @see https://www.gala-global.org/sites/default/files/migrated-pages
        #      /docs/tmx14%20%281%29.dtd
        resultatum.append(
            '  <header creationtool="hxltm" creationtoolversion="' +
            __VERSION__ + '" ' +
            'segtype="sentence" o-tmf="UTF-8" ' +
            'adminlang="en" srclang="en" datatype="PlainText"/>')
        # TODO: make source and adminlang configurable
        resultatum.append('  <body>')

        num = 0

        for rem in datum:
            num += 1

            # unit_id = rem['#item+id'] if '#item+id' in rem else num
            if '#item+id' in rem:
                unit_id = rem['#item+id']
            elif '#item+conceptum+codicem' in rem:
                unit_id = rem['#item+conceptum+codicem']
            else:
                unit_id = num

            resultatum.append('    <tu tuid="' + str(unit_id) + '">')
            if '#item+wikidata+code' in rem and rem['#item+wikidata+code']:
                resultatum.append(
                    '      <prop type="wikidata">' +
                    rem['#item+wikidata+code'] + '</prop>')

            if '#meta+item+url+list' in rem and rem['#meta+item+url+list']:
                resultatum.append(
                    # TODO: improve naming
                    '      <prop type="meta_urls">' + \
                    rem['#meta+item+url+list'] + '</prop>')

            hattrsl = HXLTMUtil.hxllangattrs_list_from_item(rem)
            # print(hattrsl)
            for langattrs in hattrsl:
                # print(langattrs)

                if '#item' + langattrs in rem:
                    keylang = '#item' + langattrs
                elif '#item+rem' + langattrs in rem:
                    keylang = '#item+rem' + langattrs
                else:
                    keylang = 'no-key-found-failed'

                if keylang in rem:
                    bcp47 = HXLTMUtil.bcp47_from_hxlattrs(langattrs)
                    resultatum.append('      <tuv xml:lang="' + bcp47 + '">')
                    resultatum.append(
                        '        <seg>' + rem[keylang] + '</seg>')
                    resultatum.append('      </tuv>')

            resultatum.append('    </tu>')

        resultatum.append('  </body>')
        resultatum.append('</tmx>')

        if is_stdout:
            for ln in resultatum:
                print(ln)
        else:
            tmx_output_cleanup = open(tmx_output, 'w')
            tmx_output_cleanup.truncate()
            tmx_output_cleanup.close()

            with open(tmx_output, 'a') as new_txt:
                for ln in resultatum:
                    new_txt.write(ln + "\n")
                    # print (ln)

    def in_tmx_de_hxltmasa(self, archivum_objectivum: Union[str, None]):
        """HXLTM In Fōrmātum Translation Memory eXchange format (TMX) v1.4

        Args:
            archivum_objectivum (Union[str, None]):
                Archīvum locum, id est, Python file path
        """

        farmatum_tmx = HXLTMInFormatumTMX(self.hxltm_asa)

        if archivum_objectivum is None:
            return farmatum_tmx.in_normam_exitum()

        farmatum_tmx.in_archivum(archivum_objectivum)

    def in_xliff(self, hxlated_input, xliff_output, is_stdout, args):
        """
        in_xliff is  is the main method to de facto make the conversion.

        TODO: this is a work-in-progress at this moment, 2021-06-28
        """

        datum = []

        with open(hxlated_input, 'r') as csv_file:
            csvReader = csv.DictReader(csv_file)

            # Convert each row into a dictionary
            # and add it to data
            for item in csvReader:

                datum.append(HXLTMUtil.xliff_item_relevant_options(item))

        resultatum = []
        resultatum.append('<?xml version="1.0"?>')
        resultatum.append(
            '<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" ' +
            'version="2.0" srcLang="en" trgLang="fr">')
        resultatum.append('  <file id="f1">')

        num = 0

        for rem in datum:
            num += 1
            if '#x_xliff+unit+id' in rem and rem['#x_xliff+unit+id']:
                unit_id = rem['#x_xliff+unit+id']
            else:
                unit_id = num
            # unit_id = rem['#x_xliff+unit+id'] if rem['#x_xliff+unit+id'] \
            #               else num
            resultatum.append('      <unit id="' + str(unit_id) + '">')

            resultatum.append('        <segment>')

            xsource = HXLTMUtil.xliff_item_xliff_source_key(rem)
            if xsource:
                if not rem[xsource]:
                    resultatum.append(
                        '          <!-- ERROR source ' + str(unit_id) +
                        ', ' + xsource + '-->')
                    if not args.silentium:
                        print('ERROR:', unit_id, xsource)
                        # TODO: make exit status code warn about this
                        #       so other scripts can deal with bad output
                        #       when --silentium is not used
                    # continue
                else:
                    resultatum.append('          <source>' +
                                      rem[xsource] + '</source>')

            xtarget = HXLTMUtil.xliff_item_xliff_target_key(rem)
            if xtarget and rem[xtarget]:
                resultatum.append('          <target>' +
                                  rem[xtarget] + '</target>')

            resultatum.append('        </segment>')

            resultatum.append('      </unit>')

        resultatum.append('  </file>')
        resultatum.append('</xliff>')

        if is_stdout:
            for ln in resultatum:
                print(ln)
        else:
            xliff_output_cleanup = open(xliff_output, 'w')
            xliff_output_cleanup.truncate()
            xliff_output_cleanup.close()

            with open(xliff_output, 'a') as new_txt:
                for ln in resultatum:
                    new_txt.write(ln + "\n")
                    # print (ln)

    def in_xliff_old(self, hxlated_input, xliff_output, is_stdout, args):
        """
        in_xliff is  is the main method to de facto make the conversion.

        TODO: this is a work-in-progress at this moment, 2021-06-28
        """

        datum = []

        with open(hxlated_input, 'r') as csv_file:
            csvReader = csv.DictReader(csv_file)

            # Convert each row into a dictionary
            # and add it to data
            for item in csvReader:

                datum.append(HXLTMUtil.xliff_item_relevant_options(item))

        resultatum = []
        resultatum.append('<?xml version="1.0"?>')
        resultatum.append(
            '<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" ' +
            'version="2.0" srcLang="en" trgLang="fr">')
        resultatum.append('  <file id="f1">')

        num = 0

        for rem in datum:
            num += 1
            if '#x_xliff+unit+id' in rem and rem['#x_xliff+unit+id']:
                unit_id = rem['#x_xliff+unit+id']
            else:
                unit_id = num
            # unit_id = rem['#x_xliff+unit+id'] if rem['#x_xliff+unit+id'] \
            #               else num
            resultatum.append('      <unit id="' + str(unit_id) + '">')

            resultatum.append('        <segment>')

            xsource = HXLTMUtil.xliff_item_xliff_source_key(rem)
            if xsource:
                if not rem[xsource]:
                    resultatum.append(
                        '          <!-- ERROR source ' + str(unit_id) +
                        ', ' + xsource + '-->')
                    if not args.silentium:
                        print('ERROR:', unit_id, xsource)
                        # TODO: make exit status code warn about this
                        #       so other scripts can deal with bad output
                        #       when --silentium is not used
                    # continue
                else:
                    resultatum.append('          <source>' +
                                      rem[xsource] + '</source>')

            xtarget = HXLTMUtil.xliff_item_xliff_target_key(rem)
            if xtarget and rem[xtarget]:
                resultatum.append('          <target>' +
                                  rem[xtarget] + '</target>')

            resultatum.append('        </segment>')

            resultatum.append('      </unit>')

        resultatum.append('  </file>')
        resultatum.append('</xliff>')

        if is_stdout:
            for ln in resultatum:
                print(ln)
        else:
            xliff_output_cleanup = open(xliff_output, 'w')
            xliff_output_cleanup.truncate()
            xliff_output_cleanup.close()

            with open(xliff_output, 'a') as new_txt:
                for ln in resultatum:
                    new_txt.write(ln + "\n")
                    # print (ln)

    def in_xliff_de_hxltmasa(self, archivum_objectivum: Union[str, None]):
        """HXLTM In Fōrmātum Translation Memory eXchange format (TMX) v1.4

        Args:
            archivum_objectivum (Union[str, None]):
                Archīvum locum, id est, Python file path
        """

        farmatum_xliff = HXLTMInFormatumXLIFF(self.hxltm_asa)

        if archivum_objectivum is None:
            return farmatum_xliff.in_normam_exitum()

        farmatum_xliff.in_archivum(archivum_objectivum)

    def in_csv_header(
            self, hxlated_header, fontem_linguam, objectivum_linguam):
        """
        _[eng-Latn] Convert the Main HXL TM file to a single or source to
                    target XLIFF translation pair
        [eng-Latn]_

# item+id                         -> #x_xliff+unit+id
# meta+archivum                   -> #x_xliff+file
# item+wikidata+code              -> #x_xliff+unit+note+note_category__wikidata
# meta+wikidata+code              -> #x_xliff+unit+note+note_category__wikidata
# meta+item+url+list              -> #x_xliff+unit+notes+note_category__url
# item+type+lat_dominium+list     -> #x_xliff+group+group_0
#                             (We will not implement deeper levels  than 0 now)

    [contextum: XLIFF srcLang]
# item(*)+i_ZZZ+is_ZZZZ            -> #x_xliff+source+i_ZZZ+is_ZZZZ
# status(*)+i_ZZZ+is_ZZZZ+xliff
                            -> #meta+x_xliff+segment_source+state+i_ZZZ+is_ZZZZ
                                   (XLIFF don't support)
# meta(*)+i_ZZZ+is_ZZZZ            -> #x_xliff+unit+note+note_category__source
# meta(*)+i_ZZZ+is_ZZZZ+list       -> #x_xliff+unit+notes+note_category__source

    [contextum: XLIFF trgLang]
# item(*)+i_ZZZ+is_ZZZZ            -> #x_xliff+target+i_ZZZ+is_ZZZZ
# status(*)+i_ZZZ+is_ZZZZ+xliff    -> #x_xliff+segment+state+i_ZZZ+is_ZZZZ
# meta(*)+i_ZZZ+is_ZZZZ            -> #x_xliff+unit+note+note_category__target
# meta(*)+i_ZZZ+is_ZZZZ+list       -> #x_xliff+unit+notes+note_category__target

        _[eng-Latn] TODO:
- Map XLIFF revisions back MateCat back to HXL TM
  @see http://docs.oasis-open.org/xliff/xliff-core/v2.1/os
       /xliff-core-v2.1-os.html#revisions
        [eng-Latn]_
        """

        # TODO: improve this block. I'm very sure there is some cleaner way to
        #       do it in a more cleaner way (fititnt, 2021-01-28 08:56 UTC)

        fon_ling = HXLTMUtil.linguam_2_hxlattrs(fontem_linguam)
        fon_bcp47 = HXLTMUtil.bcp47_from_hxlattrs(fontem_linguam)
        obj_ling = HXLTMUtil.linguam_2_hxlattrs(objectivum_linguam)
        obj_bcp47 = HXLTMUtil.bcp47_from_hxlattrs(objectivum_linguam)

        for idx, _ in enumerate(hxlated_header):

            if hxlated_header[idx].startswith('#x_xliff'):
                # Something explicitly was previously defined with #x_xliff
                # So we will intentionally ignore on this step.
                # This could be useful if someone is trying to translate twice
                continue

            elif hxlated_header[idx] == '#item+id' or \
                    hxlated_header[idx] == '#item +conceptum +codicem':
                hxlated_header[idx] = '#x_xliff+unit+id'
                continue

            elif hxlated_header[idx] == '#meta+archivum':
                hxlated_header[idx] = '#x_xliff+file'
                continue

            elif hxlated_header[idx] == '#meta+item+url+list':
                hxlated_header[idx] = '#x_xliff+unit+notes+note_category__url'
                continue

            elif hxlated_header[idx] == '#item+wikidata+code' or \
                    hxlated_header[idx] == '#meta+wikidata+code' or \
                    hxlated_header[idx] == '#meta+conceptum+codicem+alternativum':  # noqa
                hxlated_header[idx] = \
                    '#x_xliff+unit+note+note_category__wikidata'
                continue

            elif hxlated_header[idx] == '#item+type+lat_dominium+list' or \
                    hxlated_header[idx] == '#item+conceptum+dominium':
                hxlated_header[idx] = '#x_xliff+group+group_0'
                continue

            elif hxlated_header[idx].startswith('#item'):

                if hxlated_header[idx].find(fon_ling) > -1 and \
                        not hxlated_header[idx].find('+list') > -1:
                    hxlated_header[idx] = '#x_xliff+source' + \
                        fon_bcp47 + fon_ling
                elif hxlated_header[idx].find(obj_ling) > -1 and \
                        not hxlated_header[idx].find('+list') > -1:
                    hxlated_header[idx] = '#x_xliff+target' + obj_ling

                continue

            elif hxlated_header[idx].startswith('#status'):
                if hxlated_header[idx].find(fon_ling) > -1 and \
                        not hxlated_header[idx].find('+list') > -1:
                    # TODO: maybe just ignore source state? XLIFF do not
                    #       support translations from source languages that
                    #       are not ideally ready yet
                    if hxlated_header[idx].find('+xliff') > -1:
                        hxlated_header[idx] = '#x_xliff+segment+state' + \
                            fon_bcp47 + fon_ling
                elif hxlated_header[idx].find(obj_ling) > -1 and \
                        not hxlated_header[idx].find('+list') > -1:
                    if hxlated_header[idx].find('+xliff') > -1:
                        hxlated_header[idx] = '#x_xliff+segment+state' + \
                            obj_bcp47 + obj_ling
                if hxlated_header[idx] != '#status':
                    print('#status ERROR?, FIX ME', hxlated_header[idx])
                continue

            elif hxlated_header[idx].startswith('#meta'):
                # @see http://docs.oasis-open.org/xliff/xliff-core/v2.1/os
                #      /xliff-core-v2.1-os.html#category

                if hxlated_header[idx].find(fon_ling) > -1:
                    if hxlated_header[idx].find('+list') > -1:
                        hxlated_header[idx] = \
                            '#x_xliff+unit+notes+note_category__source'
                    else:
                        hxlated_header[idx] = \
                            '#x_xliff+unit+note+note_category__source'
                    continue

                if hxlated_header[idx].find(obj_ling) > -1:
                    if hxlated_header[idx].find('+list') > -1:
                        hxlated_header[idx] = \
                            '#x_xliff+unit+notes+note_category__target'
                    else:
                        hxlated_header[idx] = \
                            '#x_xliff+unit+note+note_category__target'
                    continue

                # We will ignore other #metas
                continue

        return hxlated_header


@dataclass
class HXLTMASA:
    """HXLTM Abstractum Syntaxim Arborem

    _[eng-Latn]
    The HXLTM-ASA is an not strictly documented Abstract Syntax Tree
    of an data conversion operation.

    This format, different from the HXLTM permanent storage, is not
    meant to be used by end users. And, in fact, either JSON (or other
    formats, like YAML) are more a tool for users debugging the initial
    reference implementation hxltmcli OR developers using JSON
    as more advanced input than the end user permanent storage.

    Warning: The HXLTM-ASA is not meant to be an stricly documented format
    even if HXLTM eventually get used by large public. If necessary,
    some special format could be created, but this would require feedback
    from community or some work already done by implementers.
    [eng-Latn]_

    Trivia:
        - abstractum, https://en.wiktionary.org/wiki/abstractus#Latin
        - syntaxim, https://en.wiktionary.org/wiki/syntaxis#Latin
        - arborem, https://en.wiktionary.org/wiki/arbor#Latin
        - conceptum de Abstractum Syntaxim Arborem
            - https://www.wikidata.org/wiki/Q127380

    Exemplōrum gratiā (et Python doctest, id est, testum automata):

>>> datum = HXLTMTestumAuxilium.datum('hxltm-exemplum-linguam.tm.hxl.csv')
>>> ontologia = HXLTMTestumAuxilium.ontologia()

# TODO: fix this after refactoring HXLTMDatum
>>> asa = HXLTMASA(datum, ontologia=ontologia)
>>> asa
HXLTMASA(fontem_linguam=None, objectivum_linguam=None, \
alternativum_linguam=None)
    """

    # pylint: disable=too-many-instance-attributes

    datum: InitVar[Type['HXLTMDatum']] = None
    hxltm_crudum: InitVar[List] = []
    ontologia: InitVar[Type['HXLTMOntologia']] = None

    # TODO: migrade from HXLTMcli to HXLTMASA the
    # fontem_linguam, objectivum_linguam, alternativum_linguam, linguam
    fontem_linguam: Type['HXLTMLinguam'] = None
    objectivum_linguam: Type['HXLTMLinguam'] = None
    alternativum_linguam: List[Type['HXLTMLinguam']] = None

    # @see https://la.wikipedia.org/wiki/Lingua_agendi
    agendum_linguam: InitVar[List[Type['HXLTMLinguam']]] = []
    # linguam: List[Type['HXLTMLinguam']] = None

    columnam_numerum: InitVar[List] = []  # deprecated
    non_columnam_numerum: InitVar[List] = []  # deprecated

    # Trivia: līmitem, https://en.wiktionary.org/wiki/limes#Latin
    limitem_quantitatem: InitVar[int] = -1  # deprecated
    limitem_initiale_lineam: InitVar[int] = -1  # deprecated

    argumentum: InitVar[Type['HXLTMArgumentum']] = None
    _verbosum: InitVar[bool] = False  # deprecated

    def __init__(self,
                 fontem_crudum_datum: Union[List[List], str],
                 #  hxltm_crudum: List[List] = None,
                 #  hxltm_archivum: str = None,
                 ontologia: Union[Type['HXLTMOntologia'], Dict] = None,
                 argumentum: Type['HXLTMArgumentum'] = None):
        """

        Args:
            hxltm_crudum (List[List]):
                _[lat-Latn]
                Crudum HXLTM Archīvum (in Python Array de Array)
                [lat-Latn]_
            ontologia (Union[Type['HXLTMOntologia'], Dict]):
                _[lat-Latn]
                HXLTM Cor Ontologia e.g. cor.hxltm.yml (in Python Dict)
                [lat-Latn]_
            argumentum (HXLTMArgumentum):
                _[lat-Latn]
                HXLTMArgumentum
                [lat-Latn]_
        """

        # self.hxltm_crudum = hxltm_crudum
        self.ontologia = ontologia

        if argumentum is not None:
            self.argumentum = argumentum
        else:
            self.argumentum = HXLTMArgumentum()

        # if argumentum:
        #     if hasattr(argumentum, 'columnam_numerum'):
        #         self.columnam_numerum = argumentum.columnam_numerum
        #     if hasattr(argumentum, 'non_columnam_numerum'):
        #         self.non_columnam_numerum = argumentum.non_columnam_numerum
        #     if hasattr(argumentum, 'limitem_quantitatem'):
        #         self.limitem_quantitatem = argumentum.limitem_quantitatem
        #     if hasattr(argumentum, 'limitem_initiale_lineam'):
        #         self.limitem_initiale_lineam = \
        #             argumentum.limitem_initiale_lineam

        self.datum = HXLTMDatum(
            fontem_crudum_datum,
            # limitem_quantitatem=self.limitem_quantitatem,
            # limitem_initiale_lineam=self.limitem_initiale_lineam,
            argumentum=self.argumentum)
        # self.argumentum = argumentum
        # self._venandum_insectum = verbosum

        self._initiale(argumentum)

    def _initiale(self, argumentum):
        """HXLTMASA initiāle

        Trivia: initiāle, https://en.wiktionary.org/wiki/initialis#Latin

        Args:
            argumentum (Dict):
                _[lat-Latn]
                Python argumentum,
                https://docs.python.org/3/library/argparse.html
                [lat-Latn]_
            venandum_insectum (bool, optional):
            _[lat-Latn]
                Vēnandum īnsectum est? Defallo falsum
            [lat-Latn]_
        """
        # if args.expertum_metadatum_est:
        #     self.expertum_metadatum_est = args.expertum_metadatum_est

        # TODO: migrate all this to HXLTMASA._initiale

        # _[eng-Latn] Process the comment line argumetns [eng-Latn]_
        if argumentum:

            if argumentum.fontem_linguam:
                self.fontem_linguam = HXLTMLinguam(argumentum.fontem_linguam)
                # if is_debug:
                #     print('fontem_linguam', self.fontem_linguam.v())

            if argumentum.objectivum_linguam:
                self.objectivum_linguam = HXLTMLinguam(
                    argumentum.objectivum_linguam)
                # if is_debug:
                #     print('objectivum_linguam', self.objectivum_linguam.v())

            if argumentum.alternativum_linguam and \
                    len(argumentum.alternativum_linguam) > 0:
                unicum = set(argumentum.alternativum_linguam)
                for rem in unicum:
                    rem_obj = HXLTMLinguam(rem)
                    # if is_debug:
                    #     print('alternativum_linguam', rem_obj.v())
                    self.alternativum_linguam.append(rem_obj)

            if argumentum.agendum_linguam and \
                    len(argumentum.agendum_linguam) > 0:
                unicum = set(argumentum.agendum_linguam)
                for rem in unicum:
                    rem_obj = HXLTMLinguam(rem)
                    # if is_debug:
                    #     print('linguam', rem_obj.v())
                    self.agendum_linguam.append(rem_obj)

    def _initiale_hxltm_crudum(self, hxltm_crudum):
        pass

    def v(self, _verbosum: bool = None):  # pylint: disable=invalid-name
        """Ego python Dict

        Trivia:
         - valendum, https://en.wiktionary.org/wiki/valeo#Latin
           - Anglicum (English): value (?)
         - verbosum, https://en.wiktionary.org/wiki/verbosus#Latin

        Args:
            _verbosum (bool): Verbosum est? Defallo falsum.

        Returns:
            [Dict]: Python dict
        """

        asa = {
            # A TL;DR of what the ASA file is
            '__ASA__': {
                'asa_nomen': 'HXLTM Abstractum Syntaxim Arborem',
                'instrumentum_varians': __SYSTEMA_VARIANS__,
                'instrumentum_versionem': __VERSION__,
            },
            # Somewhat portable reference of how the HXLTM ASA was generate
            # from souce input. This can be used by each tool to define
            # it's own parameters. But is preferable to try to use options
            # that could be reused by others
            '__ASA__INSTRUMENTUM__': {
                # 'agendum_linguam': 'mul-Zyyy'
                'agendum_linguam': []
            },

            # Similar to __ASA__INSTRUMENTUM__ (a place for tools to put
            # metadata about the datum) but the main point here is this
            # can store information that is temporary and may not make
            # sense if the ASA is shared on other computers or for long term.
            # One example is the path for the hxltm CSV temporary file on
            # local disk.
            # Why store path to temporary file? Because if HXLTM ASA is used
            # to preprocess data for another tool, a tool could still do
            # raw reading of the CSV file on disk without need to enable
            # verbose modes.
            '__ASA__TEMPORARIUM__': {
                # archīvum, https://en.wiktionary.org/wiki/archivum
                'archivum_bytes': -1,
                'archivum_temporarium_locum': None,
                'columnam_crudum_quantitatem': -1,
                # TODO: maybe implement some way to make a cheapy full
                #       disk check for how many line breaks do a file have.
                #       This could be useful for tools trying to decode CSV
                #       without being aware that may exist line breaks inside
                #       row items (they are valid).
                # @see https://stackoverflow.com/questions/845058
                # /how-to-get-line-count-of-a-large-file-cheaply-in-python
                # /27518377#27518377
                'lineam_crudum_quantitatem': -1,
                'limitem_quantitatem': self.limitem_quantitatem,
                'limitem_initiale_lineam': self.limitem_initiale_lineam,
            },
            '_datum_meta_': {},
            # '_datum_meta_': {
            #     'caput': [],
            #     # columnam, https://en.wiktionary.org/wiki/columna#Latin
            #     'columnam_quantitatem': -1,
            #     # līneam, https://en.wiktionary.org/wiki/linea#Latin
            #     'columnam_quantitatem': -1,
            #     'rem_quantitatem': -1,
            # },
            'datum': {}
        }

        asa['_datum_meta_'] = self.datum.meta.v(self._verbosum)

        if self.fontem_linguam:
            asa['__ASA__INSTRUMENTUM__']['fontem_linguam'] = \
                self.fontem_linguam.v(self._verbosum)

        if self.objectivum_linguam:
            asa['__ASA__INSTRUMENTUM__']['objectivum_linguam'] = \
                self.objectivum_linguam.v(self._verbosum)

        if self.alternativum_linguam and len(self.alternativum_linguam) > 0:
            asa['__ASA__INSTRUMENTUM__']['alternativum_linguam'] = []
            for rem_al in self.alternativum_linguam:
                asa['__ASA__INSTRUMENTUM__']['alternativum_linguam'].append(
                    rem_al.v(self._verbosum)
                )

        if self.agendum_linguam and len(self.agendum_linguam) > 0:
            asa['__ASA__INSTRUMENTUM__']['agendum_linguam'] = []
            for rem_al in self.agendum_linguam:
                asa['__ASA__INSTRUMENTUM__']['agendum_linguam'].append(
                    rem_al.v(self._verbosum)
                )

        return asa


@dataclass
class HXLTMArgumentum:
    """HXLTM Argūmentum

    Trivia:
        - HXLTM:
        - HXLTM, https://hdp.etica.ai/hxltm
            - HXL, https://hxlstandard.org/
            - TM, https://www.wikidata.org/wiki/Q333761
        - argūmentum, https://en.wiktionary.org/wiki/argumentum#Latin

    Intrōductōrium cursum de Latīnam linguam (breve glōssārium):
        - archīvum, https://en.wiktionary.org/wiki/archivum
        - agendum linguam
            - https://la.wikipedia.org/wiki/Lingua_agendi
        - collēctiōnem, https://en.wiktionary.org/wiki/collectio#Latin
        - columnam, https://en.wiktionary.org/wiki/columna#Latin
        - datum, https://en.wiktionary.org/wiki/datum#Latin
        - fontem, https://en.wiktionary.org/wiki/fons#Latin
        - fōrmātum, https://en.wiktionary.org/wiki/formatus#Latin
        - initiāle, https://en.wiktionary.org/wiki/initialis#Latin
        - ignōrandum, https://en.wiktionary.org/wiki/ignoro#Latin
        - linguam, https://en.wiktionary.org/wiki/lingua#Latin
        - līmitem, https://en.wiktionary.org/wiki/limes#Latin
        - līneam, https://en.wiktionary.org/wiki/linea#Latin
        - multiplum linguam:
            - linguam
            - multiplum, https://en.wiktionary.org/wiki/multiplus#Latin
        - objectīvum, https://en.wiktionary.org/wiki/objectivus#Latin
        - quantitātem, https://en.wiktionary.org/wiki/quantitas
        - typum, https://en.wiktionary.org/wiki/typus#Latin
        - sēcūrum, https://en.wiktionary.org/wiki/securus#Latin
        - sēlēctum, https://en.wiktionary.org/wiki/selectus#Latin
        - sōlum, https://en.wiktionary.org/wiki/solus#Latin
        - silentium, https://en.wiktionary.org/wiki/silentium
        - Vēnandum īnsectum
          - https://www.wikidata.org/wiki/Q845566

    Args:
        agendum_linguam (List[HXLTMLinguam]):
            _[lat-Latn]
            Objectīvum linguam
            (Optiōnem in multiplum linguam aut bilingue operātiōnem)
            [lat-Latn]_
        fontem_linguam (HXLTMLinguam):
            _[lat-Latn]
            Fontem linguam
            (Optiōnem sōlum in bilingue operātiōnem)
            [lat-Latn]_
        objectivum_linguam (HXLTMLinguam):
            _[lat-Latn]
            Objectīvum linguam
            (Optiōnem sōlum in bilingue operātiōnem)
            [lat-Latn]_
        objectivum_formatum (HXLTMLinguam):
            _[lat-Latn]
            OArgūmentum dēfīnītiōnem ad objectīvum archīvum fōrmātum
            [lat-Latn]_
        columnam_numerum (List):
            _[lat-Latn] Datum sēlēctum columnam numerum [lat-Latn]_
        non_columnam_numerum (List):
            _[lat-Latn] Datum non sēlēctum columnam numerum [lat-Latn]_
        limitem_quantitatem (int):
            _[lat-Latn] Datum līmitem līneam quantitātem [lat-Latn]_
        limitem_quantitatem (int):
            _[lat-Latn] Datum līmitem līneam quantitātem [lat-Latn]_
        limitem_initiale_lineam (int):
            _[lat-Latn] Datum initiāle līneam [lat-Latn]_
        silentium (bool):
            _[lat-Latn]
            Argūmentum dēfīnītiōnem ad silentium
            [lat-Latn]_
        ad_astra (bool):
            _[lat-Latn]
            Argūmentum ad astra per aspera
            (Non sēcūrum. Ignōrandum Python Exception et computandum līmitem)
            [lat-Latn]_
        venandum_insectum (bool):
            _[lat-Latn]
            Argūmentum dēfīnītiōnem ad Vēnandum īnsectum
            [lat-Latn]_
    """
    agendum_linguam: InitVar[List[Type['HXLTMLinguam']]] = []
    fontem_linguam: InitVar[Type['HXLTMLinguam']] = None
    objectivum_linguam: InitVar[Type['HXLTMLinguam']] = None
    objectivum_formatum: InitVar[str] = 'HXLTM'
    columnam_numerum: InitVar[List] = []
    non_columnam_numerum: InitVar[List] = []
    limitem_initiale_lineam: InitVar[int] = -1
    limitem_quantitatem: InitVar[int] = 1048576
    silentium: InitVar[bool] = False
    ad_astra: InitVar[bool] = False
    venandum_insectum: InitVar[bool] = False

    # def de_argparse(self, args_rem: Type['ArgumentParser']):
    def de_argparse(self, args_rem: Dict = None):
        """Argūmentum de Python argparse

        Args:
            args_rem (Dict, optional):
                Python ArgumentParser. Defallo Python None

        Returns:
            [HXLTMArgumentum]: Ego HXLTMArgumentum
        """
        if args_rem is not None:
            if hasattr(args_rem, 'agendum_linguam'):
                self.est_agendum_linguam(args_rem.agendum_linguam)
            if hasattr(args_rem, 'fontem_linguam'):
                self.est_fontem_linguam(args_rem.fontem_linguam)
            if hasattr(args_rem, 'objectivum_linguam'):
                self.est_objectivum_linguam(args_rem.objectivum_linguam)

            if hasattr(args_rem, 'columnam_numerum'):
                self.columnam_numerum = args_rem.columnam_numerum
            if hasattr(args_rem, 'non_columnam_numerum'):
                self.non_columnam_numerum = args_rem.non_columnam_numerum

            if hasattr(args_rem, 'limitem_quantitatem'):
                self.limitem_quantitatem = args_rem.limitem_quantitatem
            if hasattr(args_rem, 'limitem_initiale_lineam'):
                self.limitem_initiale_lineam = \
                    args_rem.limitem_initiale_lineam

            if hasattr(args_rem, 'silentium'):
                self.est_ad_astra(args_rem.silentium)

            if hasattr(args_rem, 'ad_astra'):
                self.est_ad_astra(args_rem.ad_astra)

            if hasattr(args_rem, 'venandum_insectum'):
                self.est_venandum_insectum(args_rem.venandum_insectum)

            # TODO: deprecated, remove venandum_insectum
            if hasattr(args_rem, 'venandum_insectum'):
                self.est_venandum_insectum(args_rem.venandum_insectum)

        return self

    def est_ad_astra(self, rem: bool):
        """Argūmentum ad astra per aspera

        (Non sēcūrum. Ignōrandum Python Exception et computandum līmitem)

        Args:
            rem (Union[str, HXLTMLinguam]): Rem

        Returns:
            [HXLTMArgumentum]: Ego HXLTMArgumentum
        """
        self.ad_astra = bool(rem)

        return self

    def est_agendum_linguam(self, rem: Union[str, list]):
        """Argūmentum dēfīnītiōnem ad agendum linguam

        (Optiōnem in multiplum linguam aut bilingue operātiōnem)

        Args:
            rem (Union[str, HXLTMLinguam]): Rem

        Returns:
            [HXLTMArgumentum]: Ego HXLTMArgumentum
        """
        if isinstance(rem, list):
            unicum = set(rem)
            for item in unicum:
                if isinstance(rem, HXLTMLinguam):
                    self.agendum_linguam.append(item)
                else:
                    self.agendum_linguam.append(HXLTMLinguam(item))
        elif isinstance(rem, str):
            collectionem = rem.split(',')
            unicum = set(collectionem)
            for item in collectionem:
                self.agendum_linguam.append(HXLTMLinguam(item.trim()))
        elif rem is None:
            # self.agendum_linguam.append(HXLTMLinguam())
            self.agendum_linguam = []
        else:
            raise SyntaxError('Rem typum incognitum {}'.format(str(rem)))

        return self

    def est_fontem_linguam(self, rem: Union[str, Type['HXLTMLinguam']]):
        """Argūmentum dēfīnītiōnem ad fontem linguam

        (Optiōnem sōlum in bilingue operātiōnem)

        Args:
            rem (Union[str, HXLTMLinguam]): Rem

        Returns:
            [HXLTMArgumentum]: Ego HXLTMArgumentum
        """
        if isinstance(rem, HXLTMLinguam):
            self.fontem_linguam = rem
        else:
            self.fontem_linguam = HXLTMLinguam(rem)
        return self

    def est_objectivum_formatum(self, rem: str = 'HXLTM'):
        """Argūmentum dēfīnītiōnem ad objectīvum archīvum fōrmātum

        Args:
            rem (Union[str, HXLTMLinguam]): Rem

        Returns:
            [HXLTMArgumentum]: Ego HXLTMArgumentum
        """
        if rem is None or len(rem) == 0:
            self.objectivum_linguam = 'HXLTM'
        else:
            self.objectivum_linguam = rem

        return self

    def est_objectivum_linguam(self, rem: Union[str, Type['HXLTMLinguam']]):
        """Argūmentum dēfīnītiōnem ad objectīvum linguam

        (Optiōnem sōlum in bilingue operātiōnem)

        Args:
            rem (Union[str, HXLTMLinguam]): Rem

        Returns:
            [HXLTMArgumentum]: Ego HXLTMArgumentum
        """
        if isinstance(rem, HXLTMLinguam):
            self.objectivum_linguam = rem
        else:
            self.objectivum_linguam = HXLTMLinguam(rem)
        return self

    def est_silentium(self, rem: bool):
        """Argūmentum dēfīnītiōnem ad silentium

        Args:
            rem (bool): Rem

        Returns:
            [HXLTMArgumentum]: Ego HXLTMArgumentum
        """
        self.silentium = bool(rem)

        return self

    def est_venandum_insectum(self, rem: bool):
        """Argūmentum dēfīnītiōnem ad Vēnandum īnsectum

        Args:
            rem (bool): Rem

        Returns:
            [HXLTMArgumentum]: Ego HXLTMArgumentum
        """
        self.venandum_insectum = bool(rem)

        return self

    def v(self, _verbosum: bool = None):  # pylint: disable=invalid-name
        """Ego python Dict

        Trivia:
         - valendum, https://en.wiktionary.org/wiki/valeo#Latin
           - Anglicum (English): value (?)
         - verbosum, https://en.wiktionary.org/wiki/verbosus#Latin

        Args:
            _verbosum (bool): Verbosum est? Defallo falsum.

        Returns:
            [Dict]: Python objectīvum
        """
        return self.__dict__


@dataclass
class HXLTMDatum:
    """
    _[eng-Latn]
    HXLTMDatum is a python wrapper for the an HXLated HXLTM dataset. It
    either be initialized by a raw Python array of arrays (with 1st or 2nd)
    row with the HXL hashtags) or with a path for a file on local disk.

    One limitation (that is unlikely to be a problem) is, similar to
    softwares like Pandas (and unlikely libhxl, that play nice with streams)
    this class requires load all the data on the memory instead of process
    row by row.

    NOTE: see also HXLTMASA(). Both are similar but HXLTMASA() could in some
          cases to be implemented eventually hold more than one HXlated
          dataset in memory, so HXLTMDatum is somewhat a simplified version
          (whitout awareness of ontologia, for example).
    [eng-Latn]_

        Args:
            crudum_datum (Union[List[List], str]):
            argumentum (HXLTMArgumentum):
                _[lat-Latn]
                HXLTMArgumentum
                [lat-Latn]_
    """

    # crudum: InitVar[List] = []
    crudum_caput: InitVar[List] = []
    crudum_hashtag: InitVar[List] = []
    columnam_numerum: InitVar[List] = []
    non_columnam_numerum: InitVar[List] = []
    limitem_quantitatem: InitVar[int] = 1048576
    limitem_initiale_lineam: InitVar[int] = -1
    meta: InitVar[Type['HXLTMDatumCaput']] = None
    # datum_rem: InitVar[List] = []
    columnam: InitVar[List] = []
    # ontologia: InitVar[Type['HXLTMOntologia']] = None
    argumentum: InitVar[Type['HXLTMArgumentum']] = None
    venandum_insectum: InitVar[bool] = False

    def __init__(self,
                 crudum_datum: Union[List[List], str],
                 argumentum: Type['HXLTMArgumentum'] = None):
        """[summary]

        Args:
            hxltm_crudum (str, List[List]): Datum
            argumentum (HXLTMArgumentum): HXLTMArgumentum
        """

        if argumentum is not None:
            self.argumentum = argumentum
        else:
            self.argumentum = HXLTMArgumentum()

        # self.ontologia = ontologia
        # self.venandum_insectum = venandum_insectum  # deprecated
        # self.columnam_numerum = columnam_numerum  # deprecated
        # self.non_columnam_numerum = non_columnam_numerum  # deprecated
        # self.limitem_quantitatem = limitem_quantitatem  # deprecated
        # self.limitem_initiale_lineam = limitem_initiale_lineam  # deprecated

        # print('limitem_initiale_lineam', self.limitem_initiale_lineam)

        # Check: is this an array of arrays (hxltm_crudum) or a path to
        # a file on disk?

        if isinstance(crudum_datum, str):
            self._initialle_de_hxltm_archivum(crudum_datum)
        elif isinstance(crudum_datum, list):
            self._initialle_de_hxltm_crudum(crudum_datum)
        else:
            raise SyntaxError('HXLTMDatum crudum aut archivum non vacuum')

    def _initialle_de_hxltm_archivum(self, archivum: str):
        """
        Trivia: initiāle, https://en.wiktionary.org/wiki/initialis#Latin
        """
        crudum_titulum = []
        crudum_hashtag = []
        datum_rem = []
        datum_rem_brevis = []

        with open(archivum, 'r') as hxl_archivum:
            csv_lectorem = csv.reader(hxl_archivum)
            rem_prius = None
            for _ in range(25):
                rem_nunc = next(csv_lectorem)
                if HXLTMDatumCaput.quod_est_hashtag_caput(rem_nunc):
                    if rem_prius is not None:
                        crudum_titulum = rem_prius
                    crudum_hashtag = rem_nunc
                    break
                rem_prius = rem_nunc
            if len(crudum_hashtag) == 0:
                # This is not supposed to happen, since the file should
                # already be parsed previously by libhxl
                raise SyntaxError('HXLTMDatum quod archīvum HXL hashtags?')

            for rem in csv_lectorem:
                datum_rem.append(rem)
        # print(datum_rem)
        # print('oooi')
        # print(len(datum_rem[0]))

        if len(datum_rem) > 0:
            # self.datum_rem = datum_rem
            datum_rem_brevis = datum_rem[:5]
            for item_num in range(len(datum_rem[0])):
                # print('oi2', item_num)

                # TODO: --non-selectum-columnam-numerum
                #         dont apply if item_num in self.non_columnam_numerum

                col_rem_val = HXLTMDatumColumnam.reducendum_de_datum(
                    datum_rem,
                    item_num,
                    limitem_quantitatem=self.argumentum.limitem_quantitatem,
                    limitem_initiale_lineam=self.argumentum.limitem_initiale_lineam  # noqa
                )
                self.columnam.append(HXLTMDatumColumnam(
                    col_rem_val
                ))
                # print(type(self.columnam[0]))

        self.meta = HXLTMDatumCaput(
            crudum_titulum=crudum_titulum,
            crudum_hashtag=crudum_hashtag,
            datum_rem_brevis=datum_rem_brevis,
            columnam_collectionem=self.columnam,
            venandum_insectum=self.argumentum.venandum_insectum
        )

    def _initialle_de_hxltm_crudum(self, hxltm_crudum: List):
        """
        Trivia: initiāle, https://en.wiktionary.org/wiki/initialis#Latin
        """

        # Note: when using hxltm_crudum, the array of arrays must already
        #       be near strictly valid. We will only check where is the
        #       hashtag line and if do exist a heading line.
        crudum_titulum = []
        crudum_hashtag = []
        # datum_rem = []
        if HXLTMDatumCaput.quod_est_hashtag_caput(hxltm_crudum[0]):
            crudum_hashtag = hxltm_crudum[0]
            hxltm_crudum.pop(0)
        elif HXLTMDatumCaput.quod_est_hashtag_caput(hxltm_crudum[1]):
            crudum_titulum = hxltm_crudum[0]
            crudum_hashtag = hxltm_crudum[1]
            hxltm_crudum.pop(0)
            hxltm_crudum.pop(0)
        else:
            # print(hxltm_crudum[0])
            # print(hxltm_crudum[1])
            raise SyntaxError('HXLTMDatum quod crudum HXL hashtags?')

        # At this point, hxltm_crudum, if any, should have only data
        if len(hxltm_crudum) > 0:
            if len(crudum_hashtag) != len(hxltm_crudum[0]):
                raise SyntaxError(
                    'HXLTMDatum hashtag numerum [{}] non aequalis '
                    'datum numerum [{}]'.format(
                        len(crudum_hashtag),
                        len(hxltm_crudum[0])
                    ))

            # self.datum_rem = datum_rem
            # datum_rem_brevis = hxltm_crudum[:5]
            for item_num in range(len(crudum_hashtag)):

                # TODO: --non-selectum-columnam-numerum
                #         dont apply if item_num in self.non_columnam_numerum

                col_rem_val = HXLTMDatumColumnam.reducendum_de_datum(
                    hxltm_crudum,
                    item_num,
                    limitem_quantitatem=self.argumentum.limitem_quantitatem,
                    limitem_initiale_lineam=self.argumentum.limitem_initiale_lineam)  # noqa
                self.columnam.append(HXLTMDatumColumnam(
                    col_rem_val
                ))

        self.meta = HXLTMDatumCaput(
            crudum_titulum=crudum_titulum,
            crudum_hashtag=crudum_hashtag,
            # datum_rem_brevis=[],
            columnam_collectionem=self.columnam,
            venandum_insectum=self.argumentum.venandum_insectum
        )

    def rem_de_numerum(self, numerum: int):
        # return numerum
        return self.columnam[0]

    def rem_iterandum(self) -> Type['HXLTMRemIterandum']:
        return HXLTMRemIterandum(self)

    def rem_quantitatem(self) -> int:
        """Rem quantitatem tōtāle numerum

        Trivia:
        - tōtāle, https://en.wiktionary.org/wiki/totalis#Latin

        Returns:
            int: [description]
        """
        totale = 0

        if self.columnam is not None and len(self.columnam) > 0:
            totale = self.columnam[0].quantitatem
        return totale

    def v(self, verbosum: bool = None, clavem: str = None):
        """Ego python Dict

        Trivia:
         - valendum, https://en.wiktionary.org/wiki/valeo#Latin
           - Anglicum (English): value (?)
         - clāvem, https://en.wiktionary.org/wiki/clavis#Latin
         - verbosum, https://en.wiktionary.org/wiki/verbosus#Latin

        Args:
            verbosum (bool): Verbosum est? Defallo falsum.

        Returns:
            [Dict]: Python objectīvum
        """
        # pylint: disable=invalid-name

        if verbosum is not False:
            verbosum = verbosum or self.argumentum.venandum_insectum

        resultatum = {
            '_typum': 'HXLTMDatum',
            # 'crudum_caput': self.crudum_caput,
            # 'crudum_hashtag': self.crudum_hashtag,
            'meta': self.meta.v(verbosum),
            'limitem_quantitatem': self.argumentum.limitem_quantitatem,
            'limitem_initiale_lineam': self.argumentum.limitem_initiale_lineam,
            # optio --venandum-insectum-est requirere
            # 'columnam': []
        }

        if verbosum:
            resultatum['crudum_caput'] = self.crudum_caput
            resultatum['crudum_hashtag'] = self.crudum_hashtag
            resultatum['columnam'] = \
                [item.v(verbosum) if item else None for item in self.columnam]

        if clavem is not None:
            return resultatum['clavem']

        return resultatum


@dataclass
class HXLTMDatumColumnam:
    """HXLTM Datum columnam summārius

    Trivia:
    - HXLTM, https://hdp.etica.ai/hxltm
    - Datum, https://en.wiktionary.org/wiki/datum#Latin
    - Columnam, https://en.wiktionary.org/wiki/columna#Latin
    - summārius, https://en.wiktionary.org/wiki/summary#English
    - valendum, https://en.wiktionary.org/wiki/valeo#Latin
      - 'value' , https://en.wiktionary.org/wiki/value#English
    - quantitātem , https://en.wiktionary.org/wiki/quantitas
    """
    # pylint: disable=too-many-instance-attributes

    _typum: InitVar[str] = None   # Used only when output JSON
    datum_typum: InitVar['str'] = None
    quantitatem: InitVar[int] = None
    # limitem_quantitatem: InitVar[int] = 1048576
    # limitem_initiale_lineam: InitVar[int] = -1
    _valendum: InitVar[List] = None

    # self._typum = 'HXLTMRemCaput'  # Used only when output JSON

    def __init__(self, valendum: List):
        #  limitem_quantitatem: int = 1048576,
        #  limitem_initiale_lineam: int = -1):

        self._typum = 'HXLTMDatumColumnam'
        # self.limitem_quantitatem = limitem_quantitatem
        # self.limitem_initiale_lineam = limitem_initiale_lineam
        # self._valendum = valendum
        self.quantitatem = len(valendum) if valendum is not None else 0
        self.datum_typum = HXLTMTypum.collectionem_datum_typum(valendum)

    @staticmethod
    def reducendum_de_datum(
            datum: List,
            columnam: int,
            limitem_quantitatem: int = 1048576,
            limitem_initiale_lineam: int = -1) -> List:
        """Redūcendum Columnam de datum

        Args:
            datum (List): Datum [rem x col]
            columnam (int): Numerum columnam in datum

        Returns:
            List: Unum columnam
        """
        resultatum = []
        if datum is not None and len(datum) > 0:
            for rem_num, _ in enumerate(datum):  # numero de linhas
                # for col_num in enumerate(datum[0]): # Número de colunas

                if limitem_initiale_lineam != -1:
                    limitem_quantitatem += limitem_initiale_lineam

                # TODO: test if is not off-by-one
                if (rem_num >= limitem_initiale_lineam) and \
                        (rem_num <= limitem_quantitatem):
                    resultatum.append(datum[rem_num][columnam])
                # else:
                #     print('ignored' + str(rem_num))
                # resultatum.append(datum[rem_num])
        # pass # redūcendum_Columnam_de_datum
        return resultatum

    def v(self, verbosum: bool = False):  # pylint: disable=invalid-name
        """Ego python Dict

        Trivia:
         - valendum, https://en.wiktionary.org/wiki/valeo#Latin
           - Anglicum (English): value (?)
         - verbosum, https://en.wiktionary.org/wiki/verbosus#Latin

        Args:
            verbosum (bool): Verbosum est? Defallo falsum.

        Returns:
            [Dict]: Python objectīvum
        """
        resultatum = {
            '_typum': self._typum,
            'quantitatem': self.quantitatem,
            'datum_typum': self.datum_typum,
        }

        # return self.__dict__
        return resultatum


@dataclass
class HXLTMDatumCaput:  # pylint: disable=too-many-instance-attributes
    """
    _[eng-Latn]
    HXLTMDatumCaput contains data about hashtags, raw headings (if they
    exist on original dataset) of a dataset
    [eng-Latn]_

        Exemplōrum gratiā (et Python doctest, id est, testum automata):

>>> rem = HXLTMDatumCaput(
...   ['id', 'Nōmen', 'Annotātiōnem'],
...   ['#item+id', '#item+lat_nomen', ''],
...   [
...      [1, 'Marcus canem amat.', 'Vērum!'],
...      [2, 'Canem Marcus amat.', ''],
...      [3, 'Amat canem Marcus.', 'vērum? vērum!']
...   ])
>>> rem.quod_datum_rem_correctum_est()
True
>>> rem.quod_datum_rem_correctum_est([[4, 'Marcus amat canem.', '']])
True
>>> rem.quod_datum_rem_correctum_est([['Canem amat Marcus.', '']])
False
>>> rem.titulum_de_columnam(0)
'id'
>>> rem.titulum_de_columnam(1)
'Nōmen'
>>> rem.titulum_de_columnam(2)
'Annotātiōnem'
>>> rem.titulum_de_columnam(9999)
False
>>> rem.hxl_hashtag_de_columnam(0)
'#item+id'
>>> rem.hxl_hashtag_de_columnam(1)
'#item+lat_nomen'
>>> rem.hxl_hashtag_de_columnam(2) is None
True
    """

    # crudum: InitVar[List] = []
    rem: InitVar[List] = []
    crudum_hashtag: InitVar[List] = []
    datum_rem_brevis: InitVar[List] = []
    columnam_quantitatem: InitVar[int] = 0
    columnam_quantitatem_hxl: InitVar[int] = 0
    columnam_quantitatem_hxl_unicum: InitVar[int] = 0
    columnam_quantitatem_nomen: InitVar[int] = 0
    columnam_quantitatem_nomen_unicum: InitVar[int] = 0
    venandum_insectum: InitVar[bool] = False

    def __init__(
            self,
            crudum_titulum: List,
            crudum_hashtag: List,
            datum_rem_brevis: List = None,
            columnam_collectionem: List[Type['HXLTMDatumColumnam']] = None,
            argumentum: Type['HXLTMArgumentum'] = None,
            venandum_insectum: bool = False  # deprecated
    ):

        self.crudum_titulum = crudum_titulum
        self.crudum_hashtag = crudum_hashtag
        self.datum_rem_brevis = datum_rem_brevis
        if argumentum is not None:
            self.argumentum = argumentum
        else:
            self.argumentum = HXLTMArgumentum()
        self.venandum_insectum = venandum_insectum

        # self.rem = [123]

        self._initialle(
            crudum_titulum, crudum_hashtag,
            datum_rem_brevis, columnam_collectionem)

    def _initialle(
        self,
        crudum_titulum: List,
        crudum_hashtag: List,
        datum_rem_brevis: List,
        columnam_collectionem: List[Type['HXLTMDatumColumnam']] = None
    ):
        """
        Trivia: initiāle, https://en.wiktionary.org/wiki/initialis#Latin
        """
        # self.quod_est_hashtag_caput

        non_vacuum_nomen = list(filter(len, crudum_titulum))
        # print(crudum_titulum)
        # print(crudum_hashtag)

        self.datum_rem_brevis = datum_rem_brevis
        # _[eng-Latn]
        # crudum_hashtag also have empty spaces, so it still can be used to
        # know how many columns do exist
        # [eng-Latn]_
        self.columnam_quantitatem = len(crudum_hashtag)
        self.columnam_quantitatem_hxl = \
            self.quod_est_hashtag_caput(crudum_hashtag)
        self.columnam_quantitatem_hxl_unicum = \
            self.quod_est_hashtag_caput(set(crudum_hashtag))
        self.columnam_quantitatem_nomen = len(non_vacuum_nomen)
        self.columnam_quantitatem_nomen_unicum = \
            len(set(non_vacuum_nomen))

        # self.rem = [123]

        # Note:
        # print('columnam_collectionem', columnam_collectionem)
        # print('columnam_collectionem', len(columnam_collectionem))
        for item_num in range(self.columnam_quantitatem):
            # if columnam_collectionem is not None and item_num in
            if columnam_collectionem is not None:
                col_meta = columnam_collectionem[item_num]
                # print('acerto')
            else:
                # print('erro')
                col_meta = None
            self.rem.append(HXLTMRemCaput(
                columnam=item_num,
                columnam_meta=col_meta,
                hashtag=self.hxl_hashtag_de_columnam(item_num),
                titulum=self.titulum_de_columnam(item_num),
            ))
            # print(col)

    def hxl_hashtag_de_columnam(self, numerum: int) -> Union[str, None]:
        """HXL hashtag dē columnam numerum

        Trivia:
          - HXL, https://hxlstandard.org/
          - hashtag, https://en.wiktionary.org/wiki/hashtag
          - dē, https://en.wiktionary.org/wiki/de#Latin
          - columnam, https://en.wiktionary.org/wiki/columna#Latin
          - numerum, https://en.wiktionary.org/wiki/numerus#Latin

        Args:
            numerum (int): Numerum de columnam. Initiāle 0.

        Returns:
            Union[str, None, False]:
                HXL Hashtag aut python None aut python False
        """

        if numerum < 0 or numerum >= len(self.crudum_hashtag):
            # _[eng-Latn]Called on a wrong, invalid, index[eng-Latn]_
            return False
        if len(self.crudum_hashtag[numerum]) == 0:
            return None
        # print('oi1', self.crudum_hashtag)
        # print('oi2', self.crudum_hashtag[numerum])
        return self.crudum_hashtag[numerum]

    def quod_datum_rem_correctum_est(
            self, datum_rem_brevis: List = None) -> bool:
        """Quod datum rem corrēctum est?

        _[eng-Latn]
        Very basic check to test if the number of columnam_quantitatem is exact
        the number of data rows. While we do tolerate rows without
        any text heading name or HXL hashtag, the number of rows (tagged or
        not) must match. Without this is very likely we will put data on
        wrong place when trying to relate they by index number (order they
        appear on the dataset)
        [eng-Latn]_

        Args:
            datum_rem_brevis (List):
                _[eng-Latn]
                List of list of custom data to test. Can be used to test
                new data from a previous created item.
                The default is use the initial data provide when
                constructing the data object.
                [eng-Latn]_

        Returns:
            bool: Verum: rem corrēctum est.
        """
        if datum_rem_brevis is None:
            datum_rem_brevis = self.datum_rem_brevis

        if len(datum_rem_brevis) == 0:
            # _[eng-Latn] Empty data is acceptable [eng-Latn]_
            return True

        return self.columnam_quantitatem == len(datum_rem_brevis[0])

    @staticmethod
    def quod_est_hashtag_caput(rem: List) -> Union[bool, int]:
        """HXL hashtag caput est?

        @see hxl.HXLReader.parse_tags()
              https://github.com/HXLStandard/libhxl-python/blob/main/hxl/io.py

        Args:
            rem (List):
                _[eng-Latn] List to test [eng-Latn]_

        Returns:
            Union[bool, int]:
                _[eng-Latn]
                False if not seems to be a HXLated; int with total
                number of columns started with #
                [eng-Latn]_
        """
        # Same as FUZZY_HASHTAG_PERCENTAGE = 0.5 from libhxl
        min_limit = 50
        total = 0
        hashtag_like = 0
        for item in rem:
            total += 1
            if item.startswith('#'):
                hashtag_like += 1

        est_hashtag = (hashtag_like > 0) and \
            ((total / hashtag_like * 100) > min_limit)

        return hashtag_like if est_hashtag else False

    def linguam_de_columnam(self, numerum: int) -> Type['HXLTMLinguam']:
        """Nōmen dē columnam numerum

        Trivia:
          - linguam, https://en.wiktionary.org/wiki/lingua#Latin
          - dē, https://en.wiktionary.org/wiki/de#Latin
          - columnam, https://en.wiktionary.org/wiki/columna#Latin
          - numerum, https://en.wiktionary.org/wiki/numerus#Latin

        Args:
            numerum (int): Numerum de columnam. Initiāle 0.

        Returns:
            Union[str, None]: linguam aut python None
        """
        # https://en.wiktionary.org/wiki/columna#Latin
        print('TODO')

    def titulum_de_columnam(self, numerum: int) -> Union[str, None]:
        """Nomen dē columnam numerum

        Trivia:
          - nōmen, https://en.wiktionary.org/wiki/nomen#Latin
          - dē, https://en.wiktionary.org/wiki/de#Latin
          - columnam, https://en.wiktionary.org/wiki/columna#Latin
          - numerum, https://en.wiktionary.org/wiki/numerus#Latin

        Args:
            numerum (int): Numerum de columnam. Initiāle 0.

        Returns:
            Union[str, None, False]: nōmen aut python None aut python False
        """
        # https://en.wiktionary.org/wiki/columna#Latin
        if numerum < 0 or numerum >= len(self.crudum_titulum):
            # _[eng-Latn]Called on a wrong, invalid, index[eng-Latn]_
            return False
        if len(self.crudum_titulum[numerum]) == 0:
            return None

        return self.crudum_titulum[numerum]

    def v(self, verbosum: bool = None):  # pylint: disable=invalid-name
        """Ego python Dict

        Trivia:
         - valendum, https://en.wiktionary.org/wiki/valeo#Latin
           - Anglicum (English): value (?)
         - verbosum, https://en.wiktionary.org/wiki/verbosus#Latin

        Args:
            verbosum (bool): Verbosum est? Defallo falsum.

        Returns:
            [Dict]: Python objectīvum
        """
        if verbosum is not False:
            verbosum = verbosum or self.venandum_insectum

        resultatum = {
            'caput': [item.v(verbosum) if item else None for item in self.rem],
            # 'crudum_titulum': self.crudum_titulum,
            # 'crudum_hashtag': self.crudum_hashtag,
            'columnam_quantitatem': self.columnam_quantitatem,
            'columnam_quantitatem_hxl': self.columnam_quantitatem_hxl,
            'columnam_quantitatem_hxl_unicum': \
            self.columnam_quantitatem_hxl_unicum,
            'columnam_quantitatem_nomen': self.columnam_quantitatem_nomen,
            'columnam_quantitatem_nomen_unicum':
            self.columnam_quantitatem_nomen_unicum,
            # 'venandum_insectum': self.venandum_insectum,
        }

        if verbosum:
            resultatum['crudum_titulum'] = self.crudum_titulum
            resultatum['crudum_hashtag'] = self.crudum_hashtag

        # return self.__dict__
        return resultatum


class HXLTMRem:

    def __init__(self, hxltm_datum: Type['HXLTMDatum'], rem_numerum: int):
        self.hxltm_datum = hxltm_datum

        # TODO: implement HXLTMRem by, via the item FIRST row number of a
        #       grouped rem and point to hxltm_datum, generate a Row
        #       with only HXLTMRemCaput (future HXLTMDatumCaput) plus
        #       the data of grouped rem

        self.rem_hoc = 0
        self.rem_quantitatem = hxltm_datum.rem_quantitatem()


class HXLTMRemIterandum:
    """HXLTM

    Trivia:
        - HXLTM:
        - HXLTM, https://hdp.etica.ai/hxltm
            - HXL, https://hxlstandard.org/
            - TM, https://www.wikidata.org/wiki/Q333761
        - disciplīnam manuāle
            - https://docs.python.org/3/library/abc.html

    Raises:
        StopIteration: fīnāle
    """

    # @see https://en.wiktionary.org/wiki/iterator
    # @see https://en.wiktionary.org/wiki/itero#Latin

    def __init__(self, hxltm_datum: Type['HXLTMDatum'] = None):
        self.hxltm_datum = hxltm_datum

        self.rem_hoc = 0
        self.rem_quantitatem = hxltm_datum.rem_quantitatem()

    def __iter__(self):
        return self

    def __next__(self):
        self.rem_hoc += 1
        if self.rem_hoc < self.rem_quantitatem:
            return self.hxltm_datum.rem_de_numerum(self.rem_hoc)
        raise StopIteration

# for c in HXLTMRemIterandum():
#     print(c)

# fōrmātum	https://en.wiktionary.org/wiki/formatus#Latin


class HXLTMInFormatum(ABC):
    """HXLTM In Fōrmātum; abstractum Python classem

    Trivia:
        - HXLTM:
        - HXLTM, https://hdp.etica.ai/hxltm
            - HXL, https://hxlstandard.org/
            - TM, https://www.wikidata.org/wiki/Q333761
        - in, https://en.wiktionary.org/wiki/in-#Latin
        - fōrmātum, https://en.wiktionary.org/wiki/formatus#Latin
        - abstractum Python classem
            - abstractum, https://en.wiktionary.org/wiki/abstractus#Latin
            - Python, https://docs.python.org/
            - classem, https://en.wiktionary.org/wiki/classis#Latin
        - disciplīnam manuāle
            - https://docs.python.org/3/library/abc.html

    Intrōductōrium cursum de Latīnam linguam (breve glōssārium):
        - archīvum, https://en.wiktionary.org/wiki/archivum
        - datum, https://en.wiktionary.org/wiki/datum#Latin
        - corporeum, https://en.wiktionary.org/wiki/corporeus#Latin
        - collēctiōnem, https://en.wiktionary.org/wiki/collectio#Latin
            - id est: Python List
        - dē, https://en.wiktionary.org/wiki/de#Latin
        - errōrem, https://en.wiktionary.org/wiki/error#Latin
        - fīnāle, https://en.wiktionary.org/wiki/finalis#Latin
        - 'id est', https://en.wiktionary.org/wiki/id_est
        - initiāle, https://en.wiktionary.org/wiki/initialis#Latin
        - locum, https://en.wiktionary.org/wiki/locum#Latin
        - resultātum, https://en.wiktionary.org/wiki/resultatum

    Speciāle verbum in HXLTM:
        - 'Exemplōrum gratiā (et Python doctest, id est, testum automata)'
            - Exemplōrum gratiā
              - https://en.wikipedia.org/wiki/List_of_Latin_phrases_(full)
            - 'Python doctest' (non Latīnam)
                -https://docs.python.org/3/library/doctest.html

    Author:
        Multis Clanculum Civibus

    Collaborators:
        Emerson Rocha <rocha[at]ieee.org>

    Creation Date:
        2021-07-14

    Revisions:

    License:
        Public Domain
    """

    # ontologia/cor.hxltm.yml clāvem nomen
    ONTOLOGIA_FORMATUM = ''

    # ontologia/cor.hxltm.yml basim extēnsiōnem
    # ONTOLOGIA_FORMATUM_BASIM = ''

    # @see https://docs.python.org/3/library/logging.html
    # @see https://docs.python.org/pt-br/dev/howto/logging.html

    def __init__(self, hxltm_asa: Type['HXLTMASA']):
        """HXLTM In Farmatum initiāle

        Args:
            hxltm_asa (HXLTMASA): HXLTMASA objectīvum
        """
        self.hxltm_asa = hxltm_asa

    def datum_initiale(self) -> List:  # pylint: disable=no-self-use
        """Datum initiāle de fōrmātum Lorem Ipsum vI.II

        Trivia:
            - datum, https://en.wiktionary.org/wiki/datum#Latin
            - initiāle, https://en.wiktionary.org/wiki/initialis#Latin

        Returns:
            List: Python List, id est: rem collēctiōnem
        """
        return []

    @abstractmethod
    def datum_corporeum(self) -> List:
        """Datum corporeum de fōrmātum Lorem Ipsum vI.II

        Trivia:
            - datum, https://en.wiktionary.org/wiki/datum#Latin
            - corporeum, https://en.wiktionary.org/wiki/corporeus#Latin

        Returns:
            List: Python List, id est: rem collēctiōnem
        """
        # _[eng-Latn]
        # The datum_corporeum() is a hard requeriment to implement a
        # file exporter.
        # [eng-Latn]_
        resultatum = []
        resultatum.append('<!-- 🚧 Opus in progressu 🚧 -->')
        resultatum.append('<!-- ' + __class__.__name__ + ' -->')
        resultatum.append('<!-- 🚧 Opus in progressu 🚧 -->')
        return resultatum

    def datum_finale(self) -> List:  # pylint: disable=no-self-use
        """Datum fīnāle de fōrmātum Lorem Ipsum vI.II

        Trivia:
            - datum, https://en.wiktionary.org/wiki/datum#Latin
            - fīnāle, https://en.wiktionary.org/wiki/finalis#Latin

        Returns:
            List: Python List, id est: rem collēctiōnem
        """
        return []

    def in_archivum(self, archivum_locum: str) -> None:
        """Resultātum in Archīvum

        Args:
            archivum_locum (str): Archīvum locum, id est, Python file path
        """
        resultatum = self.in_collectionem()

        with open(archivum_locum, 'w') as archivum_punctum:
            for rem in resultatum:
                archivum_punctum.write(rem + "\n")

    def in_collectionem(self) -> List:
        """Resultātum in collēctiōnem, id est Python List

        Returns:
            List: Python List, id est: rem collēctiōnem
        """
        # @see https://stackoverflow.com/questions/1720421
        #      /how-do-i-concatenate-two-lists-in-python
        resultatum = self.datum_initiale()
        corporeum = self.datum_corporeum()
        finale = self.datum_finale()

        resultatum += corporeum
        resultatum += finale

        return resultatum

    def in_exportandum(self):
        """Resultātum in defallo

        Raises:
            NotImplementedError:
        """
        raise NotImplementedError

    def in_textum(self) -> str:
        """Resultātum in textum, id est Python str

        Returns:
            str: Python str, id est: textum
        """
        return self.in_collectionem().join("\n")

    # def in_norman_errōrem(self) -> None
    # https://en.wiktionary.org/wiki/error#Latin

    def in_normam_exitum(self) -> None:
        """Resultātum in normam exitum, id est: Python stdout

        Trivia:
        - normam, https://en.wiktionary.org/wiki/norma#Latin
        - exitum, https://en.wiktionary.org/wiki/productio#Latin
        - etymologiam:
          - stdout, Standard output
            - https://en.wiktionary.org/wiki/stdout
            - https://en.wikipedia.org/wiki/Standard_streams
        - disciplīnam manuāle
            - https://docs.python.org/3/library/sys.html#sys.stdout
        """
        # TODO: _[eng-Latn]
        #       The current version of in_normam_exitum, since depends on
        #       HXLTMInFormatum.in_collectionem(), is not optimized for
        #       large inputs that do not fit in memory. Do exist room
        #       for improvement here if someone else is interested.
        #       (Emerson Rocha, 2021-07-14 09:52 UTC)
        #       [eng-Latn]_

        initiale = self.datum_initiale()

        if len(initiale) > 0:
            for rem in initiale:
                print(rem)

        corporeum = self.datum_corporeum()

        if len(corporeum) > 0:
            for rem in corporeum:
                print(rem)

        finale = self.datum_finale()

        if len(finale) > 0:
            for rem in finale:
                print(rem)

    def rem(self) -> Type['HXLTMRemIterandum']:

        # @see https://gist.github.com/drmalex07/6e040310ab9ac12b4dfd
        # @see https://dzone.com/articles/python-look-ahead-multiple
        return self.hxltm_asa.datum.rem_iterandum()


class HXLTMInFormatumTMX(HXLTMInFormatum):
    """HXLTM In Fōrmātum Translation Memory eXchange format (TMX) v1.4

    Trivia:
        - HXLTM:
        - HXLTM, https://hdp.etica.ai/hxltm
            - HXL, https://hxlstandard.org/
            - TM, https://www.wikidata.org/wiki/Q333761
        - in, https://en.wiktionary.org/wiki/in-#Latin
        - fōrmātum, https://en.wiktionary.org/wiki/formatus#Latin
        - TMX, https://www.wikidata.org/wiki/Q1890189

    Normam:
        - https://www.gala-global.org/tmx-14b

    Author:
        Emerson Rocha <rocha[at]ieee.org>

    Collaborators:
        (_[eng-Latn] Additional names here [eng-Latn]_)

    Creation Date:
        2021-07-14

    Revisions:

    License:
        Public Domain
    """

    ONTOLOGIA_FORMATUM = 'TMX'  # ontologia/cor.hxltm.yml clāvem nomen

    # initiāle	https://en.wiktionary.org/wiki/initialis#Latin
    def datum_initiale(self) -> List:
        """Datum initiāle de fōrmātum Translation Memory eXchange format
        (TMX) v1.4

        Trivia:
            - datum, https://en.wiktionary.org/wiki/datum#Latin
            - initiāle, https://en.wiktionary.org/wiki/initialis#Latin

        Returns:
            List: Python List, id est: rem collēctiōnem
        """

        resultatum = []
        resultatum.append("<?xml version='1.0' encoding='utf-8'?>")
        resultatum.append('<!DOCTYPE tmx SYSTEM "tmx14.dtd">')
        resultatum.append('<tmx version="1.4">')
        # @see https://www.gala-global.org/sites/default/files/migrated-pages
        #      /docs/tmx14%20%281%29.dtd
        resultatum.append(
            '  <header creationtool="hxltm" creationtoolversion="' +
            __VERSION__ + '" ' +
            'segtype="sentence" o-tmf="UTF-8" ' +
            'adminlang="en" srclang="en" datatype="PlainText"/>')
        # TODO: make source and adminlang configurable
        resultatum.append('  <body>')

        return resultatum

    def datum_corporeum(self) -> List:
        """Datum corporeum de fōrmātum Translation Memory eXchange format
        (TMX) v1.4

        Trivia:
            - datum, https://en.wiktionary.org/wiki/datum#Latin
            - corporeum, https://en.wiktionary.org/wiki/corporeus#Latin

        Returns:
            List: Python List, id est: rem collēctiōnem
        """
        resultatum = []
        resultatum.append('<!-- 🚧 Opus in progressu 🚧 -->')
        resultatum.append('<!-- ' + __class__.__name__ + ' -->')
        resultatum.append('<!-- 🚧 Opus in progressu 🚧 -->')

        # for numerum, rem in self.rem():
        # for rem, rem2 in self.rem():
        for rem in self.rem():
            # resultatum.append(rem.v())
            resultatum.append(str(rem))
        return resultatum

    def datum_finale(self) -> List:  # pylint: disable=no-self-use
        """Datum fīnāle de fōrmātum Translation Memory eXchange format
        (TMX) v1.4

        Trivia:
            - datum, https://en.wiktionary.org/wiki/datum#Latin
            - fīnāle, https://en.wiktionary.org/wiki/finalis#Latin

        Returns:
            List: Python List, id est: rem collēctiōnem
        """
        resultatum = []
        resultatum.append('  </body>')
        resultatum.append('</tmx>')
        return resultatum


class HXLTMInFormatumXLIFF(HXLTMInFormatum):
    """HXLTM In Fōrmātum XML Localization Interchange File Format (XLIFF) v2.1

    Trivia:
        - HXLTM:
        - HXLTM, https://hdp.etica.ai/hxltm
            - HXL, https://hxlstandard.org/
            - TM, https://www.wikidata.org/wiki/Q333761
        - in, https://en.wiktionary.org/wiki/in-#Latin
        - fōrmātum, https://en.wiktionary.org/wiki/formatus#Latin
        - XLIFF, <https://en.wikipedia.org/wiki/XLIFF>
        - disciplīnam manuāle
            - <https://docs.oasis-open.org/xliff/xliff-core/v2.1/>

    Normam:
        - <https://docs.oasis-open.org/xliff/xliff-core/v2.1/>

    Author:
        Emerson Rocha <rocha[at]ieee.org>

    Collaborators:
        (_[eng-Latn] Additional names here [eng-Latn]_)

    Creation Date:
        2021-07-14

    Revisions:

    License:
        Public Domain
    """

    def datum_initiale(self) -> List:
        """Datum initiāle de fōrmātum XML Localization Interchange File Format
        (XLIFF)

        Trivia:
            - datum, https://en.wiktionary.org/wiki/datum#Latin
            - initiāle, https://en.wiktionary.org/wiki/initialis#Latin

        Returns:
            List: Python List, id est: rem collēctiōnem
        """
        resultatum = []
        resultatum.append('<?xml version="1.0"?>')
        resultatum.append(
            '<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" ' +
            'version="2.0" srcLang="en" trgLang="fr">')
        resultatum.append('  <file id="f1">')

        return resultatum

    def datum_corporeum(self) -> List:
        """Datum corporeum de fōrmātum XML Localization Interchange File Format
        (XLIFF)

        Trivia:
            - datum, https://en.wiktionary.org/wiki/datum#Latin
            - corporeum, https://en.wiktionary.org/wiki/corporeus#Latin

        Returns:
            List: Python List, id est: rem collēctiōnem
        """
        resultatum = []
        resultatum.append('<!-- 🚧 Opus in progressu 🚧 -->')
        resultatum.append('<!-- ' + __class__.__name__ + ' -->')
        resultatum.append('<!-- 🚧 Opus in progressu 🚧 -->')
        return resultatum

    def datum_finale(self) -> List:  # pylint: disable=no-self-use
        """Datum fīnāle de fōrmātum

        Returns:
            List: Python List, id est: rem collēctiōnem
        """
        resultatum = []
        resultatum.append('  </file>')
        resultatum.append('</xliff>')
        return resultatum


class HXLTMOntologia:
    """
    _[eng-Latn] HXLTMOntologia is a python wrapper for the cor.hxltm.yml.
    [eng-Latn]_

    """

    def __init__(self, ontologia):
        """
        _[eng-Latn] Constructs all the necessary attributes for the
                    HXLTMOntologia object.
        [eng-Latn]_
        """
        self.crudum = ontologia
        self.initialle()

    def initialle(self):
        """
        Trivia: initiāle, https://en.wiktionary.org/wiki/initialis#Latin
        """
        # print('TODO')

    def hxl_de_aliud_nomen_breve(self, structum=False):
        """HXL attribūtum de aliud nōmen breve (cor.hxltm.yml)

        Trivia:
        - aliud, https://en.wiktionary.org/wiki/alius#Latin
        - nōmen, https://en.wiktionary.org/wiki/nomen#Latin
        - breve, https://en.wiktionary.org/wiki/brevis

        _[eng-Latn] For each item that have both __nomen_breve and __HXL,
                    create a flatten dictionary (only a key and value)
                    with the equivalent HXL hashtags.

                    This approach allows pass much more control logic to the
                    YAML file.
        [eng-Latn]_

        Returns:
            [Dict]: Dictionary
        """
        resultatum = {}
        # pylint: disable=invalid-name

        def recursionem(rem):
            # Trivia:
            # - recursiōnem, https://en.wiktionary.org/wiki/recursio#Latin
            for _k, v in rem.items():
                if isinstance(v, dict):
                    recursionem(v)
                else:
                    if '__HXL' in rem and '__nomen_breve' in rem:

                        if structum and rem['__nomen_breve'] in resultatum:
                            # TODO: improve this message
                            print('K [' + rem['__nomen_breve'] + ']')

                        resultatum[rem['__nomen_breve']] = \
                            ''.join(rem['__HXL'].split())

        recursionem(self.crudum['ontologia'])
        # print(resultatum)
        return resultatum

    def hxlhashtag(self, objectivum: Union[Dict, None], strictum=False):
        """Get __HXL non-whitespace value from an Dict

        Args:
            objectivum ([Dict]): an object with __HXL
            strictum (bool, optional): Raise error?. Defaults to False.

        Raises:
            RuntimeError: [description]

        Returns:
            [str]: an HXL hashtag without spaces
        """
        if objectivum is not None:
            if '__HXL' in objectivum:
                return ''.join(objectivum['__HXL'].split())

        if strictum:
            raise RuntimeError('HXLTMOntologia.hxlhashtag error')
        return None

    def de(self, dotted_key: str,  # pylint: disable=invalid-name
           default: Any = None, fontem: dict = None) -> Any:
        """
        Trivia: dē, https://en.wiktionary.org/wiki/de#Latin

        Examples:
            >>> exemplum = {'a': {'a2': 123}, 'b': 456}
            >>> otlg = HXLTMOntologia(exemplum)
            >>> otlg.de('a.a2', fontem=exemplum)
            123

        Args:
            dotted_key (str): Dotted key notation
            default ([Any], optional): Value if not found. Defaults to None.
            fontem (dict): An nested object to search

        Returns:
            [Any]: Return the result. Defaults to default
        """
        if fontem is None:
            fontem = self.crudum

        keys = dotted_key.split('.')
        return reduce(
            lambda d, key: d.get(
                key) if d else default, keys, fontem
        )


class HXLTMBCP47:
    """HXLTM BCP47 auxilium programmi

    _[eng-Latn] A non-dictionary aware BCP47 converter
                Note: this on this version depends on langcodes,
                <https://github.com/rspeer/langcodes>,
                So you need
                    pip3 install langcodes
    [eng-Latn]_


    Author:
            Emerson Rocha <rocha[at]ieee.org>
    Creation date:
            2021-06-09
    """

    def __init__(self, textum_bcp47: str):
        """

        """
        self.crudum = textum_bcp47

    @staticmethod
    def testum(textum: str) -> str:
        """testum est (...)

        Example:
            >>> HXLTMBCP47.testum('eng_US')
            'en-US'
            >>> HXLTMBCP47.testum('en-UK')
            'en-GB'

        Args:
            textum (str): [description]

        Returns:
            str: [description]
        """
        resultatum = langcodes.standardize_tag(textum)
        return resultatum

    @staticmethod
    def iso6392a3(textum: str) -> str:
        """iso6392a3, ISO 639-2 alphabētum 3 de BCP47 textum

        Example:
            >>> HXLTMBCP47.iso6392a3('eng_US')
            'eng'
            >>> HXLTMBCP47.iso6392a3('en-UK')
            'eng'
            >>> HXLTMBCP47.iso6392a3('en-UK')
            'eng'
            >>> HXLTMBCP47.iso6392a3('yue')
            'yue'

            # Romany [rom], https://iso639-3.sil.org/code/rom
            >>> HXLTMBCP47.iso6392a3('rom')
            'rom'

            # >>> HXLTMBCP47.iso6392a3('zh-TW')
            # '...'

        Args:
            textum (str): BCP47 language code string

        Returns:
            str: ISO 639-3 language code
        """
        L = langcodes.Language.get(textum)
        if L.is_valid():
            return L.to_alpha3()
            # resultatum = L.to_alpha3()
        return None


@dataclass
class HXLTMLinguam:  # pylint: disable=too-many-instance-attributes
    """HXLTM linguam auxilium programmi

    Exemplōrum gratiā (et Python doctest, id est, testum automata):

>>> HXLTMLinguam('lat-Latn@la-IT@IT')
HXLTMLinguam()

>>> HXLTMLinguam('lat-Latn@la-IT@IT').v()
{'_typum': 'HXLTMLinguam', \
'crudum': 'lat-Latn@la-IT@IT', 'linguam': 'lat-Latn', \
'bcp47': 'la-IT', 'imperium': 'IT', 'iso6391a2': 'la', 'iso6393': 'lat', \
'iso115924': 'Latn'}

>>> HXLTMLinguam('lat-Latn@la-IT@IT').a()
'+i_la+i_lat+is_latn+ii_it'

        Kalo Finnish Romani, Latin script (no ISO 2 language)

>>> HXLTMLinguam('rmf-Latn').v()
{'_typum': 'HXLTMLinguam', 'crudum': 'rmf-Latn', \
'linguam': 'rmf-Latn', 'iso6393': 'rmf', 'iso115924': 'Latn'}

        Kalo Finnish Romani, Latin script (no ISO 2 language, so no attr)

>>> HXLTMLinguam('rmf-Latn').a()
'+i_rmf+is_latn'

        Private use language tags: se use similar pattern of BCP 47.
        (https://tools.ietf.org/search/bcp47)

>>> HXLTMLinguam('lat-Latn-x-privatum').a()
'+i_lat+is_latn+ix_privatum'

>>> HXLTMLinguam('lat-Latn-x-privatum-tag8digt').a()
'+i_lat+is_latn+ix_privatum+ix_tag8digt'

        If x-private is only on BCP, we ignore it on HXL attrs.
        Tools may still use this for other processing (like for XLIFF),
        but not for generated Datasets.

>>> HXLTMLinguam(
... 'cmn-Latn@zh-Latn-CN-variant1-a-extend1-x-wadegile-private1').a()
'+i_zh+i_cmn+is_latn'

        To force a x-private language tag, it must be on linguam (first part)
        even if it means repeat. Also, we create attributes shorted by
        ASCII alphabet, as BCP47 would do

>>> HXLTMLinguam(
... 'cmn-Latn-x-wadegile-private1@zh-CN-x-wadegile-private1').a()
'+i_zh+i_cmn+is_latn+ix_private1+ix_wadegile'


>>> HXLTMLinguam(
... 'lat-Latn-x-caesar12-romanum1@la-IT-x-caesar12-romanum1@IT').a()
'+i_la+i_lat+is_latn+ii_it+ix_caesar12+ix_romanum1'

    """

    # Exemplum: lat-Latn@la-IT@IT, arb-Arab@ar-EG@EG
    _typum: InitVar[str] = None  # 'HXLTMLinguam'
    crudum: InitVar[str] = None
    linguam: InitVar[str] = None     # Exemplum: lat-Latn, arb-Arab
    bcp47: InitVar[str] = None       # Exemplum: la-IT, ar-EG
    imperium: InitVar[str] = None    # Exemplum: IT, EG
    iso6391a2: InitVar[str] = None     # Exemlum: la, ar
    iso6393: InitVar[str] = None     # Exemlum: lat, arb
    iso115924: InitVar[str] = None   # Exemplum: Latn, Arab
    privatum: InitVar[List[str]] = None  # Exemplum: [privatum]
    vacuum: InitVar[str] = False

    # https://tools.ietf.org/search/bcp47#page-2-12

    def __init__(self, linguam: str, strictum=False, vacuum=False):
        """HXLTMLinguam initiāle

        Args:
            linguam (str): Textum linguam
            strictum (bool, optional): Strictum est?.
                       Trivia: https://en.wiktionary.org/wiki/strictus#Latin
                       Defallo falsum.
            vacuum (bool, optional): vacuum	est?
                       Trivia: https://en.wiktionary.org/wiki/vacuus#Latin.
                       Defallo falsum.
        """
        # super().__init__()
        self._typum = 'HXLTMLinguam'  # Used only when output JSON
        self.crudum = linguam
        if not vacuum:
            self.initialle(strictum)
        else:
            self.vacuum = vacuum

    def initialle(self, strictum: bool):
        """
        Trivia: initiāle, https://en.wiktionary.org/wiki/initialis#Latin
        """

        term = self.crudum
        # Hackysh way to discover if private use is the linguam
        # tag or if is the BCP47 x-private use tag
        # Good example '4.4.2.  Truncation of Language Tags'
        # at https://tools.ietf.org/search/bcp47
        if self.crudum.find('x-') > -1:
            # print('Do exist a private-use tag')
            if self.crudum.find('@') > -1:
                parts = self.crudum.split('@')
                # print('parte1', parts)
                if parts[0].find('x-') > -1:
                    # _, privatumtext = parts[0].split('-x-')
                    part0, privatumtext = parts[0].split('-x-')
                    self.privatum = privatumtext.split('-')
                    parts.pop(0)
                    term = part0 + "@" + '@'.join(parts)
                    # print('term2', term)
                    # TODO: handle private use on linguan tag when
                    #       also BCP47 is used
            else:
                part0, privatumtext = self.crudum.split('-x-')
                self.privatum = privatumtext.split('-')
                term = part0

        if term.find('@') == -1:
            # Non @? Est linguam.
            self.linguam = term

            # self.iso6393, self.iso115924 = \
            #     list(self.linguam.split('-'))
        elif term.find('@@') > -1:
            # @@? Est linguam et imperium
            self.linguam, self.imperium = list(term.split('@@'))

            # self.iso6393, self.iso115924 = \
            #     list(self.linguam.split('-'))
        elif term.count('@') == 1:
            # Unum @? Est linguam et bcp47
            self.linguam, self.bcp47 = list(term.split('@'))

        elif term.count('@') == 2:
            # rem@rem@rem ? Est linguam, bcp47, imperium
            self.linguam, self.bcp47, self.imperium = \
                list(term.split('@'))
            # self.iso6393, self.iso115924 = \
            #     list(self.linguam.split('-'))
        elif strictum:
            raise ValueError('HXLTMLinguam [' + term + ']')
        else:
            return False

        if self.bcp47:
            parts = self.bcp47.split('-')
            if len(parts[0]) == 2:
                self.iso6391a2 = parts[0].lower()

        self.iso6393, self.iso115924 = \
            list(self.linguam.split('-'))

        self.iso6393 = self.iso6393.lower()
        self.iso115924 = self.iso115924.capitalize()
        self.linguam = self.iso6393 + '-' + self.iso115924
        if self.imperium:
            self.imperium = self.imperium.upper()

        if self.privatum is not None and len(self.privatum) > 0:
            # https://tools.ietf.org/search/bcp47#page-2-12
            # '4.5.  Canonicalization of Language Tags'
            # We short the keys
            # privatum_est = sorted(self.imperium, key=str.upper)

            # print('antes', self.imperium)
            privatum_est = sorted(self.privatum)

            # print('depois', self.privatum)
            self.privatum = privatum_est

        return True

    def a(self):  # pylint: disable=invalid-name
        """HXL attribūtum

        Exemplum:
            >>> HXLTMLinguam('lat-Latn@la-IT@IT').a()
            '+i_la+i_lat+is_latn+ii_it'

        Returns:
            [str]: textum HXL attribūtum
        """
        resultatum = []

        if self.iso6391a2:
            resultatum.append('+i_' + self.iso6391a2)
        if self.iso6393:
            resultatum.append('+i_' + self.iso6393)
        if self.iso115924:
            resultatum.append('+is_' + self.iso115924)
        if self.imperium:
            resultatum.append('+ii_' + self.imperium)
        if self.privatum and len(self.privatum) > 0:
            for item in self.privatum:
                resultatum.append('+ix_' + item)

        return ''.join(resultatum).lower()

    def designo(self, clavem: str, rem: Any) -> Type['HXLTMLinguam']:
        """Designo clavem rem

        _[eng-Latn] The HXLTMLinguam.designo() can be useful for create empty
                    languages with HXLTMLinguam('', vacuum=True) and then
                    manually defining what attributes would like when search
                    by hashtags
        [eng-Latn]_

       Args:
            clavem (str): clāvem, https://en.wiktionary.org/wiki/clavis#Latin
            rem (Any): rem, https://en.wiktionary.org/wiki/res#Latin

        Returns:
            [HXLTMLinguam]: HXLTMLinguam to allow method chaining

        Exemplum:
>>> rem_vacuum = HXLTMLinguam('', vacuum=True)
>>> rem = rem_vacuum.designo('iso115924', 'Latn')
>>> collectionem = [
...    '#item+conceptum+codicem',
...    '#item+rem+i_la+i_lat+is_latn',
...    '#item+definitionem+i_la+i_lat+is_latn',
...    '#item+rem+i_ar+i_arb+is_arab',
...    '#item+definitionem+i_ar+i_arb+is_arab'
... ]
>>> rem.intra_collectionem_est(collectionem)
['#item+rem+i_la+i_lat+is_latn', '#item+definitionem+i_la+i_lat+is_latn']


        """
        setattr(self, clavem, rem)
        return self

    def h(self, formatum: str):  # pylint: disable=invalid-name
        """HXL hashtag de fōrmātum

        Exemplum:
>>> HXLTMLinguam('lat-Latn@la-IT@IT').h('#item+rem__linguam__')
'#item+rem+i_la+i_lat+is_latn+ii_it'

>>> HXLTMLinguam('lat-Latn-x-privatum').h('#item+rem__linguam__')
'#item+rem+i_lat+is_latn+ix_privatum'

        Returns:
            [str]: textum HXL hashtag
        """
        linguam_attrs = self.a()

        if formatum.find('__linguam__') > -1:
            return formatum.replace('__linguam__', linguam_attrs)

        if formatum.find('__linguam_de_imperium__') > -1:
            return formatum.replace('__linguam_de_imperium__', linguam_attrs)

        raise ValueError('HXLTMLinguam fōrmātum errōrem [' + formatum + ']')

    def intra_collectionem_est(
            self, collectionem: List, formatum: str = None) -> List:
        """Intrā collēctiōnem est?

        Trivia:
        - intrā, https://en.wiktionary.org/wiki/intra#Latin
        - collēctiōnem, https://en.wiktionary.org/wiki/collectio#Latin
        - est, https://en.wiktionary.org/wiki/est#Latin


        Args:
            collectionem (List): List of HXL hashtags
            formatum (str): An formatted template.

        Returns:
            [List]: List of HXL hashtags that match the search

        Tests:

>>> rem = HXLTMLinguam('lat-Latn@la')
>>> collectionem = [
...    '#item+conceptum+codicem',
...    '#item+rem+i_la+i_lat+is_latn',
...    '#item+definitionem+i_la+i_lat+is_latn',
...    '#item+rem+i_ar+i_arb+is_arab',
...    '#item+definitionem+i_ar+i_arb+is_arab'
... ]

>>> rem.intra_collectionem_est(collectionem)
['#item+rem+i_la+i_lat+is_latn', '#item+definitionem+i_la+i_lat+is_latn']

>>> rem.intra_collectionem_est(collectionem, '#item+rem__linguam__')
['#item+rem+i_la+i_lat+is_latn']
>>> rem.intra_collectionem_est(collectionem,'#status+rem+accuratum__linguam__')
[]

>>> rem_vacuum = HXLTMLinguam('', vacuum=True)
>>> rem_vacuum.intra_collectionem_est(collectionem)
['#item+conceptum+codicem', \
'#item+rem+i_la+i_lat+is_latn', \
'#item+definitionem+i_la+i_lat+is_latn', \
'#item+rem+i_ar+i_arb+is_arab', \
'#item+definitionem+i_ar+i_arb+is_arab']

>>> rem_vacuum.intra_collectionem_est(collectionem, '#item+rem__linguam__')
['#item+rem+i_la+i_lat+is_latn', '#item+rem+i_ar+i_arb+is_arab']

        """
        resultatum = []
        if formatum:
            indaginem = self.h(formatum)
        else:
            indaginem = self.a()

        for rem in collectionem:
            if rem.find(indaginem) > -1:
                resultatum.append(rem)

        return resultatum

    def v(self, _verbosum: bool = None):  # pylint: disable=invalid-name
        """Ego python Dict

        Trivia:
         - valendum, https://en.wiktionary.org/wiki/valeo#Latin
           - Anglicum (English): value (?)
         - verbosum, https://en.wiktionary.org/wiki/verbosus#Latin

        Args:
            _verbosum (bool): Verbosum est? Defallo falsum.

        Returns:
            [Dict]: Python objectīvum
        """
        return self.__dict__


class HXLTMRemCaput(HXLTMLinguam):
    """HXLTMRemCaput HXLTMLinguam et HXLTMDatumCaput metadatum

    TODO: maybe rename to HXLTMDatumCaput

    Args:
        HXLTMLinguam ([HXLTMLinguam]): HXLTMLinguam
    """

    columnam: InitVar[int] = -1
    valendum_meta: InitVar[Dict] = None
    datum_typum: InitVar['str'] = None
    hashtag: InitVar[str] = None
    titulum: InitVar[str] = None

    # @see https://github.com/PyCQA/pylint/issues/3505
    # pylint: disable=super-init-not-called
    # pylint: disable=non-parent-init-called
    # pylint: disable=too-many-arguments
    def __init__(
            self,
            columnam: int = -1,
            columnam_meta: Dict = None,  # HXLTMDatumColumnam.v()
            hashtag: str = '',
            titulum: str = '',
            strictum=False):
        """HXLTMRemCaput initiāle

        Args:
            columnam (int): Numerum columnam
            columnam_meta (HXLTMDatumColumnam): HXLTMDatumColumnam
            hashtag (str): Textum hashtag. Defallo: ''
            titulum (str): Textum titulum. Defallo: ''
            strictum (bool, optional): Strictum est?.
                       Trivia: https://en.wiktionary.org/wiki/strictus#Latin
                       Defallo falsum.
        """

        linguam = HXLTMUtil.linguam_de_hxlhashtag(hashtag) if hashtag else ''
        # _[eng-Latn]
        # While on HXLTMLinguam the user must explicitly force vacuum=False
        # to not tolerate malformated requests, the HXLTMRemCaput
        # have to deal with pretty much anything as header. So we assume
        # empty HXL hashtag means HXLTMLinguam vacuum=True
        # [eng-Latn]_
        vacuum = bool(linguam is None or len(linguam) == 0)

        HXLTMLinguam.__init__(self, linguam, strictum, vacuum)

        self._typum = 'HXLTMRemCaput'  # Used only when output JSON

        self.columnam = columnam
        self.hashtag = hashtag
        self.titulum = titulum
        if columnam_meta is not None:
            self.valendum_meta = columnam_meta.v(False)


class HXLTMTestumAuxilium:
    """HXLTM Testum Auxilium

    _[eng-Latn]
    This class only contains static methods to help test the rest of the huge
    hxltmcli.py file.

    Every time lines start with ">>> python-code-here" this actually is an
    python doctest operation that can be executed with something like

        python3 -m doctest hxlm/core/bin/hxltmcli.py

    So the HXLTMTestumAuxilium contain test helpers.
    [eng-Latn]_

    Trivia:
    - testum, https://en.wiktionary.org/wiki/testum
    - auxilium, https://en.wiktionary.org/wiki/auxilium#Latin
    - disciplīnam manuāle
      - Python doctest
        - https://docs.python.org/3/library/doctest.html
    """

    @staticmethod
    def testum_praefixum(archivum: str = None) -> str:
        """Testum basim

        _[eng-Latn]
        Note: this will try check if the enviroment variable
        HXLTM_TESTUM_BASIM and only fallback to assume the entire
        hdp-toolchain installation (or a fork from
        EticaAI/HXL-Data-Science-file-formats) on local disk.

        Since the hxltmclitm v0.8.2 can be used in standalone more, users
        may want to run tests from other paths (in special if they
        eventually want to propose for the public project)
        [eng-Latn]_

        Trivia:
        - archīvum, https://en.wiktionary.org/wiki/archivum
        - praefīxum, https://en.wiktionary.org/wiki/praefixus#Latin

        Returns:
            str:
                _[eng-Latn]
                Directory containing test files.
                [eng-Latn]_
        """

        # if HDATUM_EXEMPLUM:
        # hxltmtestum = str(Path(
        #     HXLTM_SCRIPT_DIR + '/../../../testum/hxltm').resolve())

        praefixum = os.getenv('HXLTM_TESTUM_BASIM', HXLTM_TESTUM_BASIM_DEFALLO)

        if archivum:
            return praefixum + '/' + archivum

        return praefixum

    @staticmethod
    def datum(
        exemplum_archivum: str = 'hxltm-exemplum-linguam.tm.hxl.csv'
    ) -> List:
        """Crudum HXLTM exemplum datum

        Returns:
            List: Crudum HXLTM exemplum datum
        """
        if not os.path.isfile(exemplum_archivum):
            exemplum_archivum = HXLTMTestumAuxilium.testum_praefixum(
                exemplum_archivum)

        if not os.path.isfile(exemplum_archivum):
            raise RuntimeError(
                'HXLTMTestumAuxilium non-datum [{}]. '
                'Requīsītum: dēfīnītiōnem HXLTM_TESTUM_BASIM. Exemplum:'
                '> HXLTM_TESTUM_BASIM="/home/marcus/testum/" '
                'python3 -m doctest hxltmcli-de-marcus.py'
                ' <'.format(exemplum_archivum))

        hxltm_crudum = []
        with open(exemplum_archivum, 'r') as arch:
            csv_lectorem = csv.reader(arch)
            for rem in csv_lectorem:
                hxltm_crudum.append(rem)
            # hxltm_crudum = arch.read().splitlines()

        # print(hxltm_crudum)
        return hxltm_crudum

    @staticmethod
    def ontologia() -> Dict:
        """HXLTM Ontologia 'cor.hxltm.yml'

        Returns:
            Dict: HXLTM Ontologia
        """
        # print(HXLTMUtil.load_hxltm_options())
        return HXLTMUtil.load_hxltm_options()


class HXLTMTypum:
    """HXLTM Data typum

    _[eng-Latn]
    Recommendation for proposes of new types to HXLTMTypum (if over the years)
    this happens:

    Add yourself to the Author of the individual functions and (even if need
    help for the documentation) add inline documentation about the naming of
    the funcion.

    You can also write non eng-Latn comments.
    [eng-Latn]_

    Author:
        Emerson Rocha <rocha[at]ieee.org>
        David Megginson
            (HXLTMTypum based also on from hxl.datatypes)
    Creation date:
            2018-04-07 hxl.datatypes
                       (@see https://github.com/HXLStandard/libhxl-python
                        /blob/main/hxl/datatypes.py)
            2021-06-12 HXLTMTypum

    Exemplōrum gratiā (et Python doctest, id est, testum automata):

>>> HXLTMTypum.hoc_est_numerum(1234)
True
>>> HXLTMTypum.hoc_est_numerum("1234")
True
>>> HXLTMTypum.collectionem_datum_typum([1])
'numerum'
>>> HXLTMTypum.collectionem_datum_typum([1, "2", "tribus"])
'textum'
>>> HXLTMTypum.collectionem_datum_typum(["", "   ", "	"])
'vacuum'
    """

    @staticmethod
    def datum_typum(rem: Type[Any], _annotationem=None) -> str:
        """Datum typum

        Trivia:
        - datum, https://en.wiktionary.org/wiki/datum#Latin
        - typum, https://en.wiktionary.org/wiki/typus#Latin
        - rem, https://en.wiktionary.org/wiki/res#Latin

        Args:
            rem (Type[Any]): Rem

        Returns:
            str: Textum datum typum
        """
        # TODO: this is a draft

        if HXLTMTypum.hoc_est_numerum(rem):
            return 'numerum'
        if HXLTMTypum.hoc_est_vacuum(rem):
            return 'vacuum'

        return 'textum'

    @staticmethod
    def collectionem_datum_typum(
            colloctionem_rem,  # : List,
            _annotationem=None) -> str:
        """Datum typum

        Trivia:
        - collēctiōnem, https://en.wiktionary.org/wiki/collectio#Latin
        - datum, https://en.wiktionary.org/wiki/datum#Latin
        - typum, https://en.wiktionary.org/wiki/typus#Latin
        - rem, https://en.wiktionary.org/wiki/res#Latin
        - incognitum, https://en.wiktionary.org/wiki/incognitus#Latin

        Args:
            rem (Type[Any]): Rem

        Returns:
            str: Textum datum typum
        """
        # TODO: this is a draft
        resultatum = set()

        try:
            iter(colloctionem_rem)
            # print('iteration will probably work')
        except TypeError:
            return 'incognitum'
            # print('not iterable')
        for rem in colloctionem_rem:
            resultatum.add(HXLTMTypum.datum_typum(rem))
        resultatum = list(resultatum)

        if len(resultatum) == 1:
            return resultatum[0]

        if 'vacuum' in resultatum:
            resultatum.remove('vacuum')
            if len(resultatum) == 1:
                return resultatum[0]

        if 'textum' in resultatum:
            return 'textum'
        return 'incognitum'

    @staticmethod
    def hoc_est_numerum(rem: Type[Any]) -> bool:
        """Hoc est numerum?

        _[eng-Latn]
        hxl.datatypes.is_number()

        By duck typing, test if a value contains something recognisable as
        a number.
        [eng-Latn]_

        Trivia:
          - rem, https://en.wiktionary.org/wiki/res#Latin
          - hoc, https://en.wiktionary.org/wiki/hoc#Latin
          - est, https://en.wiktionary.org/wiki/est#Latin
          - numerum, https://en.wiktionary.org/wiki/numerus#Latin

        Args:
            rem ([Any]): Rem

        Returns:
            [str]: Datum typum de rem
        """
        try:
            float(rem)
            return True
        except ValueError:
            return False

    @staticmethod
    def hoc_est_vacuum(rem: Type[Any]) -> bool:
        """Hoc est numerum?

        _[eng-Latn]
        hxl.datatypes.is_empty()

        None, empty string, or whitespace only counts as empty; anything else
        doesn't.
        [eng-Latn]_

        Trivia:
          - rem, https://en.wiktionary.org/wiki/res#Latin
          - hoc, https://en.wiktionary.org/wiki/hoc#Latin
          - est, https://en.wiktionary.org/wiki/est#Latin
          - vacuum, https://en.wiktionary.org/wiki/vacuus#Latin

        Args:
            rem ([Any]): Rem

        Returns:
            [str]: Datum typum de rem
        """
        # TODO: implement the '∅' that we use for intentionaly mark
        #       a value that is okay to be empty

        return rem is None or rem == '' or str(rem).isspace()

    @staticmethod
    def in_numerum(rem: Union[int, str]) -> Union[int, float]:
        """Trānslātiōnem: rem in numerum

        Trivia:
          - rem, https://en.wiktionary.org/wiki/res#Latin
          - in, https://en.wiktionary.org/wiki/in#Latin
          - numerum, https://en.wiktionary.org/wiki/numerus#Latin

        Args:
            rem ([Any]): Rem

        Returns:
            [int, float]: Rem in numerum
        """
        # _[eng-Latn]
        # TODO: is a draft. We have so many types of numbers that this will
        #       need lots of funcions. In special to convert, for example
        #       I = 1, V = 5, IX = 9, ... and other textum types
        #       (Emerson Rocha, 2021-07-13 04:14 UTC)
        # [eng-Latn]_
        return HXLTMTypum.in_numerum_simplex(rem)

    @staticmethod
    def in_textum_json(
            rem: Any,
            formosum: Union[bool, int] = None,
            clavem_sortem: bool = False,
            imponendum_praejudicium: bool = False
    ) -> str:
        """Trānslātiōnem: rem in textum JSON

        Trivia:
          - rem, https://en.wiktionary.org/wiki/res#Latin
          - in, https://en.wiktionary.org/wiki/in#Latin
          - json, https://www.json.org/
          - fōrmōsum, https://en.wiktionary.org/wiki/formosus
          - impōnendum, https://en.wiktionary.org/wiki/enforcier#Old_French
          - praejūdicium, https://en.wiktionary.org/wiki/praejudicium#Latin
          - sortem, https://en.wiktionary.org/wiki/sors#Latin
          - clāvem, https://en.wiktionary.org/wiki/clavis#Latin

        Args:
            rem ([Any]): Rem

        Returns:
            [str]: Rem in JSON textum

        Exemplōrum gratiā (et Python doctest, id est, testum automata):

>>> rem = {"b": 2, "a": ['ت', 'ツ', '😊']}

>>> HXLTMTypum.in_textum_json(rem)
'{"b": 2, "a": ["ت", "ツ", "😊"]}'

>>> HXLTMTypum.in_textum_json(rem, clavem_sortem=True)
'{"a": ["ت", "ツ", "😊"], "b": 2}'

>>> HXLTMTypum.in_textum_json(rem, imponendum_praejudicium=True)
'{"b": 2, "a": ["\\\u062a", "\\\u30c4", "\\\ud83d\\\ude0a"]}'

>>> HXLTMTypum.in_textum_json(rem, formosum=True)
'{\\n    "b": 2,\\n    \
"a": [\\n        "ت",\\n        "ツ",\\n        "😊"\\n    ]\\n}'

        """

        # print = json.dumps()

        if formosum is True:
            formosum = 4

        json_textum = json.dumps(
            rem,
            indent=formosum,
            sort_keys=clavem_sortem,
            ensure_ascii=imponendum_praejudicium
        )

        return json_textum

    @staticmethod
    def in_textum_yaml(
            rem: Any,
            formosum: Union[bool, int] = None,
            clavem_sortem: bool = False,
            imponendum_praejudicium: bool = False
    ) -> str:
        """Trānslātiōnem: rem in textum YAML

        Trivia:
          - rem, https://en.wiktionary.org/wiki/res#Latin
          - in, https://en.wiktionary.org/wiki/in#Latin
          - YAML, https://yaml.org/
          - fōrmōsum, https://en.wiktionary.org/wiki/formosus
          - impōnendum, https://en.wiktionary.org/wiki/enforcier#Old_French
          - praejūdicium, https://en.wiktionary.org/wiki/praejudicium#Latin
          - sortem, https://en.wiktionary.org/wiki/sors#Latin
          - clāvem, https://en.wiktionary.org/wiki/clavis#Latin

        Args:
            rem ([Any]): Rem

        Returns:
            [str]: Rem in JSON textum

        Exemplōrum gratiā (et Python doctest, id est, testum automata):

>>> rem = {"b": 2, "a": ['ت', 'ツ', '😊']}

>>> HXLTMTypum.in_textum_json(rem)
'{"b": 2, "a": ["ت", "ツ", "😊"]}'

>>> HXLTMTypum.in_textum_json(rem, clavem_sortem=True)
'{"a": ["ت", "ツ", "😊"], "b": 2}'

>>> HXLTMTypum.in_textum_json(rem, imponendum_praejudicium=True)
'{"b": 2, "a": ["\\\u062a", "\\\u30c4", "\\\ud83d\\\ude0a"]}'

>>> HXLTMTypum.in_textum_json(rem, formosum=True)
'{\\n    "b": 2,\\n    \
"a": [\\n        "ت",\\n        "ツ",\\n        "😊"\\n    ]\\n}'

        """

        # TODO: in_textum_yaml is a draft.

        # print = json.dumps()

        if formosum is True:
            formosum = 4

        yaml_textum = yaml.dump(
            rem, Dumper=HXLTMTypumYamlDumper,
            encoding='utf-8',
            allow_unicode=not imponendum_praejudicium
        )

        # json_textum = json.dump(
        #     rem,
        #     indent=formosum,
        #     sort_keys=clavem_sortem,
        #     ensure_ascii=imponendum_praejudicium
        # )

        # return yaml_textum
        # @see https://pyyaml.org/wiki/PyYAMLDocumentation
        return str(yaml_textum, 'UTF-8')

    # @staticmethod
    # @see also hxlm/core/io/converter.py
    # def to_yaml(thing: Any) -> str:
    #     """Generic YAML exporter

    #     Returns:
    #         str: Returns an YAML formated string
    #     """

    #     return yaml.dump(thing, Dumper=HXLTMTypumYamlDumper,
    #                     encoding='utf-8', allow_unicode=True)

    @staticmethod
    def in_numerum_simplex(rem: Union[int, str]) -> int:
        """Rem in numerum simplex?

        _[eng-Latn]
        See also hxl.datatypes.normalise_number()

        Attempt to convert a value to a number.

        Will convert to int type if it has no decimal places.
        [eng-Latn]_

        Author:
            David Megginson

        Trivia:
          - rem, https://en.wiktionary.org/wiki/res#Latin
          - in, https://en.wiktionary.org/wiki/in#Latin
          - numerum, https://en.wiktionary.org/wiki/numerus#Latin
          - simplex, https://en.wiktionary.org/wiki/simplex#Latin
          - disciplīnam manuāle
            - https://en.wikipedia.org/wiki/IEEE_754

        Args:
            rem ([Any]): Rem

        Returns:
            [Union[int, float]]: Rem in numerum IEEE integer aut IEEE 754

        Exemplōrum gratiā (et Python doctest, id est, testum automata):

            >>> HXLTMTypum.in_numerum_simplex('1234')
            1234
            >>> HXLTMTypum.in_numerum_simplex('1234.0')
            1234
        """
        # pylint: disable=invalid-name,no-else-return

        try:
            n = float(rem)
            if n == int(n):
                return int(n)
            else:
                return n
        except Exception as expt:
            raise ValueError(
                "Non numerum trānslātiōnem: {}".format(rem)) from expt

    @staticmethod
    def magnitudinem_de_byte(rem: str) -> int:
        """Magnitūdinem dē byte

        Trivia:
          - rem, https://en.wiktionary.org/wiki/res#Latin
          - magnitūdinem, https://en.wiktionary.org/wiki/est#Latin
          - dē, https://en.wiktionary.org/wiki/de#Latin
          - byte
            - https://en.wiktionary.org/wiki/byte#English
            - https://en.wikipedia.org/wiki/Byte

        Args:
            rem (str): Rem textum

        Returns:
            int: Numerum

        Exemplōrum gratiā (et Python doctest, id est, testum automata):

            >>> HXLTMTypum.magnitudinem_de_byte('Testīs')
            7
        """
        if rem is None:
            return -1

        # @see https://stackoverflow.com/questions/30686701
        #      /python-get-size-of-string-in-bytes
        # TODO: This is a draft. Needs work.
        return len(rem.encode('utf-8'))

    @staticmethod
    def magnitudinem_de_numerum(rem: str) -> int:
        """Magnitūdinem dē numerum

        Trivia:
          - rem, https://en.wiktionary.org/wiki/res#Latin
          - magnitūdinem, https://en.wiktionary.org/wiki/est#Latin
          - dē, https://en.wiktionary.org/wiki/de#Latin
          - numerum, https://en.wiktionary.org/wiki/numerus#Latin

        Args:
            rem (str): Rem textum

        Returns:
            int: Numerum
        """
        print('TODO')

    @staticmethod
    def magnitudinem_de_textum(rem: str) -> int:
        """magnitūdinem dē textum

        Trivia:
          - rem, https://en.wiktionary.org/wiki/res#Latin
          - magnitūdinem, https://en.wiktionary.org/wiki/est#Latin
          - dē, https://en.wiktionary.org/wiki/de#Latin
          - textum, https://en.wiktionary.org/wiki/textus#Latin

        Args:
            rem (str): Rem textum

        Returns:
            int: Numerum

        Exemplōrum gratiā (et Python doctest, id est, testum automata):

            >>> HXLTMTypum.magnitudinem_de_textum('Testīs')
            6
        """
        if rem is None:
            return -1

        # TODO: This is a draft. Needs work.
        return len(rem)


class HXLTMTypumYamlDumper(yaml.Dumper):
    """Force identation on pylint, https://github.com/yaml/pyyaml/issues/234
    TODO: check on future if this still need
          (Emerson Rocha, 2021-02-28 10:56 UTC)
    """

    def increase_indent(self, flow=False, *args, **kwargs):  # noqa
        return super().increase_indent(flow=flow, indentless=False)


class HXLTMUtil:
    """HXL Trānslātiōnem Memoriam auxilium programmi

    Author:
            Emerson Rocha <rocha[at]ieee.org>
    Creation date:
            2021-06-09
    """

    @staticmethod
    def bcp47_from_hxlattrs(hashtag: Union[str, None]) -> str:
        """From a typical HXLTM hashtag, return only the bcp47 language code
        without require a complex table equivalence.

        Example:
            >>> HXLTMUtil.bcp47_from_hxlattrs('#item+i_ar+i_arb+is_arab')
            'ar'
            >>> HXLTMUtil.bcp47_from_hxlattrs('#item+i_arb+is_arab')
            ''

        Args:
            linguam ([String]): A linguam code

        Returns:
            [String]: HXL Attributes
        """
        if hashtag and isinstance(hashtag, str):
            parts = hashtag.lower().split('+i_')
            for k in parts:
                if len(k) == 2:
                    return k

        return ''

    @staticmethod
    def bcp47_from_linguam(linguam: Union[str, None]) -> str:
        """From am linguam with hint about BCP47, get the BCP47 code
        Returns empty if no hint exist

        Example:
            >>> HXLTMUtil.bcp47_from_hxlattrs('por-Latn')
            ''
            >>> HXLTMUtil.bcp47_from_linguam('por-Latn@pt')
            'pt'
            >>> HXLTMUtil.bcp47_from_linguam('por-Latn@pt-BR')
            'pt-BR'

        Args:
            linguam ([String]): A linguam code

        Returns:
            [String]: HXL Attributes
        """
        if linguam.find('@') > -1:
            _linguam, bcp47 = list(linguam.split('@'))
            return bcp47

        return ''

    @staticmethod
    def hxllangattrs_list_from_item(item):
        """hxllangattrs_list_from_item get only the raw attr string part
        that is repeated severa times and mean the same logical group.

        Example:
            >>> item = {'#item+i_pt+i_por+is_latn':
            ...          '','#item+i_pt+i_por+is_latn+alt+list': '',
            ...           '#meta+item+i_pt+i_por+is_latn': ''}
            >>> HXLTMUtil.hxllangattrs_list_from_item(item)
            {'+i_pt+i_por+is_latn'}

        Args:
            item ([Dict]): An dict item
        Returns:
            [Set]: Set of unique HXL language attributes
        """
        result = set()

        for k in item:
            rawstr = ''
            bcp47 = HXLTMUtil.bcp47_from_hxlattrs(k)
            iso6393 = HXLTMUtil.iso6393_from_hxlattrs(k)
            iso115924 = HXLTMUtil.iso115924_from_hxlattrs(k)
            if bcp47:
                rawstr += '+i_' + bcp47
            if iso6393:
                rawstr += '+i_' + iso6393
            if iso115924:
                rawstr += '+is_' + iso115924
            # print('   ', k, '   ', rawstr)
            result.add(rawstr)
        return result

    @staticmethod
    def iso6393_from_hxlattrs(hashtag: Union[str, None]) -> str:
        """From a typical HXLTM hashtag, return only the ISO 639-3 language
        code without require a complex table equivalence.

        Example:
>>> HXLTMUtil.iso6393_from_hxlattrs('#item+i_ar+i_arb+is_arab')
'arb'
>>> HXLTMUtil.iso6393_from_hxlattrs('#item+i_ar')
''
>>> HXLTMUtil.iso6393_from_hxlattrs('#item+i_pt+i_por+is_latn+alt+list')
'por'

        Args:
            hashtag ([String]): A hashtag string

        Returns:
            [String]: HXL Attributes
        """
        if hashtag and isinstance(hashtag, str):
            # parts = hashtag.lower().split('+i_')
            parts = hashtag.lower().split('+')
            # '#item+i_ar+i_arb+is_arab' => ['#item', 'ar', 'arb+is_arab']
            # print(parts)
            for k in parts:
                # if len(k) == 5 and k.find('+i_') == 0:
                if len(k) == 5 and k.startswith('i_'):
                    # print(k.find('i_'))
                    return k.replace('i_', '')

        return ''

    @staticmethod
    def iso115924_from_hxlattrs(hashtag: Union[str, None]) -> str:
        """From a typical HXLTM hashtag, return only the ISO 115924
        writting system without require a complex table equivalence.

        Example:
            >>> HXLTMUtil.iso115924_from_hxlattrs('#item+i_ar+i_arb+is_arab')
            'arab'
            >>> HXLTMUtil.iso115924_from_hxlattrs('#item+i_ar')
            ''

        Args:
            hashtag ([String]): A linguam code

        Returns:
            [String]: HXL Attributes
        """
        if hashtag and isinstance(hashtag, str):
            parts = hashtag.lower().split('+')
            for k in parts:
                if k.startswith('is_'):
                    return k.replace('is_', '')

        return ''

    @staticmethod
    def linguam_2_hxlattrs(linguam):
        """linguam_2_hxlattrs

        Example:
            >>> HXLTMUtil.linguam_2_hxlattrs('por-Latn')
            '+i_por+is_latn'
            >>> HXLTMUtil.linguam_2_hxlattrs('por-Latn@pt')
            '+i_pt+i_por+is_latn'
            >>> HXLTMUtil.linguam_2_hxlattrs('por-Latn@pt-BR')
            '+i_pt+i_por+is_latn'
            >>> HXLTMUtil.linguam_2_hxlattrs('arb-Arab')
            '+i_arb+is_arab'

        Args:
            linguam ([String]): A linguam code

        Returns:
            [String]: HXL Attributes
        """
        if linguam.find('@') == -1:
            iso6393, iso115924 = list(linguam.lower().split('-'))
            return '+i_' + iso6393 + '+is_' + iso115924

        linguam, bcp47 = list(linguam.lower().split('@'))
        iso6393, iso115924 = list(linguam.split('-'))

        if bcp47.find('-') == -1:
            return '+i_' + bcp47 + '+i_' + iso6393 + '+is_' + iso115924

        # TODO: decide how to express country with hashtags
        iso6391, _adm = list(bcp47.split('-'))

        return '+i_' + iso6391 + '+i_' + iso6393 + '+is_' + iso115924

    @staticmethod
    def linguam_de_hxlhashtag(
            hxl_hashtag: str,
            non_obsoletum: bool = False,
            non_patriam: bool = False,
            non_privatum: bool = False) -> Union[str, None]:
        """Linguam de HXL hashtag

        Args:
            linguam ([str]): _[eng-Latn] An HXL hashtag [eng-Latn]_
            non_obsoletum ([bool]): Non bcp47?
            non_patriam ([bool]): Non patriam codicem??
            non_privatum ([bool]): Non privatum codicem?

        Returns:
            [Union[str, None]]: Linguam codicem aut python None

        Example:
            >>> HXLTMUtil.linguam_de_hxlhashtag(
            ...    '#meta+item+i_la+i_lat+is_latn')
            'lat-latn@la'
        """
        rawstr = ''
        bcp47 = HXLTMUtil.bcp47_from_hxlattrs(hxl_hashtag)
        iso6393 = HXLTMUtil.iso6393_from_hxlattrs(hxl_hashtag)
        iso115924 = HXLTMUtil.iso115924_from_hxlattrs(hxl_hashtag)

        if non_patriam:
            # TODO: implement +ii_ (region with political influence attribute)
            raise NotImplementedError('non_patriam')
        if non_privatum:
            # TODO: implement +ix_ (private attributes)
            raise NotImplementedError('non_privatum')

        if iso6393:
            rawstr += iso6393
        if iso115924:
            rawstr += '-' + iso115924
        if bcp47 and not non_obsoletum:
            rawstr += '@' + bcp47

        return rawstr if rawstr else None

    @staticmethod
    def load_hxltm_options(custom_file_option=None, is_debug=False):
        """Load options from cor.hxltm.yml

        Args:
            custom_file_option ([str], optional): Custom options.
                    Defaults to None.
            is_debug (bool, optional): Is debug enabled? Defaults to False.

        Returns:
            [Dict]: Dictionary of cor.hxltm.yml contents
        """
        # pylint: disable=using-constant-test
        if is_debug:
            print('load_hxltm_options')
            print('HXLM_CONFIG_BASE', HXLM_CONFIG_BASE)
            print('HXLTM_SCRIPT_DIR', HXLTM_SCRIPT_DIR)
            print('HXLTM_RUNNING_DIR', HXLTM_RUNNING_DIR)

        if custom_file_option is not None:
            if Path(custom_file_option).exists():
                return HXLTMUtil._load_hxltm_options_file(
                    custom_file_option, is_debug)
            raise RuntimeError("Configuration file not found [" +
                               custom_file_option + "]")

        if Path(HXLTM_RUNNING_DIR + '/cor.hxltm.yml').exists():
            return HXLTMUtil._load_hxltm_options_file(
                HXLTM_RUNNING_DIR + '/cor.hxltm.yml', is_debug)

        if Path(HXLM_CONFIG_BASE + '/cor.hxltm.yml').exists():
            return HXLTMUtil._load_hxltm_options_file(
                HXLM_CONFIG_BASE + '/cor.hxltm.yml', is_debug)

        if Path(HXLTM_SCRIPT_DIR + '/cor.hxltm.yml').exists():
            return HXLTMUtil._load_hxltm_options_file(
                HXLTM_SCRIPT_DIR + '/cor.hxltm.yml', is_debug)
        # print('oioioi')

        raise RuntimeError(
            "ERROR: no cor.hxltm.yml found (not even default one).")

    @staticmethod
    def _load_hxltm_options_file(file, is_debug=False):
        if is_debug:
            print('_load_hxltm_options_file: [' + file + ']')

        with open(file, "r") as read_file:
            data = yaml.safe_load(read_file)
            return data

    @staticmethod
    def xliff_item_relevant_options(item):
        """From an dict (python object) return only keys that start with
        # x_xliff

        Args:
            item ([Dict]): An non-filtered dict (python object) represent a row

        Returns:
            [Dict]: A filtered object. ∅ is replaced by python None
        """
        item_neo = {}

        for k in item:
            if k.startswith('#x_xliff'):
                if item[k] == '∅':
                    item_neo[k] = None
                else:
                    item_neo[k] = item[k]

        return item_neo

    @staticmethod
    def tmx_item_relevan_options(item):
        return item
        # item_neo = {}

        # for k in item:
        #     if k.startswith('#x_xliff'):
        #         if item[k] == '∅':
        #             item_neo[k] = None
        #         else:
        #             item_neo[k] = item[k]

        # return item_neo

    @staticmethod
    def xliff_item_xliff_source_key(item):
        for k in item:
            if k.startswith('#x_xliff+source'):
                return k

        return None

    @staticmethod
    def xliff_item_xliff_target_key(item):
        for k in item:
            if k.startswith('#x_xliff+target'):
                return k

        return None


class HXLUtils:
    """
    HXLUtils contains functions from the Console scripts of libhxl-python
    (HXLStandard/libhxl-python/blob/master/hxl/scripts.py) with few changes
    to be used as class (and have one single place to change).
    Last update on this class was 2021-01-25.

    Author: David Megginson
    License: Public Domain
    """

    def __init__(self):

        self.logger = logging.getLogger(__name__)

        # Posix exit codes
        self.EXIT_OK = 0
        self.EXIT_ERROR = 1
        self.EXIT_SYNTAX = 2

    # def make_args(self, description, hxl_output=True):
    def make_args(self, description, epilog=None, hxl_output=True):
        """Set up parser with default arguments.

        NOTE:
            2021-07-14: Change from libhxl make_args: added epilog option

        @param description: usage description to show
        @param hxl_output: if True (default), include options for HXL output.
        @returns: an argument parser, partly set up.
        """
        if epilog is None:
            parser = argparse.ArgumentParser(description=description)
        else:
            parser = argparse.ArgumentParser(
                description=description,
                formatter_class=argparse.RawDescriptionHelpFormatter,
                epilog=epilog
            )

        parser.add_argument(
            'infile',
            help='HXL file to read (if omitted, use standard input).',
            nargs='?'
        )
        if hxl_output:
            parser.add_argument(
                'outfile',
                help='HXL file to write (if omitted, use standard output).',
                nargs='?'
            )
        parser.add_argument(
            '--sheet',
            help='Select sheet from a workbook (1 is first sheet)',
            metavar='number',
            type=int,
            nargs='?'
        )
        parser.add_argument(
            '--selector',
            help='JSONPath expression for starting point in JSON input',
            metavar='path',
            nargs='?'
        )
        parser.add_argument(
            '--http-header',
            help='Custom HTTP header to send with request',
            metavar='header',
            action='append'
        )
        if hxl_output:
            parser.add_argument(
                '--remove-headers',
                help='Strip text headers from the CSV output',
                action='store_const',
                const=True,
                default=False
            )
            parser.add_argument(
                '--strip-tags',
                help='Strip HXL tags from the CSV output',
                action='store_const',
                const=True,
                default=False
            )
        parser.add_argument(
            "--ignore-certs",
            help="Don't verify SSL connections (useful for self-signed)",
            action='store_const',
            const=True,
            default=False
        )
        parser.add_argument(
            '--log',
            help='Set minimum logging level',
            metavar='debug|info|warning|error|critical|none',
            choices=['debug', 'info', 'warning', 'error', 'critical'],
            default='error'
        )
        return parser

    def add_queries_arg(
        self,
        parser,
        help='Apply only to rows matching at least one query.'
    ):
        parser.add_argument(
            '-q',
            '--query',
            help=help,
            metavar='<tagspec><op><value>',
            action='append'
        )
        return parser

    def do_common_args(self, args):
        """Process standard args"""
        logging.basicConfig(
            format='%(levelname)s (%(name)s): %(message)s',
            level=args.log.upper())

    def make_source(self, args, stdin=STDIN):
        """Create a HXL input source."""

        # construct the input object
        input = self.make_input(args, stdin)
        return hxl.io.data(input)

    def make_input(self, args, stdin=sys.stdin, url_or_filename=None):
        """Create an input object"""

        if url_or_filename is None:
            url_or_filename = args.infile

        # sheet index
        sheet_index = args.sheet
        if sheet_index is not None:
            sheet_index -= 1

        # JSONPath selector
        selector = args.selector

        http_headers = self.make_headers(args)

        return hxl.io.make_input(
            url_or_filename or stdin,
            sheet_index=sheet_index,
            selector=selector,
            allow_local=True,  # TODO: consider change this for execute_web
            http_headers=http_headers,
            verify_ssl=(not args.ignore_certs)
        )

    def make_output(self, args, stdout=sys.stdout):
        """Create an output stream."""
        if args.outfile:
            return FileOutput(args.outfile)
        else:
            return StreamOutput(stdout)

    def make_headers(self, args):
        # get custom headers
        header_strings = []
        header = os.environ.get("HXL_HTTP_HEADER")
        if header is not None:
            header_strings.append(header)
        if args.http_header is not None:
            header_strings += args.http_header
        http_headers = {}
        for header in header_strings:
            parts = header.partition(':')
            http_headers[parts[0].strip()] = parts[2].strip()
        return http_headers


class FileOutput(object):
    """
    FileOutput contains is based on libhxl-python with no changes..
    Last update on this class was 2021-01-25.

    Author: David Megginson
    License: Public Domain
    """

    def __init__(self, filename):
        self.output = open(filename, 'w')

    def __enter__(self):
        return self

    def __exit__(self, value, type, traceback):
        self.output.close()


class StreamOutput(object):
    """
    StreamOutput contains is based on libhxl-python with no changes..
    Last update on this class was 2021-01-25.

    Author: David Megginson
    License: Public Domain
    """

    def __init__(self, output):
        self.output = output

    def __enter__(self):
        return self

    def __exit__(self, value, type, traceback):
        pass

    def write(self, s):
        self.output.write(s)


if __name__ == "__main__":

    hxltmcli = HXLTMCLI()
    args = hxltmcli.make_args_hxltmcli()

    hxltmcli.execute_cli(args)


def exec_from_console_scripts():
    hxltmcli_ = HXLTMCLI()
    args_ = hxltmcli_.make_args_hxltmcli()

    hxltmcli_.execute_cli(args_)
