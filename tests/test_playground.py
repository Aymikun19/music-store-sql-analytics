import pytest

from playground import QueryError, run, validate


def test_select_runs():
    df, secs, truncated = run("select count(*) as n from Customer")
    assert df.loc[0, "n"] == 59 and not truncated


def test_cte_allowed_and_comments_ignored():
    df, *_ = run("-- top genre\nwith g as (select GenreId from Track) select count(*) n from g;")
    assert df.loc[0, "n"] > 0


@pytest.mark.parametrize("sql", ["delete from Customer", "drop table Album", "select 1; delete from Customer", "attach 'x.db' as x", "pragma writable_schema=1", ""])
def test_rejects_non_select(sql):
    with pytest.raises(QueryError):
        run(sql)


def test_cannot_write_through_cte():
    with pytest.raises(QueryError):
        run("with x as (select 1) insert into Genre(Name) select 'Hack'")


def test_validate_strips_trailing_semicolon():
    assert validate("select 1;") == "select 1"
