'''
Purpose:

   Exceptions used through-out Daddy Vision

'''

__pgmname__ = 'exceptions'
__version__ = '$Rev$'

__author__ = "AJ Reynolds"
__copyright__ = "Copyright 2011, AJ Reynolds"
__credits__ = []
__license__ = "GPL"

__maintainer__ = "AJ Reynolds"
__email__ = "stampedeboss@gmail.com"
__status__ = "Development"


class BaseDaddyVisionException(Exception):
    """Base exception all DaddyVision exceptions inherit from
    """
    pass

class InvalidPath(BaseDaddyVisionException):
    """Raised when an argument is a non-existent file or directory path
    """
    pass

class InvalidFilename(BaseDaddyVisionException):
    """Raised when a file does not conform to expected naming standard
    """
    pass

class NoValidFilesFound(BaseDaddyVisionException):
    """Raised when no valid files are found.
    """
    pass

class DuplicateFilesFound(BaseDaddyVisionException):
    """Raised when Duplicate files are found that are not due to PROPERs.
    """
    pass

class UserAbort(BaseDaddyVisionException):
    """User too an action to abort the process
    """
    pass

class UnexpectedErrorOccured(BaseDaddyVisionException):
    """Something unexpected occured.  Should not happen, if it does program error.
    """
    pass

class DictKeyError(BaseDaddyVisionException):
    """Raised if the Request dict is malformed
    """
    pass

class DataRetrievalError(BaseDaddyVisionException):
    """Raised when an error (such as a network problem) prevents SeriesInfo
    from being able to retrieve data such as episode name
    """

class InvalidArgumentType(BaseDaddyVisionException):
    """Raised when an argument is not expected type of object
    """
    pass


# Configuration Exceptions
class BaseConfigError(BaseDaddyVisionException):
    """Base exception for config errors
    """
    pass

class ConfigNotFound(BaseConfigError):
    """Raised if the config file is unavailable after attempting to create
    one using the default routine
    """
    pass

class ConfigValueError(BaseConfigError):
    """Raised if the config file is malformed or unreadable
    """
    pass

class RegxSelectionError(BaseConfigError):
    """Raised if the the Regx is unable to return all data from FileParse
    """
    pass

#Data Retrieval Exceptions
class SeriesNotFound(DataRetrievalError):
    """Raised when a series cannot be found
    """
    pass

class SeasonNotFound(DataRetrievalError):
    """Raised when requested season cannot be found
    """
    pass

class EpisodeNotFound(DataRetrievalError):
    """Raised when episode cannot be found
    """
    pass

class EpisodeNameNotFound(DataRetrievalError):
    """Raised when the name of the episode cannot be found
    """
    pass