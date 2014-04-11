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


_trailing_space_nl = re.compile(r'\r?\n[ \t]*$')
_trailing_space = re.compile(r'[ \t]*$')
_leading_space_nl = re.compile(r'^[ \t]*\r?\n')


## Debugging functions
#
#def abbr(string, length=16):
#    if len(string) <= length:
#        return string
#    head = (length - 3) // 2
#    tail = length - head - 3
#    return ''.join([string[:head], '...', string[-tail:]])
#
#import sys
#
#def dump_nodes(prev, node, next, file=sys.stderr):
#    prev_text, prev_obj = prev if prev else ('', None)
#    node_text, node_obj = node if node else ('', None)
#    next_text, next_obj = next if next else ('', None)
#    print('{}({!r}), {}({!r}), {}({!r})'.format(
#            re.sub(r'Node$', '', type(prev_obj).__name__), abbr(prev_text),
#            re.sub(r'Node$', '', type(node_obj).__name__), abbr(node_text),
#            re.sub(r'Node$', '', type(next_obj).__name__), abbr(next_text)),
#          file=file)


def clean_spaces(prev, node, next):
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
    #dump_nodes(prev, node, next)
    prev_text = prev[0] if prev else ''
    node_text, node_obj = node if node else ('', None)
    next_text = next[0] if next else ''
    if (node and not isinstance(node_obj, TextNode) and
            (not prev or _trailing_space_nl.search(prev_text)) and
            (not next or _leading_space_nl.search(next_text))):
        prev_text = _trailing_space_nl.sub('', prev_text)
        if not prev:
            node_text = _leading_space_nl.sub('', node_text)
        node_text = _trailing_space.sub('', node_text)
        next_text = _leading_space_nl.sub('', next_text)
    return prev_text, node_text, next_text


def render_clean(nodelist, context, clean):
    '''Similar to NodeList.render, but with a cleaner.
    
    The clean function is called with three 2-tuples as arguments, which
    are the rendered text and node instances of the previous, current,
    and next nodes, respectively. The first and second arguments will be
    None for the first node processed and each node will work its way
    from next to current to previous with each succeeding call. The last
    node in the node list will have None as the last argument and
    finally be called with the node as the first argument and None for
    the remaining arugments. The clean function should return a tuple
    containing three strings, which are the rendered text of the
    previous, current, and next nodes, respectively. The text of the
    previous node will be appended to the output of the function and the
    current and next node texts will be saved and used in the next
    round.
    '''
    bits = []
    prev = (None, None)
    for node in nodelist:
        bit = force_text(nodelist.render_node(node, context)
                         if isinstance(node, Node) else node)
        args = prev + ((bit, node),)
        text = clean(*args)
        prev = (args[1] and (text[1], args[1][1]), args[2] and (text[2], args[2][1]))
        bit = text[0]
        if bit:
            bits.append(bit)
    while any(prev):
        args = prev + (None,)
        text = clean(*args)
        prev = (args[1] and (text[1], args[1][1]), args[2] and (text[2], args[2][1]))
        bit = text[0]
        if bit:
            bits.append(bit)
    return mark_safe(''.join(bits))


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
