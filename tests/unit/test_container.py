import inspect
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable
from unittest import mock

import pytest

import volttron.server.containers as containers_module
from volttron.server.containers import Container, Unresolvable


@runtime_checkable
class Cars(Protocol):

    def get_car_model(self) -> str:
        ...


class Honda:

    def get_car_model(self) -> str:
        return "Honda"


class Ford:

    def __init__(self, subtype: str):
        self._subtype = subtype

    def get_car_type_name(self) -> str:
        return f"{self.__class__.__name__} {self._subtype}"


class Factory:

    def __call__(self, *args: mock.ANY, **kwds: mock.ANY) -> mock.ANY:
        return mock.MagicMock(*args, **kwds)


class FactoryWithKWARGS:

    def __init__(self, car_type: Cars) -> None:
        self.car_type = car_type

    def build_car(self) -> Cars:
        return self.car_type()    # type: ignore


def test_reraises_unresolvable():
    container = Container.create(name="bar")
    with pytest.raises(Unresolvable):
        container.resolve(str)


def test_can_add_instance():
    Container.destroy_all()
    container = Container.create(name="test")
    factory = Factory()
    container.add_instance(type=Factory, value=factory)
    assert container.resolve(type=Factory) is factory
    del Container.containers["test"]


def test_can_add_interface_reference():
    Container.destroy_all()
    container = Container.create(name="foo")
    container.add_interface_reference(Cars, Honda)
    honda = container.resolve(Cars)
    assert isinstance(honda, (Cars, Honda))
    assert not inspect.isclass(honda)
    assert inspect.isclass(Honda)


def test_fail_to_add_the_same_interface_reference():
    Container.destroy_all()
    container = Container.create(name="foo")
    container.add_interface_reference(Cars, Honda)
    # Should fail because there is already a "Cars" registered
    with pytest.raises(AttributeError):
        container.add_interface_reference(Cars, Ford)


def test_can_get_container():
    Container.destroy_all()
    container = Container.create(name="test")
    container2 = Container.create(name="test2")
    assert container is not container2
    assert Container.get_container(name="test") == container
    assert Container.get_container(name="test") != Container.get_container(name="test2")
    assert Container.get_container(name="test2") != container
    del Container.containers["test"]
    del Container.containers["test2"]


def test_can_add_more_than_one_type_of_car():
    Container.destroy_all()
    container = Container.create("cars")
    container.add_concrete_reference(Cars, Honda)
    container.add_concrete_reference(Cars, Ford, subtype="Caravan")
    honda = container.resolve(Honda)
    ford = container.resolve(Ford)
    assert isinstance(ford, (Ford, Cars))
    assert isinstance(honda, (Honda, Cars))
    assert ford is not honda
    assert not isinstance(ford, Honda)
    assert not isinstance(honda, Ford)


def test_cannot_add_multiple_hondas():
    Container.destroy_all()
    container = Container.create("cars")
    container.add_concrete_reference(Cars, Honda)
    with pytest.raises(ValueError):
        container.add_concrete_reference(Cars, Honda)


def test_can_resolve_optional_with_multiple_type_hints():
    Container.destroy_all()

    class Data:

        def __init__(self, path: Optional[str | Path] = None) -> None:
            self.path = path

    class Data2(Data):

        def __init__(self, path: Optional[str | Path] = None) -> None:
            super().__init__(path=path)

    container = Container.create("data")
    # No Arg Optional
    container.add_concrete_reference(Data, Data2)
    assert isinstance(container.resolve(Data2), Data2)
    assert not inspect.isclass(container.resolve(Data2))

    container.add_concrete_reference(Data2, Data2, path="woot-there-it-is")
    assert isinstance(container.resolve(Data2), Data)
    assert isinstance(container.resolve(Data2), Data2)
    assert not inspect.isclass(container.resolve(Data2))
