import asyncio
import sys
from functools import wraps
from inspect import Parameter, Signature, signature
from operator import itemgetter
from typing import Sequence


def typer_async(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def is_help_option():
    return any(['-h' in sys.argv, '--help' in sys.argv])


def merge_signatures(
    first: Signature, second: Signature, *, drop: Sequence[str] = None
) -> Signature:
    """
    https://github.com/tiangolo/typer/issues/153#issuecomment-2016834465

    Merge two signatures.

    Returns a new signature where the parameters of the second signature have been
    injected in the first if they weren't already there (i.e. same name not found).

    The following rules are used:
      - parameter order is preserved, with parameter from first signature coming
        first, and parameters from second one coming after
      - when a parameter (same name) is found in both signatures, parameter from
        first signature is kept, but if its annotation or default value is Ellipsis
        they are replaced with annotation and default value coming from second
        parameter.
      - parameters in second signature whose name appear in drop list are not
        taken into account

    Once this is done, we do not have a valid signature. The following extra step
    are performed:
      - move all positional only parameter first. Positional only parameters will
        still be ordered together, but some parameters from second signature will
        now appear before parameters from first signature (the non positional only
        ones).
      - make sure we have at most one variadic parameter of each kind (keyword and
        non keyword). They can appear in both original signature but under same
        name. Otherwise a ValueError is raised.
      - move keyword only parameters last (just before variadic keyword perameter)
      - keyword only parameters are left as is. It does not seem to be a problem is
        some of have default values and appear before other keyword only parameters
        without default value.

    Result is still not a valid signature as we could have some positional only
    parameter with a default value, followed by non keyword or positional without
    default value. In this case, a ValueError will be raised.
    """
    params = dict(first.parameters)

    if drop is None:
        drop = []

    for n, p1 in second.parameters.items():
        if n in drop:
            continue

        if p0 := params.get(n):
            if p0.default is Ellipsis or p0.default is Parameter.empty:
                p0 = p0.replace(default=p1.default)
            if p0.annotation is Parameter.empty:
                p0 = p0.replace(annotation=p1.annotation)
            params[n] = p0
        else:
            params[n] = p1

    # Sort params by kind, moving params with default value after params without
    # default value within each kind group.
    params = sorted(
        params.values(),
        key=lambda p: 2 * p.kind + bool(p.default != Parameter.empty),
    )

    # Will raise if signature not valid
    return first.replace(parameters=params)


def with_extra_parameters(extra, *, drop: Sequence[str] = None):
    """
    https://github.com/tiangolo/typer/issues/153#issuecomment-2016834465

    Append extra parameters to Typer command.
    """
    if drop is None:
        drop = []

    def wrapper(command):
        s0 = signature(extra)
        s1 = signature(command)
        s2 = merge_signatures(s1, s0, drop=drop)

        # Correct dispatch with variadic args and PO parameters would be more tricky.
        # Don't konw if we have such use cases with typer.
        assert not any(
            p.kind
            in (
                Parameter.POSITIONAL_ONLY,
                Parameter.VAR_POSITIONAL,
                Parameter.VAR_KEYWORD,
            )
            for p in s2.parameters.values()
        )

        n0 = list(p.name for p in s0.parameters.values() if p.name not in drop)
        n1 = list(p.name for p in s1.parameters.values())
        a0 = itemgetter(*n0)
        a1 = itemgetter(*n1)

        @wraps(command)
        def wrapped(*args, **kwargs):
            b2 = s2.bind(*args, **kwargs)
            b2.apply_defaults()

            # Process extra parameters
            extra(**dict(zip(n0, a0(b2.arguments))))
            # Invoke typer command
            return command(**dict(zip(n1, a1(b2.arguments))))

        setattr(wrapped, '__signature__', s2)
        return wrapped

    return wrapper
