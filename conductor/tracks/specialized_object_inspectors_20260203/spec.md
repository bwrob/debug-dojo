# Specification: Specialized Object Inspectors

## Overview
Extend the inspection tools (`i()` helper) to recognize and beautifully format specialized third-party objects. Generic inspection often fails to capture the essence of objects like DataFrames, NumPy arrays, or Pydantic models.

## Requirements
- Detect if an object is a Pandas DataFrame/Series and render a summary/head.
- Detect if an object is a NumPy array and render shape/dtype/preview.
- Detect if an object is a Pydantic model and render the schema/fields.
- Fallback gracefully if libraries are not installed.
