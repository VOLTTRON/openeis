"""
Copy files directly, i.e., without looking at contents.

Copyright (c) 2014, The Regents of the University of California, Department
of Energy contract-operators of the Lawrence Berkeley National Laboratory.
All rights reserved.

1. Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are met:

   (a) Redistributions of source code must retain the copyright notice, this
   list of conditions and the following disclaimer.

   (b) Redistributions in binary form must reproduce the copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

   (c) Neither the name of the University of California, Lawrence Berkeley
   National Laboratory, U.S. Dept. of Energy nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

2. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
   ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
   LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
   ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
   THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

3. You are under no obligation whatsoever to provide any bug fixes, patches,
   or upgrades to the features, functionality or performance of the source code
   ("Enhancements") to anyone; however, if you choose to make your Enhancements
   available either publicly, or directly to Lawrence Berkeley National
   Laboratory, without imposing a separate written license agreement for such
   Enhancements, then you hereby grant the following license: a non-exclusive,
   royalty-free perpetual license to install, use, modify, prepare derivative
   works, incorporate into other computer software, distribute, and sublicense
   such enhancements or derivative works thereof, in binary and source code
   form.

NOTE: This license corresponds to the "revised BSD" or "3-clause BSD" license
and includes the following modification: Paragraph 3. has been added.
"""


#--- Provide access.
#
import os
import shutil


def ensureDir(dirName):
    """
    Create a directory if necessary.

    **Args:**

    - *dirName*, path to directory.

    **Returns:**

    - ``True`` if created directory.
    - ``False`` if directory already exists.

    **Raises:**

    - If *dirName* cannot be created.
    - If *dirName* names an existing file.

    **Notes:**

    - *dirName* can give an absolute or relative path.
    - *srcFileName* can name intermediate directories.  For example, creating "mid/final"
      creates directory "mid" if necessary.
    """
    #
    if( os.path.isdir(dirName) ):
        return( False )
    #
    # Here, need to create directory.
    #   Note if *dirName* names an existing file, this will raise an exception.
    os.makedirs(dirName)
    #
    return( True )
    #
    # End :func:`ensureDir`.


def copyFile(srcFileName, destName):
    """
    Copy a file.

    **Args:**

    - *srcFileName*, name of file to copy.
    - *destName*, name of copy.  May be a path, in which case *srcFileName*
      gets copied to the given directory.

    **Returns:**

    - ``True`` if copied file successfully.
    - ``False`` if encounter a textual mistake, e.g., if *srcFileName* does not
      name a file, or if *destName* gives the same file as *srcFileName*.

    **Raises:**

    - If *srcFileName* cannot be copied to *destName*, e.g., because of a
      permissions error.

    **Notes:**

    - File *destName*, if it already exists, will be overwritten.
    - Both *srcFileName* and *destName* may include path information.
    """
    #
    if( (not os.path.isfile(srcFileName))
        or
        (os.path.abspath(srcFileName)==os.path.abspath(destName)) ):
        return( False )
    #
    destDirName = os.path.dirname(destName)
    if( len(destDirName) > 0 ):
        ensureDir(destDirName)
    #
    shutil.copy(srcFileName, destName)
    #
    return( True )
    #
    # End :func:`copyFile`.


def copyAllFiles(srcDirName, destDirName):
    """
    Copy all files in one directory to another.

    **Args:**

    - *srcDirName*, name of directory from which to copy files.
    - *destDirName*, name of receiving directory.

    **Returns:**

    - ``True`` if copied files successfully.
    - ``False`` if encounter a textual mistake, e.g., if *srcDirName* does not
      name a directory, or if *destDirName* gives the same directory as *srcDirName*.

    **Raises:**

    - For external error, e.g., a permissions error.

    **Notes:**

    - Any existing file in *destDirName* will be overwritten by a file with
      the same name in *srcDirName*.
    - Copy only files-- do not descend into subdirectories of *srcDirName*.
    """
    #
    if( (not os.path.isdir(srcDirName))
        or
        (os.path.abspath(srcDirName)==os.path.abspath(destDirName))
        or
        (os.path.isfile(destDirName)) ):
        return( False )
    #
    ensureDir(destDirName)
    #
    for baseName in os.listdir(srcDirName):
        srcFileName = os.path.join(srcDirName, baseName)
        if( os.path.isfile(srcFileName) ):
            destFileName = os.path.join(destDirName, baseName)
            shutil.copy(srcFileName, destFileName)
    #
    return( True )
    #
    # End :func:`copyAllFiles`.
