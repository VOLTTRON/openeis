# -*- coding: utf-8 -*- {{{
# vim: set fenc=utf-8 ft=python sw=4 ts=4 sts=4 et:
#
# Copyright (c) 2014, Battelle Memorial Institute
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.
#
#
# This material was prepared as an account of work sponsored by an
# agency of the United States Government.  Neither the United States
# Government nor the United States Department of Energy, nor Battelle,
# nor any of their employees, nor any jurisdiction or organization
# that has cooperated in the development of these materials, makes
# any warranty, express or implied, or assumes any legal liability
# or responsibility for the accuracy, completeness, or usefulness or
# any information, apparatus, product, software, or process disclosed,
# or represents that its use would not infringe privately owned rights.
#
# Reference herein to any specific commercial product, process, or
# service by trade name, trademark, manufacturer, or otherwise does
# not necessarily constitute or imply its endorsement, recommendation,
# or favoring by the United States Government or any agency thereof,
# or Battelle Memorial Institute. The views and opinions of authors
# expressed herein do not necessarily state or reflect those of the
# United States Government or any agency thereof.
#
# PACIFIC NORTHWEST NATIONAL LABORATORY
# operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
# under Contract DE-AC05-76RL01830
#
#}}}

'''
Provides a context manager to wrap around calls to Template.render() to
remove the extraneous whitespace left by block-level tags.

Use thus:

    import cleantemplate import *

    template = Template(open('template.txt').read())
    context = Context()
    with clean_render():
        result = template.render(context)
    print(result)
'''

import re
import threading

import django.template
from django.template import *
from django.template import Node, NodeList, TextNode
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe


__all__ = django.template.__all__ + ('clean_render',)


_trailing_space_nl = re.compile(r'\r?\n[ \t]*$')
_trailing_space = re.compile(r'[ \t]*$')
_leading_space_nl = re.compile(r'^[ \t]*\r?\n')


def render_clean_nodes(nodelist, context):
    '''Remove extra space caused by block-level tags.

    This generator takes advantage of the fact that node tokens
    alternate between TextNode. Only non-TextNode nodes trigger cleaning
    and only if the TextNodes on either side of the node are either non-
    existent (only if first or last node in list) or both have
    whitespace leading up to a newline touching the node. Cleaning
    involves removing that touching whitespace and trimming extra
    whitespace from the end of the nodes text.
    '''
    if not nodelist:
        return
    # The following is basically Nodelist.render wrapped in a generator.
    nodes = ((force_text(nodelist.render_node(node, context)
              if isinstance(node, Node) else node), node) for node in nodelist)
    prev_text, prev_node = '', None
    text, node = next(nodes)
    for next_text, next_node in nodes:
        if not isinstance(node, TextNode):
            if not prev_node:
                text = _leading_space_nl.sub('', text)
            if not next_node:
                text = _trailing_space_nl.sub('', text)
            if (_trailing_space_nl.search(prev_text) and
                    _leading_space_nl.search(next_text)):
                prev_text = _trailing_space_nl.sub('', prev_text)
                text = _trailing_space.sub('', text)
                if text:
                    next_text = _leading_space_nl.sub('', next_text)
        yield prev_text
        prev_text, prev_node = text, node
        text, node = next_text, next_node
    if prev_node:
        yield prev_text
    yield text


def render_clean(nodelist, context):
    '''Similar to NodeList.render, but with cleaned nodes.'''
    # While render_clean_nodes reimplements the top of Nodelist.render,
    # this function reimplements the bottom couple of lines.
    return mark_safe(''.join(render_clean_nodes(nodelist, context)))


def local_renderer(func):
    '''Decorator to use custom rendering with NodeList.render.

    This function wraps NodeList.render and calls NodeList.render if no
    renderer is stored in thread-local storage. If a renderer is found,
    however, the renderer will be called instead.
    '''
    if hasattr(func, '_renderer'):
        return func
    local = threading.local()
    def render(self, context):
        return getattr(local, 'render', func)(self, context)
    render.__dict__ = func.__dict__
    render.__name__ = func.__name__
    render.__doc__ = func.__doc__
    render._renderer = local
    return render


class clean_render(object):
    '''Context manager to use render_clean as local renderer.'''

    def __enter__(self):
        try:
            local = NodeList.render._renderer
        except AttributeError:
            NodeList.render = local_renderer(NodeList.render)
            local = NodeList.render._renderer
        local.render = render_clean

    def __exit__(self, exc_type, exc_value, traceback):
        del NodeList.render._renderer.render
