
import os
import sys
import logging
import platform

import django



IDSTR = """
PLATFORM

    platform.architecture           %s;
    platform.dist                   %s;
    platform.java_ver               %s;
    platform.libc_ver               %s;
    platform.linux_distribution     %s;
    platform.mac_ver                %s;
    platform.machine                %s;
    platform.node                   %s;
    platform.os                     %s;
    platform.platform               %s;
    platform.popen                  %s;
    platform.processor              %s;
    platform.python_branch          %s;
    platform.python_build           %s;
    platform.python_compiler        %s;
    platform.python_implementation  %s;
    platform.python_revision        %s;
    platform.python_version         %s;
    platform.python_version_tuple   %s;
    platform.re                     %s;
    platform.release                %s;
    platform.sys                    %s;
    platform.system                 %s;
    platform.system_alias           %s;
    platform.uname                  %s;
    platform.version                %s;
    platform.win32_ver              %s;

DJANGO
    django.version                  %s;
"""%(
        platform.architecture(),
        platform.dist(),
        platform.java_ver(),
        platform.libc_ver(),
        platform.linux_distribution(),
        platform.mac_ver(),
        platform.machine(),
        platform.node(),
        platform.os,
        platform.platform(),
        platform.popen,
        platform.processor(),
        platform.python_branch(),
        platform.python_build(),
        platform.python_compiler(),
        platform.python_implementation(),
        platform.python_revision(),
        platform.python_version(),
        platform.python_version_tuple(),
        platform.re,
        platform.release(),
        platform.sys,
        platform.system(),
        platform.system_alias,
        platform.uname(),
        platform.version(),
        platform.win32_ver(),
        django.get_version()
    )

if not ('LOGSTART' in globals()):
    logger = logging.getLogger(__name__)
    logging.critical(IDSTR)
    LOGSTART = True
