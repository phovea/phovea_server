###############################################################################
# Caleydo - Visualization for Molecular Biology - http://caleydo.org
# Copyright (c) The Caleydo Team. All rights reserved.
# Licensed under the new BSD license, available at http://caleydo.org/license
###############################################################################

from flask import Flask as Namespace, request, abort, make_response, Response, send_from_directory, safe_join, jsonify, render_template_string, send_file  # noqa


# based on https://github.com/miguelgrinberg/oreilly-flask-apis-video/blob/master/orders/app/decorators/caching.py
def cache_control(*directives):
  """Insert a Cache-Control header with the given directives."""
  import functools

  def decorator(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
      # invoke the wrapped function
      rv = f(*args, **kwargs)

      # convert the returned value to a response object
      rv = make_response(rv)

      # insert the Cache-Control header and return response
      rv.headers['Cache-Control'] = ', '.join(directives)
      return rv

    return wrapped

  return decorator


def no_cache(f):
  """Insert a no-cache directive in the response. This decorator just
  invokes the cache-control decorator with the specific directives."""
  return cache_control('private', 'no-cache', 'no-store', 'max-age=0')(f)


def etag(f):
  """Add entity tag (etag) handling to the decorated route."""
  import functools

  @functools.wraps(f)
  def wrapped(*args, **kwargs):
    if request.method not in ['GET', 'HEAD']:
      # etags only make sense for request that are cacheable, so only
      # GET and HEAD requests are allowed
      return f(*args, **kwargs)

    # invoke the wrapped function and generate a response object from
    # its result
    rv = f(*args, **kwargs)
    rv = make_response(rv)

    # if the response is not a code 200 OK then we let it through
    # unchanged
    if rv.status_code != 200 or rv.direct_passthrough or not rv.implicit_sequence_conversion:
      return rv

    rv.add_etag()
    return rv.make_conditional(request)
  return wrapped
