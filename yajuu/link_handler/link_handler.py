import urllib.parse
import importlib


def handle_link(url, *args, **kwargs):
    """'Unshorten's' a link: try to get the original source(s) from an external
    service.

    For example, what if you got a youtube player on different websites? Would
    you rewrite the same code for each one of them? This is what this module is
    about. You write adapters for different players, or external sites and then
    reuse this method.

    This method uses lazy loading to load the necessary handlers, that's to
    save time for the initial response time.

    Note:
        Ususually, the link handlers are not specialized in the media type, but
        in storing files. For example, while kissanime proposes a catalog of
        videos, they use the google servers to store the videos. You would use
        an extractor to extract the links the videos from kissanime, and then
        a link handler to extract the data from the google servers.

    Args:
        *args, **kwargs: the arguments to be passed to the sources constructors
            if needed (eg: if you already know the quality of the streams).
    
    Returns:
        A source list (yajuu.sources.SourceList) object, or None.
    
    """
    
    # Add the netloc of the site here, and then the name of the handler
    handlers = {
        'tiwi.kiwi': 'tiwi_kiwi',
        'solidfiles.com': 'solidfiles',
        'mp4upload.com': 'mp4upload',
        'stream.moe': 'stream_moe',
        'bakavideo.tv': 'bakavideo',
        'drive.google.com': 'google_drive',
        'docs.google.com': 'google_drive',
        'tusfiles.net': 'tusfiles',
        'upload.af': 'upload_af',
        'openload.co': 'openload',
        'playbb.me': 'playbb',
        'videonest.net': 'videonest'
    }

    # Extract the host (netloc) from the passed url.
    host = urllib.parse.urlparse(url).netloc

    if host.startswith('www.'):
        host = host[4:]

    if host not in handlers:
        return None

    # Now that we have the handler's name, we can lazy import it
    return importlib.import_module(
        'yajuu.link_handler.' + handlers[host]
    ).handle_link(url, *args, **kwargs)
