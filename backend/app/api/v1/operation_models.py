"""Response bodies for §5, the operation registry and limits (docs/api_contract.md)."""

from pydantic import Field

from app.api.models import ApiModel
from app.core.artifact_type import ArtifactType
from app.core.operations import OperationContract, Port

__all__ = ["ArtifactType", "Limits", "OperationContract", "Port"]


class Limits(ApiModel):
    """Server limits. The frontend reads them from here and never hard-codes them."""

    max_file_size: int = Field(description="Bytes")
    max_files_per_run: int
    max_nodes: int = Field(description="Most nodes in one workflow")
    workspace_quota: int = Field(description="Bytes of storage per workspace")
