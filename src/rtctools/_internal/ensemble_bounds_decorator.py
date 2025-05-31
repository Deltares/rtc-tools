import functools
import inspect


def ensemble_bounds_check(func):
    """
    Decorator for bounds() methods that enforces ensemble_member parameter handling
    based on the ensemble_specific_bounds feature flag.

    When ensemble_specific_bounds is True:
    - ensemble_member parameter must be passed (and must be integer)

    When ensemble_specific_bounds is False:
    - ensemble_member parameter must NOT be passed

    Raises appropriate TypeErrors with feature flag context.
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Check that the decorator is used on a method that matches the
        # expected signature
        sig = inspect.signature(func)

        has_ensemble_member_param = "ensemble_member" in sig.parameters

        if not has_ensemble_member_param:
            raise RuntimeError(
                f"bounds() method {func.__qualname__} must have 'ensemble_member' parameter. "
                f"Expected signature: def bounds(self, ensemble_member: Optional[int] = None)"
            )

        # Determine if ensemble_member was provided in the call
        ensemble_member_provided = False
        ensemble_member_value = None

        if args:
            # ensemble_member was passed as positional argument
            ensemble_member_provided = True
            ensemble_member_value = args[0]
        elif "ensemble_member" in kwargs:
            # ensemble_member was passed as keyword argument
            ensemble_member_provided = True
            ensemble_member_value = kwargs["ensemble_member"]

        # Check feature flag and enforce rules
        if self.ensemble_specific_bounds:
            # Feature flag is ON - ensemble_member should be passed
            if not ensemble_member_provided:
                raise TypeError(
                    f"{func.__name__}() missing 1 required positional argument: 'ensemble_member'. "
                    f"This is required when the 'ensemble_specific_bounds' feature flag is enabled."
                )
            if ensemble_member_provided and not isinstance(ensemble_member_value, int):
                raise TypeError(
                    f"ensemble_member must be an int, got {type(ensemble_member_value).__name__}"
                    f"This is required when the 'ensemble_specific_bounds' feature flag is enabled."
                )
        else:
            # Feature flag is OFF - ensemble_member should NOT be passed. Not even None.
            if ensemble_member_provided:
                raise TypeError(
                    f"{func.__name__}() takes 1 positional argument but 2 were given. "
                    f"The 'ensemble_member' parameter should not be provided when the "
                    f"'ensemble_specific_bounds' feature flag is disabled."
                )

        # Call the original function
        return func(self, *args, **kwargs)

    return wrapper
