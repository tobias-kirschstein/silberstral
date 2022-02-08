<img src="logo.png" width="150px"> Silberstral
===========
>Reveal the true shape of type vars

Python's typing system is weak and lacks features well known in other languages. 
For example, templating in C++ allows you to instantiate a new object of the templated class `T` via `T(..)` which is not possible in Python.
The **Silberstral** package provides remedy with a simple utility to obtain the actual *type* that a generic type var refers to:

#### C++
```cpp
template<typename T>
class DefaultContainer {
    
    T get(int idx) {
        defaultElement = T();  // <- in C++, we can access the actual class of T
        ...
    }
    
}
```
#### Python
```python
_T = TypeVar('_T')
class DefaultContainer(Generic[_T]):
    
    def get(self, idx: int) -> _T:
        default_element =  _T()  # <- DOES NOT WORK
        ...
```

#### Python + Silberstral

```python
from silberstral import reveal_type_var

_T = TypeVar('_T')
class DefaultList(Generic[_T]):
    
    def get(self, idx: int) -> _T:
        T_cls = reveal_type_var(self, _T)  # <- Reveals the actual class of _T, e.g., int, str, ...
        default_element = T_cls()
        ...
```

## Usage
`reveal_type_var(obj_or_cls, type_var)`: Finds the actual type that `type_var` was instantiated to in `obj_or_cls`.

Example:
```python
from typing import TypeVar, Generic
from silberstral import reveal_type_var

_T = TypeVar('_T')
class List(Generic[_T]):
    pass

reveal_type_var(List[int], _T)
>>> int

str_list = List[str]()
reveal_type_var(str_list, _T)
>>> str
```
---
`reveal_type_vars(obj_or_cls)`: Lists all type vars and their corresponding instantiations of `obj_or_cls`

Example:
```python
from typing import TypeVar, Generic
from silberstral import reveal_type_vars

_K = TypeVar('_K')
_V = TypeVar('_V')
class Dict(Generic[_K, _V]):
    pass

reveal_type_vars(Dict[int, str])
>>> {_K: int, _V: str}
```
---
`is_type_var_instantiated(obj_or_cls, type_var)`: Checks whether `type_var` was instantiated with an actual class in `obj_or_cls`

Example:

```python
from typing import TypeVar, Generic
from silberstral import is_type_var_instantiated

_T = TypeVar('_T')
class List(Generic[_T]):
    pass

is_type_var_instantiated(List, _T)
>>> False

is_type_var_instantiated(List[int], _T)
>>> True
```
