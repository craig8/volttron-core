from typing import Optional
from returns.result import Result, Success, Failure
from returns.maybe import Some, Nothing, Maybe, maybe


def test_results_from_value():
    assert str(Result.from_value(1)) == '<Success: 1>'
    assert str(Result.from_value(0)) == '<Success: 0>'
    assert str(Result.from_value(False)) == '<Success: False>'


def test_results_from_optional():
    assert Maybe.from_optional(1) == Some(1)
    assert Maybe.from_optional(None) == Nothing


def test_from_failure():
    assert Result.from_failure(1) == Failure(1)


def test_may_fail_function():

    @maybe
    def may_fail(a_number: int) -> Optional[int]:
        if isinstance(a_number, str):
            return None
        else:
            return a_number

    value: Result[int] = Success(5)
    result: Result[int] = value.bind(may_fail)
    assert result == Some(5)

    value: Result[int] = Success("this")
    result: Result[int] = value.bind(may_fail)
    assert result == Nothing
