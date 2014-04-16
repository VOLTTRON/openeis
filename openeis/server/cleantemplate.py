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
