#!/usr/bin/gawk -f
# -*- tab-width: 4; indent-tabs-mode: t -*-
#
# This file is part of the LibreOffice project.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#

# Create dependency information from the output of cl.exe's showInclude.  It
# needs additional information - the output name to which to write, objfile
# that depends on the includes, and the original file name.
# For best results all arguments should be absolute paths.
#
# It also consolidates the file names to a canonical form, and filters out
# duplicates.
#
# based on filter-showInclude.pl by Jan Holesovsky <kendy@suse.cz>

BEGIN {
    if (!depfile || !objectfile || !sourcefile) {
        print "usage: filter-showIncludes.awk -vdepfile=depfile.d " \
          "-vobjectfile=objfile.o -vsourcefile=source.cxx" > "/dev/stderr"
        exit 1
    }
    tempfile = depfile ".tmp"
    print objectfile " : \\\n " sourcefile " \\" > tempfile

    showincludes_prefix = ENVIRON["SHOWINCLUDES_PREFIX"];
    if (!showincludes_prefix) {
        showincludes_prefix = "Note: including file:"
    }

    # Only headers below these directories are dependencies; everything else
    # (compiler and SDK headers) is filtered out.  WORKDIR holds generated
    # headers (UNO API headers, SDI output, custom targets); it is listed on
    # its own because it is not necessarily spelled as a subdirectory of
    # BUILDDIR (configure may give SRCDIR/BUILDDIR as 8.3 short paths but
    # WORKDIR as a long path).
    ndirs = 0
    split("WORKDIR SRCDIR BUILDDIR", dirvars)
    for (i = 1; i in dirvars; i++) {
        dir = ENVIRON[dirvars[i]]
        gsub(/\\/, "/", dir)
        sub(/\/+$/, "", dir)
        add_dir(dir, dir)
        dirvals[i] = dir
    }
    # cl.exe reports a header that it finds next to the including file (a
    # quoted #include) with the long form of an 8.3 short directory name, so
    # accept the long forms of SRCDIR and BUILDDIR too.
    for (i = 2; i in dirvars; i++) { # dirvars[1] is WORKDIR
        dir = dirvals[i]
        if (index(dir, "~") && !(dir in longdone)) {
            longdone[dir]
            cmd = "cygpath -m -l '" dir "' 2>/dev/null"
            if ((cmd | getline longdir) > 0) {
                sub(/\/+$/, "", longdir)
                if (longdir != dir) {
                    add_dir(longdir, dir)
                }
            }
            close(cmd)
        }
    }
    firstline = 1
}

# Record that headers below directory dir (compared case insensitively,
# because of drive letters) are written below spelling instead.
function add_dir(dir, spelling) {
    if (dir != "") {
        dirs[++ndirs] = dir
        spellings[ndirs] = spelling
    }
}

# If path is below one of dirs, return it with that prefix spelled as in the
# variable, so that it is the same string as gbuild's target for a generated
# header; otherwise return "".
function canonical_path(path,    i, len) {
    for (i = 1; i <= ndirs; i++) {
        len = length(dirs[i])
        if (tolower(substr(path, 1, len)) == tolower(dirs[i]) \
            && substr(path, len + 1, 1) == "/") {
            return spellings[i] substr(path, len + 1)
        }
    }
    return ""
}

{
    sub(/\r$/, "")
    sub(/^ */, "")
    if (index($0, showincludes_prefix) == 1) {
        $0 = substr($0, length(showincludes_prefix) + 1)
        sub(/^ */, "")
        gsub(/\\/, "/")
        $0 = canonical_path($0)
        if ($0 != "") { # filter out system headers
            gsub(/ /, "\\ ")
            if (!($0 in incfiles)) {
                incfiles[$0]
                print " " $0 " \\" > tempfile
            }
        }
    } else {
        # because MSVC stupidly prints errors on stdout, it's
        # necessary to forward everything that isn't matched by the pattern
        # so users get to see them.
        if (firstline) { # ignore the line that just prints name of sourcefile
            firstline = 0
        } else {
            print $0 > "/dev/stderr"
        }
    }
}

END {
    if (!tempfile) {
        exit 1
    }
    print "" > tempfile

    # fdo#40099 if header.h does not exist, it will simply be considered out of
    # date and any targets that use it as a prerequisite will be updated,
    # which avoid misery when the header is deliberately deleted and removed
    # as an include
    # see http://www.makelinux.net/make3/make3-CHP-8-SECT-3
    for (file in incfiles) {
        print file " :\n" > tempfile
    }

    close(tempfile)
    movecmd = "mv " tempfile " " depfile
    ret = system(movecmd)
    if (ret) {
        print "ERROR: " movecmd " FAILED with status " ret > "/dev/stderr"
        exit ret
    }
}

# vim: set noet sw=4 ts=4:
