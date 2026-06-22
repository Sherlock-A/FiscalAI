# Import all ORM models here so SQLAlchemy's MetaData always has the full
# table graph when resolving foreign keys. Without this, FK references to
# tables whose model hasn't been imported yet raise NoReferencedTableError
# during the first flush() that touches a related model.
from app.models.commune import Commune  # noqa: F401
from app.models.building import Building  # noqa: F401
from app.models.utility_connection import UtilityConnection  # noqa: F401
from app.models.gap_detection import GapDetection  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
