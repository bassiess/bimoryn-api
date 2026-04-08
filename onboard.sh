#!/usr/bin/env bash
# BIMoryn Pilot Onboarding
# Installs dependencies and validates the demo model.
# Requirements: Python 3.11+

set -e

echo ""
echo "============================================"
echo "  BIMoryn — BIM Validation Engine"
echo "  Pilot Onboarding"
echo "============================================"
echo ""

# Check Python version
PYTHON=$(command -v python3 || command -v python || true)

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python not found."
    echo "Please install Python 3.11 or later from https://www.python.org/downloads/"
    exit 1
fi

PYVER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYMAJ=$($PYTHON -c "import sys; print(sys.version_info.major)")
PYMIN=$($PYTHON -c "import sys; print(sys.version_info.minor)")

if [ "$PYMAJ" -lt 3 ] || ([ "$PYMAJ" -eq 3 ] && [ "$PYMIN" -lt 11 ]); then
    echo "ERROR: Python 3.11 or later is required (found $PYVER)."
    exit 1
fi

echo "Python $PYVER found."
echo ""

# Install BIMoryn
echo "Installing BIMoryn..."
$PYTHON -m pip install -e . --quiet
echo "Done."
echo ""

# Run demo validation
echo "Running validation on samples/demo.ifc..."
echo "--------------------------------------------"
bimoryn validate samples/demo.ifc
echo "--------------------------------------------"
echo ""

# Offer to save JSON report
echo "Saving JSON report to demo-report.json..."
bimoryn validate samples/demo.ifc --output demo-report.json --quiet
echo "Report saved: demo-report.json"
echo ""
echo "============================================"
echo "  Setup complete!"
echo ""
echo "  To validate your own model:"
echo "    bimoryn validate path/to/your-model.ifc"
echo ""
echo "  To save a BCF file for Revit / Solibri:"
echo "    bimoryn validate model.ifc --output issues.bcfzip --format bcf"
echo ""
echo "  To list all rules:"
echo "    bimoryn rules list"
echo "============================================"
echo ""
