import sys
from dataclasses import is_dataclass
from inspect import isclass
from typing import Type, Union, TypeVar, Generic, Iterable, Set, get_type_hints, Optional, \
    _GenericAlias, Dict, Collection

from dacite.types import is_generic_collection, extract_generic, is_union, is_generic

_T_TypeVar = TypeVar('_T_TypeVar', bound=TypeVar)


# =========================================================================
# Generic Methods
# =========================================================================

def get_origin(tp: _GenericAlias) -> Union[Type, None]:
    """
    Retrieves the generic base type of the passed (generic) class, e.g., `MyContainer[MySample]` -> `MyContainer`.
    Having the generic base class is useful if one wants to access the TypeVars that were defined in `tp`.
    `MyContainer[MySample]` tells you that one TypeVar has been instantiated with `MySample` while `MyContainer` tells
    you which TypeVars were defined (e.g., `class MyContainer(Generic[T])` ), so that one can link the TypeVar `T` to
    `MySample`, the instantiation.

    Parameters
    ----------
        tp:
            the generic type for which the generic base class should be retrieved. This should be a type that was
            instantiated with square brackets [], e.g., Iterable[MySample], as regular (non-generic) types don't have
            generic base classes

    Returns
    -------
        The corresponding generic base type of the passed class
    """

    if hasattr(tp, '_name') and tp._name is not None:
        try:
            from typing import _SpecialGenericAlias
        except ImportError:
            pass

        if sys.version_info < (3, 9) and tp._special or sys.version_info >= (3, 9) and isinstance(tp,
                                                                                                  _SpecialGenericAlias):
            # _special = True for Python's internal generic base class
            # e.g., Iterable: _special = True
            # Iterable[str]: _special = False
            # In Python >= 3.9, this flag was replaced with _SpecialGenericAlias
            return None
        else:
            # Internal Python generic types (such as List[], Iterable[]) are implemented slightly hacky.
            # When typing.get_origin() is called on them, the don't return the actual generic base type, but the
            # implementation from the collections module which lack TypeVars
            # (e.g., typing.Iterable[T] -> collections.Iterable).
            # To get the actual generic base type (i.e., typing.Iterable[T] -> typing.Iterable) exploit the _name
            # attribute that is set on Python's internal types and that directly links to the name of the correct
            # type in the typing module (which has generics)
            typing_modules = sys.modules['typing']
            if hasattr(typing_modules, tp._name):
                return getattr(typing_modules, tp._name)

    # Only works in Python >= 3.8
    # origin_cls = typing.get_origin(tp)
    if hasattr(tp, '__origin__'):
        # Get generic origin class
        return tp.__origin__
    else:
        # The passed type does not correspond to a _GenericAlias
        return None


def reveal_type_vars(obj_or_cls: Union[object, Type, _GenericAlias]) -> Dict[TypeVar, Type]:
    """
    Obtains a mapping of all defined type vars with their corresponding instantiations from the passed object or class.
    Type vars that are only defined but not instantiated will not be included in the returned dictionary.

    Examples
    --------
        >>> T1 = TypeVar("T1")
        >>> T2 = TypeVar("T2")
        >>> class TemplatedClass(Generic[T1, T2]):
        >>>     pass
        >>> reveal_type_vars(TemplatedClass[int, str])
        >>> >>> {T1: int, T2: str}

    Parameters
    ----------
    obj_or_cls:
        An instance of a templated class or the templated class itself

    Returns
    -------
        A dictionary that is mapping every type var to its instantiation
    """

    type_var_instantiations = dict()
    cls_origin = get_origin(obj_or_cls)

    if cls_origin is not None:
        # The passed object is actually a generic class

        if sys.version_info >= (3, 9):
            # built-in containers, e.g., List, Dict, do not have TypeVars anymore in Python >= 3.9
            # Instead, they have "anonymous" generics that are just parameterized by the number of type vars
            # In this case, the only thing we can do is enumerate the instantiations without mapping them to a type var
            from typing import _SpecialGenericAlias
            if isinstance(cls_origin, _SpecialGenericAlias):
                type_var_instantiations = dict(enumerate(obj_or_cls.__args__))
                return type_var_instantiations

        generic_types = _get_args(obj_or_cls)
        generic_type_vars = cls_origin.__parameters__
        type_var_instantiations = _pack_type_var_instantiations(generic_type_vars, generic_types)
    elif hasattr(obj_or_cls, "__orig_class__") and hasattr(obj_or_cls, "__parameters__"):
        # The passed object is an instance of a direct generic type, i.e., directly subclasses Generic[...]
        generic_types = _get_args(obj_or_cls.__orig_class__)
        generic_type_vars = obj_or_cls.__parameters__
        type_var_instantiations = _pack_type_var_instantiations(generic_type_vars, generic_types)
    elif hasattr(obj_or_cls, "__orig_bases__"):
        # The passed object is not itself a generic type, but inherits from templated types

        # Gather all typevars and their associated types of all superclasses of the passed object
        _rec_gather_generics(obj_or_cls, type_var_instantiations)

    return type_var_instantiations


def reveal_type_var(obj_or_cls: Union[object, Type, _GenericAlias],
                    type_var: Union[_T_TypeVar, int]) -> object:
    """
    Obtains the corresponding class instantiation of the given `type_var` for the passed `obj_or_cls`.

    In Python, one can inherit from a Generic[T] class where T is a type var, to hint templated classes.
    However, it is not possible to use the actual class that is passed for T when an instance is created.
    Instead, one would have to explicitly pass the class of the type var to the constructor.
    To avoid this dualism of class declarations for type hints and actual types which one can instantiate, this
    utility method allows retrieving of the actual type instance for a type var.

    Examples
    --------
        >>> T = TypeVar("T")
        >>> class TemplatedClass(Generic[T]):
        >>>     pass
        >>> assert reveal_type_var(TemplatedClass[int], T) == int
        >>> float_obj = TemplatedClass[float]()
        >>> assert reveal_type_var(float_obj, T) == float

    Parameters
    ----------
    obj_or_cls:
        An instance of a templated class or the templated class itself for which the instantiated type var should
        be retrieved. If an object or type is passed which does not inherit from Generic, an error is thrown
    type_var:
        for which of the type vars that appear in the inheritance tree of the passed object or class the respective
        instantiated class should be retrieved. If a type var is passed which does not belong to any of the specified
        type vars in the inheritance tree of the passed object or class, an error is thrown.
        Instead of the type var itself, retrieving the instantiation can also be done via the index of the type var.

    Returns
    -------
        the instantiated class for the respective `type_var` of the templated `obj_or_cls`
    """

    type_var_instantiations = reveal_type_vars(obj_or_cls)
    # If none of the above cases occurred, the passed object apparently was not a templated type
    assert len(type_var_instantiations) > 0, \
        f"Could not determine template types of `{obj_or_cls}`. Is it a generic type or instance?"

    # Find the specified type_var in the gathered typevars of all superclasses and return the respective template
    # instantiation
    if type_var in type_var_instantiations:
        # Type var could be directly matched
        return type_var_instantiations[type_var]
    else:
        # Try to find type var by name
        type_var_instantiation_items = type_var_instantiations.items()
        matching_type_var_instantiations = [tv_instantiation
                                            for tv, tv_instantiation
                                            in type_var_instantiation_items
                                            if tv.__name__ == type_var.__name__]
        assert len(matching_type_var_instantiations) == 1, \
            f"Could not find typevar `{type_var}` for `{obj_or_cls}"

        return matching_type_var_instantiations[0]


def is_type_var_instantiated(obj_or_cls: Union[object, Type, _GenericAlias], type_var: TypeVar) -> bool:
    """
    Returns whether the specified `type_var` is instantiated in the class definition of `obj_or_cls`.
    Type vars can stay uninstantiated when one subclasses a generic type without specifying its type variables.

    Parameters
    ----------
    obj_or_cls:
        An instance of a templated class or the templated class itself for which instantiation of `type_var` should be
        checked
    type_var:
        which type var to check

    Returns
    -------
        whether `type_var` is instantiated in the class definition of `obj_or_class`
    """

    type_var_instantiations = reveal_type_vars(obj_or_cls)
    return type_var in type_var_instantiations


def gather_types(types: Union[Iterable[Type], Type], parent_type: Optional[Type] = None) -> Set[Type]:
    """
    Gathers all types that are listed in some way in the specified type hint.
    Note: Types listed in super classes will NOT be returned

    Examples
    --------
        gather_types(Union[TypeA, List[TypeB]]) -> {TypeA, TypeB}

    Parameters
    ----------
        types: a collection of types that will be traversed recursively

    Returns
    -------
        All types that are listed in the specified type hint
    """

    # Ensure that types is iterable
    if is_generic_collection(types) or is_generic(types) or isclass(types):
        types = [types]

    all_types = set()
    for t in types:
        # t = t if inspect.isclass(t) else type(t)  # Ensure that passed value is a class
        # TODO: wrt parent_type: maybe we don't want to allow GenericAliases in dataclasses?
        if is_generic_collection(t) or is_union(t):
            all_types.update(gather_types(extract_generic(t), parent_type))
        elif is_dataclass(t):
            # TODO: Could get some infinite recursion here. Maybe track visited types?
            field_types = get_type_hints(t).values()
            all_types.update(gather_types(field_types, t))
        elif isinstance(t, TypeVar):
            t = reveal_type_var(parent_type, t)
            all_types.add(t)
        else:
            all_types.add(t)
    return all_types


def save_instantiate(cls_generic: _GenericAlias, *args, **kwargs) -> object:
    """
    Handles the rare use-case that one wants to instantiate a generic class without subclassing.
    In this case, Python's default way of instantiating generic classes prohibits the use of `reveal_type_var()` in
    the constructor.
    This is because generic classes are instantiated by first fully instantiating the class without type vars and then
    externally applying all type var information.
    The `save_instantiate(cls)` method alleviates this by first setting the type var information and then calling the
    constructor.
    From a user perspective, `save_instantiate(cls)` works the same as directly instantiating via `cls()`.

    Parameters
    ----------
        cls_generic:
            The generic class to be instantiated
        args:
            positional arguments for the constructor
        kwargs:
            keyword arguments for the constructor

    Returns
    -------
        An instance of the provided class, ensuring that `reveal_type_var()` calls in the constructor will succeed
    """

    obj = cls_generic.__new__(cls_generic.__origin__)
    obj.__orig_class__ = cls_generic
    obj.__init__(*args, **kwargs)
    return obj


def create_linked_type_var(other_type_var: TypeVar,
                           *constraints,
                           bound=None,
                           covariant=False,
                           contravariant=False) -> TypeVar:
    """
    Allows to refine a type var that is already been used by the super class.
    If the super class uses a type var _T1 and the middle class wants to make the bounds of _T1 specific, just creating
    a new type var _T2 and inheriting from SuperClass[_T2] does not work because the passed type var is never registered
    as _T1 in the super class. This is problematic if the super class wanted to reveal the type of _T1 but cannot do
    so if it was renamed to _T2 by the middle class.
    The workaround is to create a "linked" type var _T1_linked that simply shares the same name as _T1 but otherwise
    can freely add any bounds.
    That way, the super class will find _T1_linked as it internally still uses the name '_T1'.

    Examples:
    ---------

    >>> _T1 = TypeVar('_T1')
    >>> _T1_linked = create_linked_type_var(_T1, bound=int)
    >>> class SuperClass(Generic[_T1]):
    >>>     def __init__(self):
    >>>         self.cls_T1 = reveal_type_var(self, _T1)
    >>>
    >>> class MiddleClass(SuperClass[_T1_linked]):
    >>>     def __init__(self):
    >>>         super(MiddleClass, self).__init__()
    >>>         self.cls_T1_linked = reveal_type_var(self, _T1_linked)
    >>>
    >>> obj: MiddleClass = save_instantiate(MiddleClass[int])
    >>> assert obj.cls_T1 == obj.cls_T1_linked

    Parameters
    ----------
        other_type_var:
            the type var to link against. The newly created type var will inherit the name
        constraints:
            see TypeVar doc
        bound:
            see TypeVar doc
        covariant:
            see TypeVar doc
        contravariant:
            see TypeVar doc

    Returns
    -------
        a new type var that inherits the name of the given type var and hence can be identified by super classes to
        be linked to the old typ var.
    """

    return TypeVar(other_type_var.__name__, *constraints, bound=bound, covariant=covariant, contravariant=contravariant)


# =========================================================================
# Helper Methods
# =========================================================================

def _rec_gather_generics(cls: Union[object, Type], type_var_instantiations: Dict[TypeVar, Type]):
    # It can happen that a class without base classes was passed. In this case, don't do anything
    base_classes = cls.__orig_bases__ if hasattr(cls, '__orig_bases__') else []
    for base_class in base_classes:
        erased_class = get_origin(base_class)
        if erased_class == Generic:
            # Don't visit Generic superclasses as these are already implicitly handled by the subclass
            continue
        if erased_class is not None:
            # Current super class is a templated type. Hence, we can gather type vars and template instantiations
            type_instantiations = _get_args(base_class)
            type_vars = None
            if sys.version_info >= (3, 9):
                # built-in containers, e.g., List, Dict, do not have TypeVars anymore in Python >= 3.9
                # Instead, they have "anonymous" generics that are just parameterized by the number of type vars
                # In this case, the only thing we can do is enumerate the instantiations without mapping them to a type var
                from typing import _SpecialGenericAlias
                if isinstance(erased_class, _SpecialGenericAlias):
                    type_vars = range(len(type_var_instantiations),
                                      len(type_var_instantiations) + len(type_instantiations))

            if type_vars is None:
                # For non built-in types or Python < 3.9
                type_vars = erased_class.__parameters__

            # Collect instantiations for this type
            _pack_type_var_instantiations(type_vars, type_instantiations, type_var_instantiations)
            _rec_gather_generics(erased_class, type_var_instantiations)


def _pack_type_var_instantiations(type_vars: Collection[TypeVar],
                                  type_instantiations: Collection[Type],
                                  type_var_instantiations=None):
    if type_var_instantiations is None:
        type_var_instantiations = dict()

    assert len(type_instantiations) == len(type_vars), \
        f"Found different number of type vars ({type_vars}) and instantiations ({type_instantiations})"
    for type_var, type_instantiation in zip(type_vars, type_instantiations):
        if not isinstance(type_instantiation, TypeVar):
            if type_var in type_var_instantiations:
                assert type_var_instantiations[type_var] == type_instantiation, \
                    f"Mismatch for TypeVar {type_var}: " \
                    f"{type_var_instantiations[type_var]} and {type_instantiation}. " \
                    f"Is the {type_var} always instantiated with the same type?"
            else:
                type_var_instantiations[type_var] = type_instantiation

    return type_var_instantiations


def _get_args(obj_or_cls: Union[object, Type, _GenericAlias]):
    try:
        # Only available in Python >= 3.8
        from typing import get_args
        return get_args(obj_or_cls)
    except ImportError:
        # Python >= 3.7
        return obj_or_cls.__args__
