import sys
from typing import TypeVar, Generic, Iterable, Iterator, T_co, Container, Collection, List, Deque, Set, Dict, Generator, \
    T, KT, VT, T_contra, V_co, Union
from unittest import TestCase

from silberstral import reveal_type_var, get_origin, gather_types, reveal_type_vars

_T1 = TypeVar('_T1')
_T2 = TypeVar('_T2')
_T3 = TypeVar('_T3')


# =========================================================================
# Setup inheritance structures with type vars
# =========================================================================

# -------------------------------------------------------------------------
# Dummy Value Classes
# -------------------------------------------------------------------------

class Value1:
    pass


class Value2:
    pass


class Value3:
    pass


# -------------------------------------------------------------------------
# Generic Dummy classes
# -------------------------------------------------------------------------

class SuperClass1TypeVar(Generic[_T1]):
    pass


class SuperClass1TypeVarA(Generic[_T1]):
    pass


class SuperClass1TypeVarB(Generic[_T2]):
    pass


class SuperClass2TypeVar(Generic[_T1, _T2]):
    pass


class MiddleClass1TypeVar(SuperClass1TypeVar[_T1]):
    pass


class MiddleClass1TypeVarA(SuperClass1TypeVarA[_T1]):
    pass


class MiddleClass1TypeVarB(SuperClass1TypeVarA[_T2]):
    pass


class MiddleClass2TypeVar(SuperClass2TypeVar[_T1, _T2]):
    pass


# -------------------------------------------------------------------------
# 1 TypeVar
# -------------------------------------------------------------------------

class TypeVar1(SuperClass1TypeVar[Value1]):
    pass


class TypeVar1Level2(MiddleClass1TypeVar[Value1]):
    pass


# -------------------------------------------------------------------------
# 2 TypeVars
# -------------------------------------------------------------------------

class TypeVar2(SuperClass2TypeVar[Value1, Value2]):
    pass


class TypeVar2Level2(MiddleClass2TypeVar[Value1, Value2]):
    pass


# -------------------------------------------------------------------------
# 2 TypeVars, partial TypeVar instantiation
# -------------------------------------------------------------------------

class MiddleClass2TypeVarInstantiatedFirst(SuperClass2TypeVar[Value1, _T2]):
    pass


class MiddleClass2TypeVarInstantiatedSecond(SuperClass2TypeVar[_T1, Value2]):
    pass


class TypeVar2Level2InstantiatedFirst(MiddleClass2TypeVarInstantiatedFirst[Value2]):
    pass


class TypeVar2Level2InstantiatedSecond(MiddleClass2TypeVarInstantiatedSecond[Value1]):
    pass


# -------------------------------------------------------------------------
# 2 TypeVars, one added at middle layer
# -------------------------------------------------------------------------

class MiddleClass2TypeVarsAddGeneric(SuperClass1TypeVar[Value1], Generic[_T2]):
    pass


# -------------------------------------------------------------------------
# Multiple inheritance, 1 Level
# -------------------------------------------------------------------------

class TypeVar1Super11(SuperClass1TypeVar[Value1], SuperClass1TypeVarB[Value2]):
    pass


class TypeVar2Super12(SuperClass1TypeVar[Value1], SuperClass2TypeVar[Value1, Value2]):
    pass


class TypeVar2Super21(SuperClass2TypeVar[Value1, Value2], SuperClass1TypeVar[Value1]):
    pass


# -------------------------------------------------------------------------
# Multiple inheritance, 2 Levels
# -------------------------------------------------------------------------

class TypeVar2Super11Level2(MiddleClass1TypeVar[Value1], MiddleClass1TypeVarB[Value2]):
    pass


class TypeVar2Super12Level2(MiddleClass1TypeVarA[Value1], MiddleClass2TypeVar[Value1, Value2]):
    pass


class TypeVar2Super21Level2(MiddleClass2TypeVar[Value1, Value2], MiddleClass1TypeVarA[Value1]):
    pass


# -------------------------------------------------------------------------
# Multiple inheritance, partially instantiated
# -------------------------------------------------------------------------

class TypeVar2SuperInstantiatedFirst1(MiddleClass2TypeVarInstantiatedFirst[Value2], SuperClass1TypeVarA[Value1]):
    pass


class TypeVar2SuperInstantiatedSecond1(MiddleClass2TypeVarInstantiatedSecond[Value1], SuperClass1TypeVarA[Value1]):
    pass


class TypeVar2SuperInstantiatedSecondInstantiatedSecond(MiddleClass2TypeVarInstantiatedSecond[Value1],
                                                        MiddleClass2TypeVarInstantiatedFirst[Value2]):
    pass


# -------------------------------------------------------------------------
# Iterable
# -------------------------------------------------------------------------
class SuperClass1Iterable(Iterable[_T1]):

    def __iter__(self) -> Iterator[_T1]:
        pass


class TypeVar1IterableDirect(Iterable[Value1]):

    def __iter__(self) -> Iterator[T_co]:
        pass


class TypeVar1Iterable(SuperClass1Iterable[Value1]):
    pass


class MiddleClass1Iterable(SuperClass1Iterable[_T1]):
    pass


class TypeVar1IterableLevel2(MiddleClass1Iterable[Value1]):
    pass


# -------------------------------------------------------------------------
# Internal Types
# -------------------------------------------------------------------------

class SuperClassIterator(Iterator[_T1]):
    pass


class SuperClassContainer(Container[_T1]):
    pass


class SuperClassCollection(Collection[_T1]):
    pass


class SuperClassList(List[_T1]):
    pass


class SuperClassDeque(Deque[_T1]):
    pass


class SuperClassSet(Set[_T1]):
    pass


class SuperClassDict(Dict[_T1, _T2]):
    pass


class SuperClassGenerator(Generator[_T1, _T2, _T3]):
    pass


# -------------------------------------------------------------------------
# Internal Types, Multiple Inheritance
# -------------------------------------------------------------------------

class InheritsMultipleContainers(SuperClass1TypeVar[Value1], Dict[Value2, Value3]):
    pass


if sys.version_info >= (3, 9):
    # In Python >= 3.9, the explicit type vars are removed for the built-in containers
    # As a workaround, we allow referencing type vars also by the order in which they were defined
    T_co, KT, T = 0, 0, 0
    VT, T_contra = 1, 1
    V_co = 2


# =========================================================================
# Actual Tests
# =========================================================================

class GenericTest(TestCase):

    def test_reveal_type_var(self):
        self.assertEqual(reveal_type_var(SuperClass1TypeVar[Value1], _T1), Value1)
        self.assertEqual(reveal_type_var(SuperClass2TypeVar[Value1, Value2], _T1), Value1)
        self.assertEqual(reveal_type_var(SuperClass2TypeVar[Value1, Value2], _T2), Value2)

        self.assertEqual(reveal_type_var(TypeVar1, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar1Level2, _T1), Value1)

        self.assertEqual(reveal_type_var(TypeVar2, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar2, _T2), Value2)
        self.assertEqual(reveal_type_var(TypeVar2Level2, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar2Level2, _T2), Value2)

        self.assertEqual(reveal_type_var(TypeVar2Level2InstantiatedFirst, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar2Level2InstantiatedFirst, _T2), Value2)
        self.assertEqual(reveal_type_var(TypeVar2Level2InstantiatedSecond, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar2Level2InstantiatedSecond, _T2), Value2)

        self.assertEqual(reveal_type_var(TypeVar1Super11, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar2Super12, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar2Super12, _T2), Value2)
        self.assertEqual(reveal_type_var(TypeVar2Super21, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar2Super21, _T2), Value2)

        self.assertEqual(reveal_type_var(TypeVar2Super11Level2, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar2Super11Level2, _T2), Value2)
        self.assertEqual(reveal_type_var(TypeVar2Super12Level2, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar2Super12Level2, _T2), Value2)
        self.assertEqual(reveal_type_var(TypeVar2Super21Level2, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar2Super21Level2, _T2), Value2)

        self.assertEqual(reveal_type_var(TypeVar2SuperInstantiatedFirst1, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar2SuperInstantiatedFirst1, _T2), Value2)
        self.assertEqual(reveal_type_var(TypeVar2SuperInstantiatedSecond1, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar2SuperInstantiatedSecond1, _T2), Value2)
        self.assertEqual(reveal_type_var(TypeVar2SuperInstantiatedSecondInstantiatedSecond, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar2SuperInstantiatedSecondInstantiatedSecond, _T2), Value2)

    def test_reveal_type_vars(self):
        self.assertEqual(reveal_type_vars(MiddleClass2TypeVarInstantiatedFirst), {_T1: Value1})

    def test_reveal_type_var_iterable(self):
        self.assertEqual(reveal_type_var(Iterable[Value1], T_co), Value1)
        self.assertEqual(reveal_type_var(TypeVar1IterableDirect, T_co), Value1)
        self.assertEqual(reveal_type_var(TypeVar1Iterable, _T1), Value1)
        self.assertEqual(reveal_type_var(TypeVar1IterableLevel2, _T1), Value1)

    def test_reveal_type_var_internal_collections(self):
        self.assertEqual(reveal_type_var(Iterator[Value1], T_co), Value1)
        self.assertEqual(reveal_type_var(SuperClassIterator[Value1], _T1), Value1)

        self.assertEqual(reveal_type_var(Container[Value1], T_co), Value1)
        self.assertEqual(reveal_type_var(SuperClassContainer[Value1], _T1), Value1)

        self.assertEqual(reveal_type_var(Collection[Value1], T_co), Value1)
        self.assertEqual(reveal_type_var(SuperClassCollection[Value1], _T1), Value1)

        self.assertEqual(reveal_type_var(List[Value1], T), Value1)
        self.assertEqual(reveal_type_var(SuperClassList[Value1], _T1), Value1)

        self.assertEqual(reveal_type_var(Deque[Value1], T), Value1)
        self.assertEqual(reveal_type_var(SuperClassDeque[Value1], _T1), Value1)

        self.assertEqual(reveal_type_var(Set[Value1], T), Value1)
        self.assertEqual(reveal_type_var(SuperClassSet[Value1], _T1), Value1)

        self.assertEqual(reveal_type_var(Dict[Value1, Value2], KT), Value1)
        self.assertEqual(reveal_type_var(Dict[Value1, Value2], VT), Value2)
        self.assertEqual(reveal_type_var(SuperClassDict[Value1, Value2], _T1), Value1)
        self.assertEqual(reveal_type_var(SuperClassDict[Value1, Value2], _T2), Value2)

        self.assertEqual(reveal_type_var(Generator[Value1, Value2, Value3], T_co), Value1)
        self.assertEqual(reveal_type_var(Generator[Value1, Value2, Value3], T_contra), Value2)
        self.assertEqual(reveal_type_var(Generator[Value1, Value2, Value3], V_co), Value3)
        self.assertEqual(reveal_type_var(SuperClassGenerator[Value1, Value2, Value3], _T1), Value1)
        self.assertEqual(reveal_type_var(SuperClassGenerator[Value1, Value2, Value3], _T2), Value2)
        self.assertEqual(reveal_type_var(SuperClassGenerator[Value1, Value2, Value3], _T3), Value3)

        if sys.version_info >= (3, 9):
            # Specifically, for Python >= 3.9 test whether the order of type vars corresponds to the indices
            # returned by reveal_type_vars
            self.assertEqual(reveal_type_vars(InheritsMultipleContainers), {_T1: Value1, 1: Value2, 2: Value3})

    def test_get_origin(self):
        # Generic classes without any type var specification should return None as origin
        self.assertIsNone(get_origin(List))
        self.assertIsNone(get_origin(SuperClass1TypeVar))
        self.assertIsNone(get_origin(SuperClass2TypeVar))
        # Inherits from generic class (with instantiated type var) but itself is not generic
        self.assertIsNone(get_origin(TypeVar1))

        # Anytime some generic class is instantiated with class[types, ...] we should be able to get class back
        self.assertEqual(get_origin(List[Value1]), List)
        self.assertEqual(get_origin(SuperClass1TypeVar[Value1]), SuperClass1TypeVar)
        self.assertEqual(get_origin(SuperClass2TypeVar[Value1, Value2]), SuperClass2TypeVar)
        self.assertEqual(get_origin(MiddleClass2TypeVarsAddGeneric[Value1]), MiddleClass2TypeVarsAddGeneric)

    def test_gather_types(self):
        # Built-in collections
        self.assertEqual(gather_types(List), set())
        self.assertEqual(gather_types(List[int]), {int})
        self.assertEqual(gather_types(Dict[Value1, Value2]), {Value1, Value2})
        self.assertEqual(gather_types(Union[List[Value1], Dict[Value2, Set[Value3]]], Value1), {Value1, Value2, Value3})

        # Currently, type vars instantiated through subclassing will NOT be listed
        self.assertEqual(gather_types(TypeVar2Super11Level2), {TypeVar2Super11Level2})
