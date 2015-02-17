# -*- coding: UTF-8 -*-
'''
    Initialization Routine for movies

    Routine is call on any import of a module in the library

'''
import re


__pgmname__ = 'movie'

__version__ = '@version: $Rev$'

__author__ = "@author: AJ Reynolds"
__copyright__ = "@copyright: Copyright 2011, AJ Reynolds"
__status__ = "@status: Development"
__license__ = "@license: GPL"

__maintainer__ = "@organization: AJ Reynolds"
__credits__ = []

class Movie(object):

    def __init__(self, **kwargs):

        super(Movie, self).__init__()

        self.title = None
        self.ids = None
        self.year = None
        self.plays = None

        if len(kwargs) > 0:
            for key, val in kwargs.items():
                if key == 'movie':
                    for key2, val2 in val.iteritems():
                        setattr(self, key2, val2)
                else:
                    setattr(self, key, val)

    # @property
    # def title(self):
    #     """The movie title."""
    #     return self._title
    # @title.setter
    # def title(self, value):
    #     if value is None:
    #         return
    #     value = value.encode('ascii', 'ignore')
    #     self.title = value
    #     self._title = value
    #
    # def _set_title(self, key, val):
    #     self.title = val
    #     return

    @property
    def _search_title(self):
        """The title of this :class:`Movie` formatted in a searchable way"""
        _title = self.title.replace(' ', '-').lower()
        _title = _title.replace('&', 'and')
        _title = re.sub('[^A-Za-z0-9\-]+', '', _title)
        return _title

    def search(self, show):
        pass

    def __str__(self):
        """Return a string representation of a :class:`TVShow`"""
        header = '<Movie>'
        header = map(str, header)
        header = ' '.join(header)
        return '{}: {}'.format(header, self.title.encode('ascii', 'ignore'))
    __repr__ = __str__

