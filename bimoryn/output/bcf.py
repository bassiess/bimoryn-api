"""BCF 2.1 export formatter.

Produces a .bcfzip file from a ValidationResult.

BCF (BIM Collaboration Format) is the industry standard for issue tracking —
every major BIM tool (Revit, ArchiCAD, Navisworks, Solibri, BIMcollab) can
import it. This implementation targets BCF 2.1 (ISO 19650-compatible).

BCF zip structure:
  bcf.version          — version declaration
  project.bcfp         — project info
  {topic-guid}/
      markup.bcf       — the issue (topic) + comments
      viewpoint.bcfv   — camera/component viewpoint (optional)
"""

from __future__ import annotations

import io
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from xml.etree.ElementTree import Element, SubElement, indent, tostring

from bimoryn.models import Issue, Severity, ValidationResult

if TYPE_CHECKING:
    pass

# BCF priority mapping
_SEVERITY_PRIORITY = {
    Severity.ERROR:   "Critical",
    Severity.WARNING: "Major",
    Severity.INFO:    "Minor",
}

_SEVERITY_TYPE = {
    Severity.ERROR:   "Error",
    Severity.WARNING: "Warning",
    Severity.INFO:    "Info",
}

BCF_AUTHOR = "bimoryn@validation"


def write_bcf(result: ValidationResult, output_path: str | Path) -> Path:
    """Write a BCF 2.1 zip from a ValidationResult."""
    out = Path(output_path)
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("bcf.version", _version_xml())
        zf.writestr("project.bcfp", _project_xml(result))

        for issue in result.issues:
            topic_id = str(uuid.uuid4())
            zf.writestr(f"{topic_id}/markup.bcf", _markup_xml(issue, topic_id, result))
            if issue.location and any(
                v is not None for v in [issue.location.x, issue.location.y, issue.location.z]
            ):
                zf.writestr(f"{topic_id}/viewpoint.bcfv", _viewpoint_xml(issue))

    out.write_bytes(buf.getvalue())
    return out


# ---------------------------------------------------------------------------
# XML builders
# ---------------------------------------------------------------------------

def _version_xml() -> str:
    root = Element("Version", VersionId="2.1", xsi_noNamespaceSchemaLocation="version.xsd")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    SubElement(root, "DetailedVersion").text = "2.1"
    return _serialise(root)


def _project_xml(result: ValidationResult) -> str:
    root = Element("ProjectExtension")
    proj = SubElement(root, "Project", ProjectId=result.run_id)
    SubElement(proj, "Name").text = result.project_name or Path(result.model_path).stem
    SubElement(root, "ExtensionSchema").text = ""
    return _serialise(root)


def _markup_xml(issue: Issue, topic_id: str, result: ValidationResult) -> str:
    root = Element("Markup")

    # --- Header ---
    header = SubElement(root, "Header")
    file_el = SubElement(header, "File", isExternal="false")
    SubElement(file_el, "Filename").text = Path(result.model_path).name
    SubElement(file_el, "Date").text = _isoformat(result.started_at)

    # --- Topic ---
    topic = SubElement(
        root,
        "Topic",
        Guid=topic_id,
        TopicType=_SEVERITY_TYPE.get(issue.severity, "Issue"),
        TopicStatus="Open",
    )
    SubElement(topic, "Title").text = f"[{issue.rule_id}] {issue.message}"
    SubElement(topic, "Priority").text = _SEVERITY_PRIORITY.get(issue.severity, "Normal")
    SubElement(topic, "Index").text = "0"
    SubElement(topic, "CreationDate").text = _isoformat(result.started_at)
    SubElement(topic, "CreationAuthor").text = BCF_AUTHOR
    SubElement(topic, "ModifiedDate").text = _isoformat(result.started_at)
    SubElement(topic, "ModifiedAuthor").text = BCF_AUTHOR
    SubElement(topic, "Description").text = _build_description(issue)
    SubElement(topic, "Labels").text = issue.category.value

    if issue.location:
        SubElement(topic, "ReferenceLinks")
        vp = SubElement(topic, "Viewpoints", Guid=str(uuid.uuid4()))
        SubElement(vp, "Viewpoint").text = "viewpoint.bcfv"

    # --- Comment ---
    comment_el = SubElement(root, "Comment", Guid=str(uuid.uuid4()))
    SubElement(comment_el, "Date").text = _isoformat(result.started_at)
    SubElement(comment_el, "Author").text = BCF_AUTHOR
    SubElement(comment_el, "Comment").text = issue.detail or issue.message
    SubElement(comment_el, "Status").text = "Active"

    # Component reference (GUID of the offending element)
    if issue.element_guid:
        vp_ref = SubElement(comment_el, "Viewpoint", Guid=str(uuid.uuid4()))
        _ = vp_ref  # marks comment as linked to a viewpoint

    return _serialise(root)


def _viewpoint_xml(issue: Issue) -> str:
    """Minimal perspective camera pointing at the issue location."""
    root = Element("VisualizationInfo", Guid=str(uuid.uuid4()))

    if issue.element_guid:
        components = SubElement(root, "Components")
        sel = SubElement(components, "Selection")
        comp = SubElement(sel, "Component", IfcGuid=issue.element_guid)
        SubElement(comp, "OriginatingSystem").text = "BIMoryn"
        SubElement(comp, "AuthoringToolId").text = issue.element_guid

    if issue.location and issue.location.x is not None:
        x, y, z = issue.location.x, issue.location.y, issue.location.z
        camera = SubElement(root, "PerspectiveCamera")
        cam_pt = SubElement(camera, "CameraViewPoint")
        SubElement(cam_pt, "X").text = str(round(x + 10, 3))
        SubElement(cam_pt, "Y").text = str(round(y + 10, 3))
        SubElement(cam_pt, "Z").text = str(round((z or 0) + 10, 3))
        cam_dir = SubElement(camera, "CameraDirection")
        SubElement(cam_dir, "X").text = "-0.577"
        SubElement(cam_dir, "Y").text = "-0.577"
        SubElement(cam_dir, "Z").text = "-0.577"
        cam_up = SubElement(camera, "CameraUpVector")
        SubElement(cam_up, "X").text = "0"
        SubElement(cam_up, "Y").text = "0"
        SubElement(cam_up, "Z").text = "1"
        SubElement(camera, "FieldOfView").text = "60"

    return _serialise(root)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_description(issue: Issue) -> str:
    parts = [issue.message]
    if issue.element_type:
        parts.append(f"Type: {issue.element_type}")
    if issue.element_name:
        parts.append(f"Name: {issue.element_name}")
    if issue.element_guid:
        parts.append(f"GUID: {issue.element_guid}")
    if issue.detail:
        parts.append(issue.detail)
    return "\n".join(parts)


def _isoformat(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _serialise(element: Element) -> str:
    indent(element, space="  ")
    return '<?xml version="1.0" encoding="utf-8"?>\n' + tostring(element, encoding="unicode")
