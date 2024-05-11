# Management commands

All the management commands provided.

## collectstaticsite

The main entry point for usage. Readers all your renderers, gets the content of every
URL, and writes the content to the storage backend.

Accepts the following arguments:

- `--noinput` won\'t ask you to confirm before going ahead. Same principle as the
  [Django collectstatic command](https://docs.djangoproject.com/en/stable/ref/contrib/staticfiles/#collectstatic)
- `--processes=N` where `N` is a number, will split the reading and writing over the
  given number of processes using
  [multiprocessing](https://docs.python.org/3/library/multiprocessing.html)
