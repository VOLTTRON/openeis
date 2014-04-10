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
from django.utils.safestring import mark_safe, SafeData


__all__ = django.template.__all__ + ('clean_render',)


_sub_trailing_space_nl = re.compile(r'\r?\n[ \t]*$').sub
_sub_trailing_space = re.compile(r'[ \t]*$').sub
_sub_leading_space_nl = re.compile(r'^[ \t]*\r?\n').sub


class JoinedStr(str, SafeData):
    '''Wraps strings returned from NodeList.render so they can be
    detected as such by cleaning functions.'''
    pass


def clean_spaces(prev, node):
    '''Remove extra space caused by block-level tags.

    This function takes advantage of the fact that node tokens alternate
    between TextNode nodes and tag nodes. If a tag node is empty, and it
    stands alone on a line, the line is removed which involves removing
    spaces and tabs, up to and including a newline, from the end of the
    previous TextNode and removing all spaces and tabs, up to and
    including a newline, from the front of the next TextNode. If the
    node is nodelist, only the trailing spaces and tabs must be removed
    from the previous node.
    '''
    node_text, node_obj = node if node else ('', None)
    prev_text, prev_obj = prev if prev else ('', None)
    if not prev_text and isinstance(node_obj, TextNode):
        # The previous node was empty, so adjust space before current node.
        node_text = _sub_leading_space_nl('', node_text)
    if isinstance(node_text, JoinedStr):
        # Node text is from a node list and will likely not be empty, but
        # is caused by a block tag where previous space should be adjusted.
        prev_text = _sub_trailing_space('', prev_text)
    elif not node_text and isinstance(prev_obj, TextNode):
        # Current node is empty, so adjust space after previous node.
        prev_text = _sub_trailing_space_nl('', prev_text)
    return prev_text, node_text


def render_clean(nodelist, context, clean):
    '''Similar to NodeList.render, but with a cleaner.
    
    The clean function takes two 2-tuples as arguments: the first is the
    rendered text and object instance of the previous node; the second
    the rendered text and object instance of the current node. The first
    argument will be None for the first node processed and the second
    will be None after the last node is processed. The clean function
    should return a tuple containing two strings: the rendered text of
    the previous and current nodes. The text of the previous node will
    be appended to the output of the function and the current node and
    its text will be saved for the next round. The results are also
    wrapped in a JoinedStr object to allow the cleaner to detect the
    results of a NodeList.render.
    '''
    bits = []
    prev = None
    for node in nodelist:
        if isinstance(node, Node):
            bit = nodelist.render_node(node, context)
        else:
            bit = node
        bit = force_text(bit)
        bit, text = clean(prev, (bit, node))
        prev = (text, node)
        if bit:
            bits.append(bit)
    if prev:
        bit, text = clean(prev, None)
        if bit:
            bits.append(bit)
    return JoinedStr(mark_safe(''.join(bits)))


def with_cleaner(func):
    '''Decorator to add template cleaning to NodeList.render.

    This function wraps NodeList.render and calls NodeList.render
    normally if no cleaner is stored in thread-local storage. If a
    cleaner is found, however, render_clean will be called with the
    cleaner instead to provide clean template rendering.
    '''
    if hasattr(func, '_cleaner'):
        return func
    local = threading.local()
    def render(self, context):
        try:
            clean = local.clean
        except AttributeError:
            return func(self, context)
        return render_clean(self, context, clean)
    render.__dict__ = func.__dict__
    render.__name__ = func.__name__
    render.__doc__ = func.__doc__
    render._cleaner = local
    return render


class clean_render(object):
    '''Context manager for clean template rendering.

    The manager can be called with a custom cleaner if a different style
    of cleaning is desired. While in the context of the manager, the
    thread-local cleaner is set and NodeList rendering will use the
    cleaner.
    '''

    def __init__(self, cleaner=clean_spaces):
        self.cleaner = cleaner

    def __enter__(self):
        try:
            local = NodeList.render._cleaner
        except AttributeError:
            NodeList.render = with_cleaner(NodeList.render)
            local = NodeList.render._cleaner
        local.clean = self.cleaner

    def __exit__(self, exc_type, exc_value, traceback):
        del NodeList.render._cleaner.clean
