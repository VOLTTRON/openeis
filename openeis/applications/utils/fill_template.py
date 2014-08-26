"""
Fill in a template file with user-supplied replacements.

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
import re
import shutil


#--- Pattern to identify a replacement key as {:non-spaces:}.
#
#   For use as a *pattern* argument to a template-filling fcn.
#
#   Break up a string into groups, identifying non-space characters between
# "{:" and ":}" as a replacement key.
#   Examples:
# ** "pre{:replace-me:}post" ==> "pre", "{:replace-me:}", and "post".
# ** "{:replace-me:}post" ==> "", "{:replace-me:}", and "post".
# ** "pre {:replace-me:} post" ==> "pre ", "{:replace-me:}", and " post".
# ** "pre{:replace-me:}post{:rr:}pp" ==> "pre", "{:replace-me:}", and "post{:rr:}pp".
# ** "pre{:replace-me:}{:rr:}pp" ==> "pre", "{:replace-me:}", and "{:rr:}pp".
# ** "pre{:replace me:}post" ==> no match (space inside braces).
# ** "pre{:replace-me}post" ==> no match (missing closing colon).
#
#   Implementation note - breakdown of the regular expression:
#
# ** (.*?), non-greedy match of zero or more of anything.  In a group (i.e., in
# parentheses) because need to access the contents.  Has to be non-greedy,
# to allow detecting multiple replacement keys in a single string.
#
# ** ({:\S+?:}), non-greedy match of a '{:' followed by non-space characters,
# followed by ':}'.  This pattern picks up a replacement key.  Has to be
# non-greedy, to allow detecting multiple replacement keys in a single string.
#
# ** (.*), pick up rest of line.  In a group because need to access the rest
# of the line, in order to search for further replacement keys.
#
PATTERN_BRACE_COLON = re.compile(r'(.*?)({:\S+?:})(.*)')

# TODO:  Test whether Sphinx can pick up a docstring for a global constant like *PATTERN_BRACE_COLON*.


#--- Convenience regex.
#
#   For internal use.
#
__REX_LINE_ENDINGS = re.compile(r'(.*)([\r\n]+)')


def fillTemplate_strKey(templateFile,
    pattern, replacements,
    outFile):
    """
    Stream through a template file, replacing substrings that match a pattern.

    **Args:**

    - *templateFile*, an open file-like object whose contents are to be modified.
    - *pattern*, a regular expression object that identifies a "replacement key"
      of characters to replace.
    - *replacements*, dictionary that maps each replacement key to its
      replacement value.
    - *outFile*, an open file-like object to receive the results.

    **Returns:**

    - Either ``None``, or a dictionary *unmatched*.
    - ``None`` indicates all matched substrings in *templateFile* had a
      corresponding entry in *replacements*.  This is roughly the equivalent
      of "success".
    - If a dictionary, the keywords are substrings that match *pattern*, but
      that do not appear in *replacements*.  The keywords map to an integer
      giving the line number, in *templateFile*, of the first occurence of the
      unmatched substring.

    **Notes:**

    - *pattern* is a compiled regular expression that separates a string into
      three groups: (1) the characters before a replacement key; (2) the
      characters of the replacement key; and (3) the characters after the
      replacement key.  The last group should include any other replacement keys
      that appear on the same line.  See for example *PATTERN_BRACE_COLON*.
    - The keys in *replacements* should be strings.
    - The values in *replacements* do not have to be strings.  Before substitution,
      :func:`str` is called on the.  For example, replacments['{:area:}'] = 10000
      is OK.
    - It is OK for a replacement key in *templateFile* to not have a match in
      *replacements*.  Any un-matched replacement key is simply written, unaltered,
      to *outFile*.
    - It is OK to have an unused key in *replacements* (i.e., a key that does not
      appear in the template file).
    - It is possible to make *pattern* exclude characters from the string.  For
      example, the string "pre[[replace-me]]post" could be grouped into
      "pre"/"replace-me"/"post".  Note that, unlike *PATTERN_BRACE_COLON*, this
      pattern excludes the special markers "[[" and "]]".  Note also that, in
      this case, if "replace-me" does not appear as a key in *replacements*, then
      "replace-me" (without the "[[" and "]]") will be written to *outFile*.
    - A replacement key should not contain any embedded newlines, since this
      function processes *templateFile* one line at a time.
    - The replacement text for a replacement key may contain newlines.
    - File-like objects include :class:`File`, :class:`StringIO`, and
      :class:`cStringIO`.  The latter makes it easy to process a template string
      with multiple replacement dictionaries.
    """
    #
    # Check inputs.
    assert( hasattr(templateFile,'read') )
    assert( hasattr(pattern,'match') )
    assert( dict == type(replacements) )
    assert( hasattr(outFile,'write') )
    assert( not outFile == templateFile )  # Don't try to overwrite the template file.
    #
    # Initialize.
    unmatched = dict()
    lineNo = 1
    #
    # Process *templateFile* by lines.
    for inLine in templateFile:
        #
        # Preserve newline characters.
        #   This is necessary in order to preserve "foreign" line endings, e.g.,
        # to keep DOS-style '\r\n' when running on a Mac.  In general, Python
        # either converts '\n' to the operating-system-appropriate line ending,
        # or else uses a literal '\n' (when writing a file in binary mode).
        got = __REX_LINE_ENDINGS.search(inLine)
        if( got ):
            inLine = got.group(1)
            lineEnding = got.group(2)
        else:
            lineEnding = ''
        #
        # Look for replacement keys in *inLine*.
        #   Note *inLine* may have more than one replacement key.
        #   Note use re.match(), rather than re.search(), to ensure match the
        # first replacement key.
        while( True ):
            got = pattern.match(inLine)
            if( not got ):
                break
            # Here, found a replacement key.
            outFile.write(got.group(1))
            replacementKey = got.group(2)
            if( replacementKey in replacements ):
                outFile.write(str(replacements[replacementKey]))
            else:
                # Pass unknown *replacementKey* through unchanged.
                outFile.write(replacementKey)
                if( replacementKey not in unmatched ):
                    unmatched[replacementKey] = lineNo
            # Prepare for next round of testing on *inLine*.
            inLine = got.group(3)
        #
        # Here, *inLine* has no more replacement keys.
        outFile.write(inLine)
        outFile.write(lineEnding)
        #
        # Prepare for next iteration.
        lineNo += 1
    #
    if( 0 == len(unmatched) ):
        return( None )
    return( unmatched )
    #
    # End :func:`fillTemplate_strKey`.


def copyTemplate(templateFile, outFile):
    """
    Copy a template file directly, making no replacements.

    **Args:**

    - *templateFile*, an open file-like object whose contents are to be copied.
    - *outFile*, an open file-like object to receive the results.

    **Notes:**

    - Neither *templateFile* nor *outFile* has to be positioned at the beginning
      of the file (if they are, it's probably more efficient to use
      :func:`shutil.copyfile`).
    """
    #
    # Check inputs.
    assert( hasattr(templateFile,'read') )
    assert( hasattr(outFile,'write') )
    assert( not outFile == templateFile )  # Don't try to overwrite the template file.
    #
    shutil.copyfileobj(templateFile, outFile)
    #
    # End :func:`copyTemplate`.
