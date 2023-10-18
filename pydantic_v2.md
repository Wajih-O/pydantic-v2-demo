# Pydantic V2 features

[pydantic-v2-demo](https://github.com/Wajih-O/pydantic-v2-demo)

demo the updates announced in the [v2 plan](https://docs.pydantic.dev/latest/blog/pydantic-v2/)

version used: Pydantic v2.2

---

## Pydantic?

A data validation and parsing library:

Helps defining data schemas via type hinting and custom validators.

```Python
from pydantic import BaseModel, validator
from datetime import datetime

class Car(BaseModel):
    make: str
    model: str
    year: int

    @validator("year")
    def validate_year(cls, value):
        current_year = datetime.now().year
        if not (1900 <= value <= current_year):
            raise ValueError("Invalid manufacturing year")
        return value
```

---

### Features

- Data Validation
- Automatic documentation
- Parsing and Serialization
- Default Values and Type Conversion
- Immutable Models
- Dependency Injection

...

---

## the V2

> Motivations: performance, maintainability, composability, and strict mode.

 Two packages design

1. **pydantic** (pure python, no Cython)
2. **pydantic-core** (rust (binary), stubs)

--

### Validation flow

1. **pydantic** read the type hints and construct a "core-schema dict"
2. **pydantic-core** process the core schema and return a **SchemaValidator**
3. **pydantic** calls schema_validator on the data (runs pydantic-core side)
4. **pydantic-core** validate, raise or returns the result (data)

<!-- ref: https://youtu.be/pWZw7hYoRVU?t=813 -->

---

### V2 perf. and more

Using rust/pyo3 underneath:

Gain in perf. (order of magnitude 10x, 5x to 50 x)

- Multithreading (perf.)
- Reusing rust libraries (perf. + maintainability)
- More explicit error handling (within rust) (maintainability)

---

but also in V2 ...

---

## Namespace clean-up

All methods on models will start with model_, fields' names will not be allowed to start with "model" (aliases can be used if required).

- avoid confusing gotchas when field names clash with methods on a model
- make it safer to add more methods

--

This is how the `BaseModel` class looks like

```python

class BaseModel:
    model_fields: List[FieldInfo]
    """previously `__fields__`, although the format will change a lot"""
    @classmethod
    def model_validate(cls, data: Any, *, context=None) -> Self:
        """ previously `parse_obj()`, validate data"""
    @classmethod
    def model_validate_json(
        cls,
        data: str | bytes | bytearray,
        *,
        context=None
    ) -> Self:
        """
        previously `parse_raw(..., content_type='application/json')`
        validate data from JSON
        """
    @classmethod
    def model_is_instance(cls, data: Any, *, context=None) -> bool:
        """
        new, check if data is value for the model
        """
    @classmethod
    def model_is_instance_json(
        cls,
        data: str | bytes | bytearray,
        *,
        context=None
    ) -> bool:
        """
        Same as `model_is_instance`, but from JSON
        """
    def model_dump(
        self,
        include: ... = None,
        exclude: ... = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        mode: Literal['unchanged', 'dicts', 'json-compliant'] = 'unchanged',
        converter: Callable[[Any], Any] | None = None
    ) -> Any:
        """
        previously `dict()`, as before
        with new `mode` argument
        """
    def model_dump_json(self, ...) -> str:
        """
        previously `json()`, arguments as above
        effectively equivalent to `json.dump(self.model_dump(..., mode='json'))`,
        but more performant
        """
    def model_json_schema(self, ...) -> dict[str, Any]:
        """
        previously `schema()`, arguments roughly as before
        JSON schema as a dict
        """
    def model_update_forward_refs(self) -> None:
        """
        previously `update_forward_refs()`, update forward references
        """
    @classmethod
    def model_construct(
        self,
        _fields_set: set[str] | None = None,
        **values: Any
    ) -> Self:
        """
        previously `construct()`, arguments roughly as before
        construct a model with no validation
        """
    @classmethod
    def model_customize_schema(cls, schema: dict[str, Any]) -> dict[str, Any]:
        """
        new, way to customize validation,
        e.g. if you wanted to alter how the model validates certain types,
        or add validation for a specific type without custom types or
        decorated validators
        """
    class ModelConfig:
        """
        previously `Config`, configuration class for models
        """

```

---

## Strict mode

Where data is not coerced but rather an error is raised

```python
class Energy(BaseModel):
    value: int  # energy value in wh
    def from_kwh(kwh: int) -> Self:
        return Energy(value=kwh * 10e3)
```

```python
Energy(value="3") # data coerced
```

```output
    Energy(value=3)
```

```python
class EnergyStrictMode(BaseModel):
    model_config = dict(strict=True)
    value: int  # energy value in wh
    def from_kwh(kwh: int) -> Self:
        return Energy(value=kwh * 10e3)
```

```python
with pytest.raises(ValidationError):
    EnergyStrictMode(value="3")
```

---

## Formalized <a href="https://docs.pydantic.dev/latest/usage/conversion_table/"> conversion table </a>

Solves inconsistency around data conversion

> If the input data has a single and intuitive representation in the field's type and no data is lost during the conversion then the data will be converted; otherwise a  validation error is raised.

--

### String fields

only **str, bytes and bytearray** are valid as inputs.

```python
class WithStringFields(BaseModel):
    s1: str
    s2: str

with pytest.raises(ValidationError):
    WithStringFields(s1=5, s2="5")

WithStringFields(s1="5", s2=b"test")

```

```output
WithStringFields(s1='5', s2='test')
```

---

## Builtin JSON support

**Pydantic-core** can parse json directly into a model or output type:

- Improves performance
- Avoids issue with strictness <sub> <sup> (no tuple in json) with external parser would parse it to a list which will be rejected in strict mode  </sup></sub>

```python
class WithATuple(WithStringFields):
    model_config = dict(strict=True)
    t3: tuple[int, int, str]

json_str = '{"s1": "s1", "s2": "s2", "t3": [1, 2, "third"]}'
```

```python
WithATuple.model_validate_json(json_str)
```

works fine,

--

while explicitly using python json parser

```python
try:
    WithATuple.model_validate(json.loads(json_str))
except ValidationError as e:
    print(e)
```

```output
1 validation error for WithATuple
t3
  Input should be a valid tuple [type=tuple_type, input_value=[1, 2, 'third'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.2/v/tuple_type
```


--

<!--
In future direct validation of JSON will also allow (maybe in 2.1):

- Parsing in a separate thread while starting validation in the main thread
- Line numbers from JSON to be included in the validation errors

(check an example of json validation)
-->

---

## Required vs nullable clean-up

A Nullable (accepting None as a value) might be also required

<!-- where None is explicitly required as a value -->

```python

class Foo(BaseModel):
    f1: str  # required, cannot be None
    f2: str | None  # required, can be None - same as Optional[str] / Union[str, None]
    f3: Optional[str]  # required, can be None (while in Pydantic v1 it is set to None)
    f4: str | None = None  # not required, can be None
    f5: str = 'Foobar'  # not required, but cannot be None

```

```python
Foo(f1="test", f2="123", f3="22")
Foo(f1="test", f2=None, f3="22")

with pytest.raises(ValidationError):
    # as f3 is required
    Foo(f1="test", f2="123")

```

---

## Validation without a model using TypeAdapter
<!-- TypeAdapter is formerly AnalyzedType  -->

In pydantic V1 the core of all validation was a pydantic model this led to:

- Performance penalty
- Extra complexity when the output data type was not  a model

--

- In V2 pydantic-core operates on a tree of validators with no model type required at the base of that tree.

- It can therefore validate a single string or datetime value a TypedDict or a Model equally easily

--

```python
from dataclasses import dataclass
from pydantic import model_validator, TypeAdapter 
#TypeAdapter is the new name for AnalyzedType
# (https://github.com/pydantic/pydantic/issues/5580)

@dataclass
class Point:
    x: float
    y: float

@dataclass
class Circle:
    center: Point
    radius: float


@dataclass
class Square:
    center: Point
    side: float


class Rectangle(BaseModel):
    center: Point
    width: float
    height: float

    @model_validator(mode='after')
    def infer_width_and_height(cls, data):
        if data.width <= 0:
            data.width *= -1
        if data.height <= 0:
            data.height *= -1
        return data

```


```python
simple_forms = TypeAdapter(Circle|Square|Rectangle)

for form in [{"center": {"x": 0, "y": 0}, "radius": 1},
             {"center": {"x": 0, "y": 0}, "side": 1},
             {"center": {"x": 0, "y": 0},
             "width": 10, "height": -5}]:
print(simple_forms.dump_json(
    simple_forms.validate_python(form)))
```

```output
    b'{"center":{"x":0.0,"y":0.0},"radius":1.0}'
    b'{"center":{"x":0.0,"y":0.0},"side":1.0}'
    b'{"center":{"x":0.0,"y":0.0},"width":10.0,"height":5.0}'
```

---

## Wrap validators

logic before and after catching error, new error or defaults

```python
class Energy(BaseModel):

    value: int  # energy value in wh

    @field_validator("value", mode="wrap")
    def validate_value(cls, value, handler):
        if value == "null": # Before handler error catching !
            return 0
        try:
            return handler(value)
        except ValidationError:
            return 0 # After handler catching error
    #...
```

```python
Energy(value="null")
```

```output
Energy(value=0)
```

---

## Validation using context

```python
import json
from pydantic import field_validator

class User(BaseModel):
    id: int
    name: str

    @field_validator("id")
    def check_user_in_vip(cls, v, info):
        if v not in info.context["vip_ids"]:
            raise ValueError("user is not in vip list")
        return v

```


```python
vip_ids = [1, 2, 3]
User.model_validate_json(
    json.dumps({"id": 1, "name": "John"}),
    context = {"vip_ids": vip_ids})
```

```output
    User(id=1, name='John')
```

```python
with pytest.raises(ValidationError):
    User.model_validate_json(
    json.dumps({"id": 4, "name": "John"}),
    context = {"vip_ids": vip_ids}
)
```

---

## More powerful alias(es)

<!-- alternative source/name for field, enable seamless mapping of different names of fields to corresponding model -->

supports simple alias as well as alias paths with flatten feature for mapping nested data

```python
from pydantic import AliasPath

data = {
    'al-bar': "simple",
    'baz': [
        {'qux': 'a'},
        {'qux': 'b'},
        {'qux': 'longer'},
    ]
}
```

```python
class FooSimplePath(BaseModel):
    bar: str = Field(validation_alias=AliasPath("al-bar"))
    # equivalent to
    # bar: str = Field(validation_alias="al-bar")

class FooLongerPath(BaseModel):
    bar: str = Field(validation_alias=\
    AliasPath('baz', 2, 'qux'))
```

```python
assert FooSimplePath(**data).bar == "simple"
assert FooLongerPath(**data).bar == "longer"
```

--

```python
from pydantic import AliasChoices

class FooPrecedenceRule(BaseModel):
    bar: str = Field(validation_alias=AliasChoices("al-bar",
                    AliasPath('baz', 2, 'qux')))

assert FooPrecedenceRule(**data).bar == "simple"
data.pop('al-bar')
assert FooPrecedenceRule(**data).bar == "longer"

```

--

Tweet data mapping example

```python
class TweetSimplified(BaseModel):
    id : str = Field(alias='id_str')
    text: str
    user_id : int = Field(validation_alias=AliasPath('user', 'id'))
    url : str = Field(validation_alias=AliasPath("entities", "urls", 0 , "unwound", "url")) # todo: get the url list


with open("tweet.json", "r", encoding="utf-8") as tweet_file:
    tweet = TweetSimplified(**json.load(tweet_file))

pprint(tweet.model_dump())
```


```output


    {'id': '850006245121695744',
     'text': '1/ Today we’re sharing our vision for the future of the Twitter API '
             'platform!\n'
             'https://t.co/XweGngmxlP',
     'url': 'https://cards.twitter.com/cards/18ce53wgo4h/3xo1c',
     'user_id': 2244994945}
```

---

## Recursive models

model with a reference to it self.

<!-- Note: this would segfault in v1 -->

```python
class Energy(BaseModel):
    offset: int = 0
    slots: list[Energy] = Field(default_factory=list) # partial energy from different sources (contributors)
    def from_kwh(kwh: int) -> Self:
        return Energy(offset=kwh * 10e3)
    def simplify(self):
        offset_ = sum([slot.offset for slot in self.slots])
        return Energy(offset=offset_ , slots=[])
```

```python
e = Energy(offset=0)
e.slots.append(e)
```

```python
e.json() # in v1 would segfault
# RecursionError: maximum recursion depth exceeded while calling a Python object
# (note that this is a v1 interface)
```
while in v2
```python
e.model_dump_json() # v2 (as json is deprecated)
```

```output
'{"offset":0,"slots":[{"offset":0,"slots":[{}]}]}'
```

---

## Generics (enhanced)


Example: a stack of data

```python
from typing import Generic, TypeVar

DataT = TypeVar('DataT')

class Stack(BaseModel, Generic[DataT]):
    """ a pile/stack of data"""
    data: list[DataT] = Field(default_factory=list)

    def add(self, item: DataT):
        self.data.append(item)

    def pop(self) -> Optional[DataT]:
        if len(self.data):
            return self.data.pop()

    def __repr__(self):
        return f"Pile({self.data})"



```

--

```python
class EnergyContributions(Stack[Energy]):
    def __repr__(self):
        return f"EnergyContributions({self.data})"
    def simplify(self) -> Self:
        offset_ = 0
        while energy:=self.pop():
            offset_ += energy.offset
        self.add(Energy(offset=offset_))
        return self

EnergyContributions(data = [Energy(offset=i) for i in range(10)]).simplify().model_dump()
```

```output
    {'data': [{'offset': 45, 'slots': []}]}

```

--

### Recursive Generics

```python
DataT = TypeVar('DataT')

class BinaryTree(BaseModel, Generic[DataT]):
    left: Optional[Union[DataT, "BinaryTree[DataT]"]] = None
    right: Optional[Union[DataT, "BinaryTree[DataT]"]] = None
    data: DataT

    def add_most_right(self, item: DataT):
        if self.right is None:
            self.right = item
        else:
            self.right.add_most_right(item)

    def traverse(self):
        """ traverse depth first, (left to right) """
        if self.left:
            yield from self.left.traverse()
        yield self.data
        if self.right:
            yield from self.right.traverse()
```

```python

# let's build a tree
tree :BinaryTree[int] = BinaryTree(left=BinaryTree(data=1),
    data=2, right=BinaryTree(data=3))
tree.add_most_right(BinaryTree(data=4))

assert list(tree.traverse())==list(range(1,5))
```

```python

BinaryTree[int].model_validate_json(tree.model_dump_json())

```

---

## Serialization

in v1 it asks the value, in v2 it asks the type annotation to do the serialization
it solves **"do not ask the type"** problem

```python
class PublicCustomer(BaseModel):
    id: int
    name: str

class PrivateCustomer(PublicCustomer):
    """ with sensible data """
    vat_number: str = Field(validation_alias=AliasPath("vat", "number"))
    email: str = Field(validation_alias=AliasPath("contact", "email"))
    phone: str = Field(validation_alias=AliasPath("contact", "phone"))
```

--

``` python
class PublicAccount(BaseModel):
    account_id: int
    customer: PublicCustomer

class PrivateAccount(BaseModel):
    account_id: int
    customer: PrivateCustomer

```

```python

private_customer = PrivateCustomer.model_validate({"vat": {"number": "123"}, "id":"123", "name": "John", "contact": {"email": "abc@abc.com", "phone": "123456789"}})

# it doesn't serialize the private fields since the model is PublicAccount
# it doesn't ask the value which is private_customer but rather the type of the field which is PublicCustomer
print(PublicAccount(account_id=1, customer=private_customer).model_dump())
```

```output
{'account_id': 1, 'customer': {'id': 123, 'name': 'John'}}
```

---

## Migration

https://docs.pydantic.dev/dev-v2/migration/

code transformation tool -> bump-pydantic (python package)

```bash
pip install bump-pydantic
```

```python
! bump-pydantic --help
```

let's try migrating the tweet models

```python
! bump-pydantic  --log-file tweet_model_migration_log.txt --diff ./tweet_v1.py

```

```python
# let's try migrating a bigger project ...
```
