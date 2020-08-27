# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 Jonathan M. Lange <jml@mumak.net>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Library for formatting trees."""
from __future__ import annotations
import itertools
from typing import Generator
from toolz import partition_all

class Options(object):
    def __init__(self,
                 FORK=u'\u251c',
                 LAST=u'\u2514',
                 VERTICAL=u'\u2502',
                 HORIZONTAL=u'\u2500',
                 NEWLINE=u'\u23ce'):
        self.FORK = FORK
        self.LAST = LAST
        self.VERTICAL = VERTICAL
        self.HORIZONTAL = HORIZONTAL
        self.NEWLINE = NEWLINE

    def color(self, node, depth):
        return lambda text, *a, **kw: text

    def vertical(self):
        return u''.join([self.VERTICAL, u'   '])

    def fork(self):
        return u''.join([self.FORK, self.HORIZONTAL, self.HORIZONTAL, u' '])

    def last(self):
        return u''.join([self.LAST, self.HORIZONTAL, self.HORIZONTAL, u' '])



ASCII_OPTIONS = Options(FORK=u'|',
                        LAST=u'+',
                        VERTICAL=u'|',
                        HORIZONTAL=u'-',
                        NEWLINE=u'\n')


def _format_newlines(prefix, formatted_node, options):
    """
    Convert newlines into U+23EC characters, followed by an actual newline and
    then a tree prefix so as to position the remaining text under the previous
    line.
    """
    replacement = u''.join([
        options.NEWLINE,
        u'\n',
        prefix])
    return formatted_node.replace(u'\n', replacement)


def _format_tree(node, format_node, get_children, options, prefix=u'', depth=0):
    children = list(get_children(node))
    color = options.color(node, depth)
    #options.set_depth(depth)
    next_prefix = prefix + color(options.vertical())
    for child in children[:-1]:
        yield u''.join([prefix,
                        color(options.fork()),
                        _format_newlines(next_prefix,
                                         format_node(child),
                                         options)])
        for result in _format_tree(child,
                                   format_node,
                                   get_children,
                                   options,
                                   next_prefix,
                                   depth=depth + 1):
            yield result
    if children:
        last_prefix = u''.join([prefix, u'    '])
        yield u''.join([prefix,
                        color(options.last()),
                        _format_newlines(last_prefix,
                                         format_node(children[-1]),
                                         options)])
        for result in _format_tree(children[-1],
                                   format_node,
                                   get_children,
                                   options,
                                   last_prefix,
                                   depth=depth + 1):
            yield result

def paged_format_tree(node, format_node, get_children, options=None, page_size=0)->Generator[str]:
    lines = itertools.chain(
        [format_node(node)],
        _format_tree(node, format_node, get_children, options or Options()),
        [u""],
    )
    if page_size is None or page_size<=0:
        yield u"\n".join(lines)
    else:
        write_lines = partition_all(page_size, lines)
        while True:
            try:
                yield u"\n".join(next(write_lines))
            except StopIteration:
                break

def format_tree(node, format_node, get_children, options=None):
    lines = itertools.chain(
        [format_node(node)],
        _format_tree(node, format_node, get_children, options or Options()),
        [u""],
    )
    return u"\n".join(lines)



def format_ascii_tree(tree, format_node, get_children):
    """ Formats the tree using only ascii characters """
    return format_tree(tree,
                       format_node,
                       get_children,
                       ASCII_OPTIONS)


def print_tree(*args, **kwargs):
    print(format_tree(*args, **kwargs))
