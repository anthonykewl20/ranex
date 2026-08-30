.. _default:

default
^^^^^^^

All optional arguments and some positional arguments may be omitted at the
command line.  The ``default`` keyword argument of
:meth:`~ArgumentParser.add_argument`, whose value defaults to ``None``,
specifies what value should be used if the command-line argument is not present.
For optional arguments, the ``default`` value is used when the option string
was not present at the command line::

   >>> parser = argparse.ArgumentParser()
   >>> parser.add_argument('--foo', default=42)
   >>> parser.parse_args(['--foo', '2'])
   Namespace(foo='2')
   >>> parser.parse_args([])
   Namespace(foo=42)

If the target namespace already has an attribute set, the action *default*
will not overwrite it::

   >>> parser = argparse.ArgumentParser()
   >>> parser.add_argument('--foo', default=42)
   >>> parser.parse_args([], namespace=argparse.Namespace(foo=101))
   Namespace(foo=101)

If the ``default`` value is a string, the parser parses the value as if it
were a command-line argument.  In particular, the parser applies any type_
conversion argument, if provided, before setting the attribute on the
:class:`Namespace` return value.  Otherwise, the parser uses the value as is::

   >>> parser = argparse.ArgumentParser()
   >>> parser.add_argument('--length', default='10', type=int)
   >>> parser.add_argument('--width', default=10.5, type=int)
   >>> parser.parse_args()
   Namespace(length=10, width=10.5)

For positional arguments with nargs_ equal to ``?`` or ``*``, the ``default`` value
is used when no command-line argument was present::

   >>> parser = argparse.ArgumentParser()
   >>> parser.add_argument('foo', nargs='?', default=42)
   >>> parser.parse_args(['a'])
   Namespace(foo='a')
   >>> parser.parse_args([])
   Namespace(foo=42)

For required_ arguments, the ``default`` value is ignored. For example, this
applies to positional arguments with nargs_ values other than ``?`` or ``*``,
or optional arguments marked as ``required=True``.

Providing ``default=argparse.SUPPRESS`` causes no attribute to be added if the
command-line argument was not present::

   >>> parser = argparse.ArgumentParser()
   >>> parser.add_argument('--foo', default=argparse.SUPPRESS)
   >>> parser.parse_args([])
   Namespace()
   >>> parser.parse_args(['--foo', '1'])
   Namespace(foo='1')
