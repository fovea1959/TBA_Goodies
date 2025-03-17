import argparse
import datetime
import logging
import json
import sys
import typing

import sqlalchemy.orm.exc

from typing import Optional

from sqlalchemy import Text, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.orm.base import Mapped


class Base(DeclarativeBase):
    # https://stackoverflow.com/a/11884806
    def as_dict(self, *args) -> dict:
        rv = {c.name: getattr(self, c.name) for c in self.__table__.columns}

        for name in dir(self.__class__):
            if isinstance(getattr(self.__class__, name), property):
                rv[name] = getattr(self, name)

        return rv

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        # Helper for __repr__
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f'{key}={field!r}')
            except sqlalchemy.orm.exc.DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"

    def __repr__(self) -> str:
        # override this one if necessary
        return self._repr(**self.as_dict())


class TBAData(Base):
    __tablename__ = 'tba'

    url: Mapped[str] = mapped_column(Text, primary_key=True)
    date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    etag: Mapped[str] = mapped_column(Text)
    data_json: Mapped[str] = mapped_column(Text)

    data_cache = None

    @property
    def data(self):
        if self.data_cache is None:
            self.data_cache = json.loads(self.data_json)
        return self.data_cache

def main(argv):
    parser = argparse.ArgumentParser()
    args = parser.parse_args(argv)

    db_filename = 'tba.db'
    logging.info ("Creating database file %s", db_filename)
    Base.metadata.create_all(create_engine(f'sqlite:///{db_filename}', echo=True))
    logging.info("...created")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])