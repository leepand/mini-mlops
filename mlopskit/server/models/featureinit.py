import contextlib
import datetime
from typing import List, Optional, Type, TypeVar, Union

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from structlog import get_logger
from .errors import UnknownMetadataError
from .feature_store import Base

logger = get_logger(__name__)


class FeatureModelInit(object):
    type = "sqlalchemy"

    def __init__(self, db_uri: str):
        self.db_uri = db_uri
        self._engine = create_engine(db_uri)
        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine)
        self._active_session = None

    @contextlib.contextmanager
    def _session(self) -> Session:
        if self._active_session is None:
            logger.debug("Creating session for %s", db_uri=self.db_uri)
            self._active_session = self._Session()
            new_session = True
        else:
            new_session = False

        try:
            yield self._active_session

            if new_session:
                self._active_session.commit()
        except:  # noqa
            if new_session:
                self._active_session.rollback()
            raise
        finally:
            if new_session:
                self._active_session.close()
                self._active_session = None

    def _get_objects(self, object_type, add_filter=None) -> List:
        with self._session() as s:
            if add_filter is None:
                logger.debug("Getting %ss", name=object_type.__name__)
            else:
                logger.debug(
                    "Getting %ss with filter %s",
                    name=object_type.__name__,
                    _filter=add_filter,
                )
            q = s.query(object_type)
            if add_filter is not None:
                q = q.filter(add_filter)
            return [o.to_obj() for o in q.all()]

    def _create_object(self, obj):
        with self._session() as s:
            p = obj
            s.add(p)
            try:
                logger.debug("Inserting object %s", query=p)
                s.commit()
            except IntegrityError:
                raise obj
            return obj

    def _delete_object(self, object_type, _id, ne_error_type, ie_error_type):
        with self._session() as s:
            p = s.query(object_type).filter(object_type.id == _id).first()
            if p is None:
                raise ne_error_type(object_type)
            logger.debug("Deleting object %s", query=p)
            try:
                s.delete(p)
                s.commit()
            except IntegrityError:
                s.rollback()
                if p.to_obj().bind_meta_repo(self).has_children():
                    raise ie_error_type(object_type)
                else:
                    raise UnknownMetadataError
